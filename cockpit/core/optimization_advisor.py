"""Optimization advisor: detecta patrones de gasto subóptimo en ai_usage.jsonl.

Reglas heurísticas, sin IA. Cada regla produce 0..n recomendaciones con:
  severity, savings_estimate_usd, evidence, action.

Inspiración: skill token-optimizer (T01..T10) adaptada a este sistema.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from . import usage_tracker


@dataclass
class Recommendation:
    rule_id: str
    severity: str  # critical | warning | info
    title: str
    evidence: str
    action: str
    savings_estimate_usd: float = 0.0


# Sustituciones por defecto modelo-caro → modelo-barato equivalente.
CHEAPER_EQUIVALENT: dict[str, str] = {
    "claude-opus-4-7": "claude-sonnet-4-6",
    "claude-sonnet-4-6": "claude-haiku-4-5",
    "claude-sonnet-4-5": "claude-haiku-4-5",
    "gpt-4o": "gpt-4o-mini",
    "gpt-4.1": "gpt-4.1-mini",
}


def analyze(events: Iterable[dict[str, Any]]) -> list[Recommendation]:
    """Aplica todas las reglas a la lista de eventos y devuelve recomendaciones."""
    events = list(events)
    if not events:
        return []

    recs: list[Recommendation] = []
    recs.extend(_rule_expensive_model_for_cheap_work(events))
    recs.extend(_rule_high_concentration_per_source(events))
    recs.extend(_rule_failed_calls(events))
    recs.extend(_rule_high_output_ratio(events))
    recs.extend(_rule_unused_caching_opportunity(events))
    recs.sort(key=lambda r: (-r.savings_estimate_usd, r.severity))
    return recs


def _rule_expensive_model_for_cheap_work(events: list[dict]) -> list[Recommendation]:
    """T01: modelo caro usado en tareas con poco output → bajar de gama."""
    out: list[Recommendation] = []
    by_model: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        by_model[ev.get("model", "?")].append(ev)

    for model, calls in by_model.items():
        if model not in CHEAPER_EQUIVALENT:
            continue
        small = [c for c in calls if int(c.get("output_tokens", 0)) < 300]
        if len(small) < 3:
            continue
        spent = sum(float(c.get("cost_usd", 0)) for c in small)
        cheaper = CHEAPER_EQUIVALENT[model]
        # Aproximación: precio del modelo barato escalando linealmente sobre input/output.
        savings_factor = _savings_factor(model, cheaper)
        savings = round(spent * savings_factor, 4)
        out.append(
            Recommendation(
                rule_id="T01",
                severity="warning",
                title=f"{model} usado para {len(small)} tareas con <300 tokens output",
                evidence=(
                    f"{len(small)} llamadas con output pequeño consumiendo ${spent:.4f}. "
                    f"Sources más afectados: "
                    + ", ".join(_top_sources(small, 3))
                ),
                action=(
                    f"Cambia a {cheaper} en estas sources. "
                    f"Ahorro estimado: ${savings:.4f} sobre el histórico."
                ),
                savings_estimate_usd=savings,
            )
        )
    return out


def _rule_high_concentration_per_source(events: list[dict]) -> list[Recommendation]:
    """Una source acumula >40% del coste total → punto caliente."""
    out: list[Recommendation] = []
    total = sum(float(e.get("cost_usd", 0)) for e in events)
    if total <= 0:
        return out
    by_source: dict[str, float] = defaultdict(float)
    for ev in events:
        by_source[ev.get("source", "?")] += float(ev.get("cost_usd", 0))
    for src, cost in by_source.items():
        ratio = cost / total
        if ratio > 0.4:
            out.append(
                Recommendation(
                    rule_id="HOT-SOURCE",
                    severity="warning",
                    title=f"Source «{src}» concentra el {ratio:.0%} del gasto",
                    evidence=f"${cost:.4f} de ${total:.4f} total.",
                    action=(
                        "Revisa el prompt y el contexto que se envía desde esa source. "
                        "Suele ser el primer sitio donde optimizar."
                    ),
                    savings_estimate_usd=round(cost * 0.3, 4),
                )
            )
    return out


def _rule_failed_calls(events: list[dict]) -> list[Recommendation]:
    """Llamadas con ok=False → coste de errores, posible problema de prompts/keys."""
    fails = [e for e in events if e.get("ok") is False]
    if not fails:
        return []
    by_err: dict[str, int] = defaultdict(int)
    for f in fails:
        by_err[f.get("error", "?")] += 1
    top = sorted(by_err.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return [
        Recommendation(
            rule_id="FAILS",
            severity="critical" if len(fails) >= 5 else "warning",
            title=f"{len(fails)} llamadas fallidas registradas",
            evidence="Errores top: " + " · ".join(f"{e} (×{n})" for e, n in top),
            action=(
                "Revisa keys y rate limits. Los fallos no facturan output pero sí "
                "input y latencia. Considera bajar `max_retries` si son sistemáticos."
            ),
        )
    ]


def _rule_high_output_ratio(events: list[dict]) -> list[Recommendation]:
    """Output/input > 3 → prompts demasiado abiertos, pedir longitud acotada."""
    out: list[Recommendation] = []
    candidates = [
        e for e in events
        if int(e.get("input_tokens", 0)) > 0
        and int(e.get("output_tokens", 0)) / max(int(e.get("input_tokens", 0)), 1) > 3
    ]
    if len(candidates) < 5:
        return out
    extra_cost = sum(float(e.get("cost_usd", 0)) for e in candidates)
    return [
        Recommendation(
            rule_id="VERBOSE",
            severity="info",
            title=f"{len(candidates)} llamadas con ratio output/input > 3",
            evidence=(
                "Sources más verbosas: " + ", ".join(_top_sources(candidates, 3))
                + f". Coste acumulado de estas llamadas: ${extra_cost:.4f}."
            ),
            action=(
                "Añade «máximo N palabras» o «formato JSON estructurado» al prompt. "
                "Ahorro típico: 30-50% del output."
            ),
            savings_estimate_usd=round(extra_cost * 0.35, 4),
        )
    ]


def _rule_unused_caching_opportunity(events: list[dict]) -> list[Recommendation]:
    """Mismo system prompt repetido en muchas llamadas → activar prompt caching.

    Aprox: muchas llamadas desde misma source con input_tokens similar (±20%)
    sugieren contexto repetido cacheable.
    """
    out: list[Recommendation] = []
    by_source: dict[str, list[int]] = defaultdict(list)
    for ev in events:
        by_source[ev.get("source", "?")].append(int(ev.get("input_tokens", 0)))
    for src, inputs in by_source.items():
        if len(inputs) < 5:
            continue
        avg = sum(inputs) / len(inputs)
        if avg < 1000:
            continue
        deviations = sum(1 for i in inputs if abs(i - avg) / max(avg, 1) < 0.2)
        if deviations / len(inputs) > 0.7:
            out.append(
                Recommendation(
                    rule_id="CACHE",
                    severity="info",
                    title=f"Source «{src}»: contexto repetido ({len(inputs)} llamadas)",
                    evidence=f"Input promedio {avg:.0f} tokens, 70%+ dentro de ±20% de la media.",
                    action=(
                        "Candidato a Anthropic prompt caching. Marca el system prompt "
                        "como cacheable con cache_control: ahorro 50-90% sobre tokens "
                        "cacheados a partir de la 2ª llamada en 5 min."
                    ),
                    savings_estimate_usd=0.0,  # difícil estimar sin pricing exacto.
                )
            )
    return out


def _top_sources(calls: list[dict], n: int) -> list[str]:
    by_source: dict[str, int] = defaultdict(int)
    for c in calls:
        by_source[c.get("source", "?")] += 1
    return [k for k, _ in sorted(by_source.items(), key=lambda kv: kv[1], reverse=True)[:n]]


def _savings_factor(expensive: str, cheap: str) -> float:
    """Fracción del coste que se ahorraría usando el modelo barato."""
    pe = usage_tracker.PRICING.get(expensive)
    pc = usage_tracker.PRICING.get(cheap)
    if not pe or not pc:
        return 0.5
    # Estimación grosera con peso medio input/output 50/50.
    expensive_avg = (pe[0] + pe[1]) / 2
    cheap_avg = (pc[0] + pc[1]) / 2
    return max(0.0, 1.0 - cheap_avg / expensive_avg)

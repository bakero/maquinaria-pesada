"""Tracker de uso de IA: append a `logs/ai_usage.jsonl` + agregados.

Cada llamada a un modelo se registra como una línea JSON con:
  timestamp, kind (generation|improvement|update|api_check),
  provider, model, source (página/pipeline que la disparó),
  input_tokens, output_tokens, cost_usd, latency_ms, ok.

No persiste secrets ni prompts: solo metadatos.
"""
from __future__ import annotations

import json
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import paths

# Precios USD/M tokens (mayo 2026). Actualizar cuando cambien.
PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-4-7": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "gpt-4.1": (3.0, 12.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
}


@dataclass
class UsageEvent:
    timestamp: str
    kind: str  # generation | improvement | update | api_check
    provider: str
    model: str
    source: str  # página o pipeline que la dispara
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    ok: bool = True
    error: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    p_in, p_out = PRICING.get(model, (0.0, 0.0))
    return round((input_tokens * p_in + output_tokens * p_out) / 1_000_000, 6)


def record(event: UsageEvent, log_path: Path | None = None) -> None:
    log_path = log_path or paths.ai_usage_log()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


def iter_events(log_path: Path | None = None) -> Iterable[dict[str, Any]]:
    log_path = log_path or paths.ai_usage_log()
    if not log_path.exists():
        return
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def aggregate(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Totales globales + por modelo + por kind + por source."""
    total_in = total_out = total_cost = total_calls = 0
    by_model: dict[str, dict[str, float]] = {}
    by_kind: dict[str, dict[str, float]] = {}
    by_source: dict[str, dict[str, float]] = {}

    for ev in events:
        total_calls += 1
        ti = int(ev.get("input_tokens", 0))
        to = int(ev.get("output_tokens", 0))
        cost = float(ev.get("cost_usd", 0.0))
        total_in += ti
        total_out += to
        total_cost += cost

        for bucket, key in (
            (by_model, ev.get("model", "?")),
            (by_kind, ev.get("kind", "?")),
            (by_source, ev.get("source", "?")),
        ):
            slot = bucket.setdefault(key, {"calls": 0, "in": 0, "out": 0, "cost": 0.0})
            slot["calls"] += 1
            slot["in"] += ti
            slot["out"] += to
            slot["cost"] += cost

    return {
        "total_calls": total_calls,
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_cost_usd": round(total_cost, 4),
        "by_model": by_model,
        "by_kind": by_kind,
        "by_source": by_source,
    }


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


# ---------------------------------------------------------------------------
# Helpers para instrumentar pipelines top-level (generar_guion.py, etc.).
#
# Uso típico:
#
#   from cockpit.core.usage_tracker import track_anthropic, track_openai
#   t0 = time.monotonic()
#   resp = client.messages.create(...)
#   track_anthropic(resp, model=model, source="generar_guion.py", kind="generation",
#                   latency_ms=int((time.monotonic()-t0)*1000))
#
# Los helpers SON DEFENSIVOS: si algo falla extrayendo tokens o escribiendo el
# log, se silencia (la generación real no debe romperse por telemetría).
# ---------------------------------------------------------------------------


def track_anthropic(
    response: Any,
    *,
    model: str,
    source: str,
    kind: str = "generation",
    latency_ms: int = 0,
    ok: bool = True,
    error: str = "",
) -> None:
    """Registra una respuesta del SDK Anthropic en `ai_usage.jsonl`.

    Acepta tanto la respuesta de `client.messages.create(...)` como el objeto
    devuelto por `stream.get_final_message()`.
    """
    try:
        usage = getattr(response, "usage", None)
        in_tok = int(getattr(usage, "input_tokens", 0) or 0)
        out_tok = int(getattr(usage, "output_tokens", 0) or 0)
        record(UsageEvent(
            timestamp=now_iso(),
            kind=kind,
            provider="anthropic",
            model=model,
            source=source,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=estimate_cost_usd(model, in_tok, out_tok),
            latency_ms=latency_ms,
            ok=ok,
            error=error,
        ))
    except Exception:
        # Telemetría no debe romper la generación.
        pass


def track_openai(
    response: Any,
    *,
    model: str,
    source: str,
    kind: str = "generation",
    latency_ms: int = 0,
    ok: bool = True,
    error: str = "",
) -> None:
    """Registra una respuesta del SDK OpenAI (`chat.completions.create`)."""
    try:
        usage = getattr(response, "usage", None)
        in_tok = int(getattr(usage, "prompt_tokens", 0) or 0)
        out_tok = int(getattr(usage, "completion_tokens", 0) or 0)
        record(UsageEvent(
            timestamp=now_iso(),
            kind=kind,
            provider="openai",
            model=model,
            source=source,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=estimate_cost_usd(model, in_tok, out_tok),
            latency_ms=latency_ms,
            ok=ok,
            error=error,
        ))
    except Exception:
        pass

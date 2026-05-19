"""Cliente envolvente de Anthropic con tracking de coste y retry estructurado.

Pensado para ser mockeable en tests (todas las llamadas pasan por `generate()`,
que en tests se reemplaza con un fake que devuelve texto predefinido).

Tracking: cada llamada se loguea en `costes_generacion.log` (CSV append) con
modelo, tokens, métricas de caching y coste estimado.
"""
from __future__ import annotations

import csv
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

try:  # carga .env de la raíz del repo si está disponible (override=True para
    # asegurar que las claves del fichero ganan a las del shell)
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:  # pragma: no cover
    pass

logger = logging.getLogger(__name__)

# Precios por millón de tokens (orientativos a 2026-05).
_PRICES_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.8, 4.0),
    "claude-haiku-4-5": (0.8, 4.0),
}

# Mínimos de tokens para que `cache_control` sea aceptado por la API.
# Anthropic exige bloques largos para amortizar la escritura del cache.
_CACHE_MIN_TOKENS_SONNET = 1024
_CACHE_MIN_TOKENS_HAIKU = 4096
# Heurística conservadora chars→tokens para castellano.
_CHARS_PER_TOKEN_ES = 3.5


@dataclass
class CacheableBlock:
    """Bloque de texto cacheable vía `cache_control: {type: ephemeral, ttl: ...}`.

    `ttl` debe ser "5m" (cache estándar) o "1h" (cache extendido). El TTL más
    largo ayuda cuando el contenido es estable entre múltiples episodios
    (ej.: system prompt + master PDF).
    """

    text: str
    ttl: Literal["5m", "1h"] = "5m"

    def to_anthropic_block(self) -> dict:
        return {
            "type": "text",
            "text": self.text,
            "cache_control": {"type": "ephemeral", "ttl": self.ttl},
        }


def _meets_cache_threshold(text: str, model: str) -> bool:
    """Chequea si un bloque supera el mínimo para activar caching en el modelo."""
    estimated_tokens = len(text) / _CHARS_PER_TOKEN_ES
    if "haiku" in model.lower():
        return estimated_tokens >= _CACHE_MIN_TOKENS_HAIKU
    return estimated_tokens >= _CACHE_MIN_TOKENS_SONNET


def _build_system_param(
    system: str | list[CacheableBlock],
    model: str,
) -> str | list[dict]:
    """Construye el parámetro `system` para la API.

    - Si es `str`: comportamiento legacy (sin caching).
    - Si es `list[CacheableBlock]`: bloques con `cache_control` cuando superan
      el mínimo, sin él cuando no llegan (loggea warning para auditar).
    """
    if isinstance(system, str):
        return system
    if not system:
        return ""
    blocks: list[dict] = []
    cache_eligible = 0
    for block in system:
        if _meets_cache_threshold(block.text, model) and cache_eligible < 4:
            # API limita a 4 bloques con cache_control por request.
            blocks.append(block.to_anthropic_block())
            cache_eligible += 1
        else:
            if not _meets_cache_threshold(block.text, model):
                logger.warning(
                    "Bloque de %d chars no supera mínimo cache para %s; "
                    "se envía sin cache_control",
                    len(block.text), model,
                )
            blocks.append({"type": "text", "text": block.text})
    return blocks


@dataclass
class GenerationResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    error: str | None = None
    raw_response: object | None = field(default=None, repr=False)
    # Métricas de prompt caching (0 cuando no se usó).
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_creation_5m_tokens: int = 0
    cache_creation_1h_tokens: int = 0
    latency_ms: int = 0
    stop_reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text)

    @property
    def cache_hit_rate(self) -> float:
        total = self.input_tokens + self.cache_read_input_tokens
        if total <= 0:
            return 0.0
        return self.cache_read_input_tokens / total


def _estimate_cost(model: str, input_tokens: int, output_tokens: int,
                   cache_read: int = 0, cache_create_5m: int = 0,
                   cache_create_1h: int = 0) -> float:
    """Coste en USD considerando descuentos/sobrecostes de caching.

    Anthropic factura cache reads a 0.1× input price y cache writes a 1.25×
    (5m) o 2× (1h) input price. Si no se pasan cache fields, se aplica solo
    input × precio normal.
    """
    inp, out = _PRICES_USD_PER_MTOK.get(model, (3.0, 15.0))
    cost = (
        input_tokens * inp
        + output_tokens * out
        + cache_read * inp * 0.1
        + cache_create_5m * inp * 1.25
        + cache_create_1h * inp * 2.0
    ) / 1_000_000
    return round(cost, 6)


_CSV_HEADER_V2 = [
    "timestamp", "kind", "episode_id", "model", "attempt",
    "input_tokens", "output_tokens",
    "cache_read", "cache_create_5m", "cache_create_1h",
    "cost_usd", "latency_ms",
    "validation_result", "hard_failed", "soft_failed",
]


def _log_cost(repo_root: Path, kind: str, episode_id: str,
              result: GenerationResult, validation_result: str,
              attempt: int = 0,
              hard_failed: int = 0,
              soft_failed: int = 0) -> None:
    """Append a `costes_generacion.log` (CSV) con métricas extendidas.

    Si existe un CSV antiguo (sin columnas de cache), lo renombra a
    `costes_generacion_v1.log` y abre uno nuevo con header v2.
    """
    log_path = repo_root / "costes_generacion.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Detectar formato legacy y migrar si procede.
    if log_path.exists():
        try:
            with log_path.open(encoding="utf-8", newline="") as fh:
                first_row = next(csv.reader(fh), None)
        except (StopIteration, OSError):
            first_row = None
        if first_row and "cache_read" not in first_row:
            legacy = repo_root / "costes_generacion_v1.log"
            try:
                log_path.rename(legacy)
            except OSError:
                pass

    new_file = not log_path.exists()
    with log_path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(_CSV_HEADER_V2)
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            kind, episode_id, result.model, attempt,
            result.input_tokens, result.output_tokens,
            result.cache_read_input_tokens,
            result.cache_creation_5m_tokens,
            result.cache_creation_1h_tokens,
            result.cost_usd, result.latency_ms,
            validation_result, hard_failed, soft_failed,
        ])


def generate(*, system: str | list[CacheableBlock], user: str, model: str,
             max_output_tokens: int = 8000,
             temperature: float = 0.7,
             stream: bool = True,
             api_key: str | None = None) -> GenerationResult:
    """Llama a la API de Anthropic y devuelve un `GenerationResult`.

    `system` acepta str (legacy, sin caching) o list[CacheableBlock] (con
    `cache_control` automático sobre los bloques que superan el mínimo).
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return GenerationResult(
            text="", model=model, input_tokens=0, output_tokens=0,
            cost_usd=0.0, error="ANTHROPIC_API_KEY no definida",
        )
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover
        return GenerationResult(
            text="", model=model, input_tokens=0, output_tokens=0,
            cost_usd=0.0, error=f"anthropic no disponible: {exc}",
        )

    started = time.perf_counter()
    system_param = _build_system_param(system, model)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        kwargs = dict(
            model=model,
            max_tokens=max_output_tokens,
            temperature=temperature,
            system=system_param,
            messages=[{"role": "user", "content": user}],
        )
        if stream:
            text_parts: list[str] = []
            usage_obj = None
            stop_reason = None
            with client.messages.stream(**kwargs) as stream_resp:
                for delta in stream_resp.text_stream:
                    text_parts.append(delta)
                final = stream_resp.get_final_message()
                usage_obj = final.usage
                stop_reason = getattr(final, "stop_reason", None)
            text = "".join(text_parts)
        else:
            resp = client.messages.create(**kwargs)
            text = "".join(getattr(b, "text", "") for b in resp.content)
            usage_obj = resp.usage
            stop_reason = getattr(resp, "stop_reason", None)

        input_tokens = getattr(usage_obj, "input_tokens", 0) or 0
        output_tokens = getattr(usage_obj, "output_tokens", 0) or 0
        cache_read = getattr(usage_obj, "cache_read_input_tokens", 0) or 0
        cache_create = getattr(usage_obj, "cache_creation_input_tokens", 0) or 0
        cache_5m = 0
        cache_1h = 0
        cache_creation = getattr(usage_obj, "cache_creation", None)
        if cache_creation is not None:
            cache_5m = getattr(cache_creation, "ephemeral_5m_input_tokens", 0) or 0
            cache_1h = getattr(cache_creation, "ephemeral_1h_input_tokens", 0) or 0

        cost = _estimate_cost(
            model, input_tokens, output_tokens,
            cache_read=cache_read,
            cache_create_5m=cache_5m,
            cache_create_1h=cache_1h,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        return GenerationResult(
            text=text, model=model,
            input_tokens=input_tokens, output_tokens=output_tokens,
            cost_usd=cost,
            cache_read_input_tokens=cache_read,
            cache_creation_input_tokens=cache_create,
            cache_creation_5m_tokens=cache_5m,
            cache_creation_1h_tokens=cache_1h,
            latency_ms=latency_ms,
            stop_reason=stop_reason,
        )
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((time.perf_counter() - started) * 1000)
        return GenerationResult(
            text="", model=model, input_tokens=0, output_tokens=0,
            cost_usd=0.0, error=f"{type(exc).__name__}: {exc}",
            latency_ms=latency_ms,
        )


def generate_with_retry(*, system: str | list[CacheableBlock],
                         user: str, model: str,
                         retry_feedback: str | None = None,
                         **kwargs) -> tuple[GenerationResult, GenerationResult | None]:
    """Genera y, si `retry_feedback` se proporciona tras un hard-fail, hace UN
    reintento con feedback explícito. Devuelve `(primer_intento, segundo|None)`.

    El segundo intento añade el feedback al final del prompt user, manteniendo
    el system idéntico (más cache-friendly).
    """
    first = generate(system=system, user=user, model=model, **kwargs)
    if retry_feedback is None:
        return first, None
    retry_user = (
        f"{user}\n\n---\nFEEDBACK DE LA GENERACIÓN ANTERIOR (no se aceptó):\n"
        f"{retry_feedback}\n\n"
        "Genera de nuevo respetando exactamente las reglas del system prompt."
    )
    second = generate(system=system, user=retry_user, model=model, **kwargs)
    return first, second


def track_cost(repo_root: Path, kind: str, episode_id: str,
               result: GenerationResult,
               validation_result: str = "n/a",
               attempt: int = 0,
               hard_failed: int = 0,
               soft_failed: int = 0) -> None:
    """Atajo para loguear la generación en costes_generacion.log (formato v2)."""
    _log_cost(repo_root, kind, episode_id, result, validation_result,
              attempt=attempt, hard_failed=hard_failed, soft_failed=soft_failed)

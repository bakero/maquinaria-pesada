"""Cliente Anthropic común: retry + backoff + tracking de uso + streaming.

Resuelve los gaps detectados en la auditoría (área 11):
- Sin retry en llamadas Claude → reintentos exponenciales en 429/503.
- Sin trazabilidad de qué modelo+tokens se usó → cada call se registra en
  ai_usage.jsonl con kind/source explícitos.
- Sin manejo común de errores → un único punto que normaliza fallos.
- Sin verbose para el usuario → `improve_with_claude_stream` cede el texto
  parcialmente para mostrar progreso en vivo en Streamlit.

API:
    text, usage = improve_with_claude(system=..., user=..., source=...)

    # Modo verbose con streaming:
    for kind, payload in improve_with_claude_stream(system=..., user=..., source=...):
        if kind == "text":   # chunk de texto
            ...
        elif kind == "usage":  # CallUsage final
            ...
"""
from __future__ import annotations

import os
import time
from collections.abc import Iterator
from dataclasses import dataclass

from . import paths, usage_tracker

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_MAX_RETRIES = 3
RETRY_BACKOFF_S = (1, 2, 4, 8)


@dataclass
class CallUsage:
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    ok: bool
    error: str = ""


class AIClientError(RuntimeError):
    pass


def _load_anthropic_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    env_path = paths.env_file()
    if env_path.exists():
        try:
            from dotenv import dotenv_values

            values = dotenv_values(env_path)
            return values.get("ANTHROPIC_API_KEY", "") or ""
        except ImportError:
            return ""
    return ""


def improve_with_claude(
    *,
    system: str,
    user: str,
    source: str,
    kind: str = "improvement",
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> tuple[str, CallUsage]:
    """Llama a Claude (bloqueante) y devuelve (texto, CallUsage).

    Internamente reusa el stream y concatena. La función bloquea hasta el final.
    """
    chunks: list[str] = []
    usage: CallUsage | None = None
    for tag, payload in improve_with_claude_stream(
        system=system,
        user=user,
        source=source,
        kind=kind,
        model=model,
        max_tokens=max_tokens,
        max_retries=max_retries,
    ):
        if tag == "text":
            chunks.append(payload)
        elif tag == "usage":
            usage = payload
    assert usage is not None
    return "".join(chunks), usage


def improve_with_claude_stream(
    *,
    system: str,
    user: str,
    source: str,
    kind: str = "improvement",
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Iterator[tuple[str, object]]:
    """Llama a Claude en streaming y cede tuplas (tag, payload).

    Tags:
      - "text"  → payload es str con el delta nuevo.
      - "usage" → payload es CallUsage final (input/output tokens, coste, etc.)

    En caso de error, registra el evento como fallido y lanza AIClientError.
    Aplica retry exponencial en errores retryables.
    """
    try:
        import anthropic
    except ImportError as e:
        raise AIClientError("anthropic SDK no instalado") from e

    api_key = _load_anthropic_key()
    if not api_key:
        raise AIClientError("ANTHROPIC_API_KEY no configurada")

    client = anthropic.Anthropic(api_key=api_key)

    try:
        from cockpit.core.log_helpers import get_run_logger as _glog
        _logger = _glog(source.replace(".py", "").replace("/", "."))
    except Exception:  # noqa: BLE001
        _logger = None

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        if attempt > 0 and _logger is not None:
            _logger.retry(
                attempt=attempt,
                reason=f"{type(last_error).__name__ if last_error else 'unknown'}",
                source=source,
            )
        t0 = time.monotonic()
        try:
            chunks: list[str] = []
            if _logger is not None:
                _logger.info(
                    f"AI call → {kind}",
                    model=model, purpose=kind, source=source, attempt=attempt + 1,
                )
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            ) as stream:
                for text_delta in stream.text_stream:
                    chunks.append(text_delta)
                    yield "text", text_delta
                final = stream.get_final_message()

            latency_ms = int((time.monotonic() - t0) * 1000)
            in_tok = final.usage.input_tokens
            out_tok = final.usage.output_tokens
            usage = CallUsage(
                model=model,
                input_tokens=in_tok,
                output_tokens=out_tok,
                cost_usd=usage_tracker.estimate_cost_usd(model, in_tok, out_tok),
                latency_ms=latency_ms,
                ok=True,
            )
            _record(usage, kind=kind, source=source)
            if _logger is not None:
                _logger.ok(
                    f"AI call ok → {kind}",
                    model=model, purpose=kind, source=source,
                    ms=latency_ms, tokens_in=in_tok, tokens_out=out_tok,
                    cost_usd=round(usage.cost_usd, 4),
                )
            yield "usage", usage
            return

        except Exception as e:
            last_error = e
            should_retry = _is_retryable(e) and attempt < max_retries
            if not should_retry:
                latency_ms = int((time.monotonic() - t0) * 1000)
                usage = CallUsage(
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                    ok=False,
                    error=f"{type(e).__name__}: {str(e)[:200]}",
                )
                _record(usage, kind=kind, source=source)
                if _logger is not None:
                    _logger.error(
                        f"AI call error → {kind}",
                        model=model, purpose=kind, source=source,
                        ms=latency_ms, exc_type=type(e).__name__,
                    )
                raise AIClientError(usage.error) from e
            time.sleep(RETRY_BACKOFF_S[min(attempt, len(RETRY_BACKOFF_S) - 1)])

    raise AIClientError(f"Agotados {max_retries} reintentos: {last_error}")


def _is_retryable(e: Exception) -> bool:
    name = type(e).__name__
    if name in {"RateLimitError", "APIConnectionError", "APITimeoutError"}:
        return True
    status = getattr(e, "status_code", None)
    return status is not None and 500 <= int(status) < 600


def _record(usage: CallUsage, *, kind: str, source: str) -> None:
    usage_tracker.record(
        usage_tracker.UsageEvent(
            timestamp=usage_tracker.now_iso(),
            kind=kind,
            provider="anthropic",
            model=usage.model,
            source=source,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_usd=usage.cost_usd,
            latency_ms=usage.latency_ms,
            ok=usage.ok,
            error=usage.error,
        )
    )

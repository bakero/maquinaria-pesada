"""Componente reutilizable «✨ Mejorar con IA».

Cualquier página puede llamar `render_improve_block(...)` para añadir un
bloque expander con: textarea de petición, botón ejecutar, área de salida y
métricas de tokens/coste.

Modos:
  - verbose=True (default): streaming visible + contador de segundos +
    aviso al cruzar `slow_warning_seconds` (default 120 = 2 min).
  - verbose=False: spinner único, resultado al final.

No ejecuta nada al renderizar; solo al pulsar el botón.
"""
from __future__ import annotations

import time
from collections.abc import Callable

from cockpit.core import ai_client, sandbox

_DEFAULT_SYSTEM = (
    "Eres un arquitecto senior del sistema MaquinarIA Pesada (Python + Streamlit "
    "+ pipelines de generación de podcasts/vídeos con Anthropic, OpenAI y "
    "ElevenLabs). Tu rol es proponer mejoras concretas, accionables y mínimas. "
    "Responde en español de España, conciso, en formato lista numerada.\n\n"
    + sandbox.explain_policy()
    + "\n\nIMPORTANTE: si propones cambios que requieren tocar paths PROHIBIDOS, "
    "indícalo explícitamente como «requiere acción humana fuera del sandbox»."
)

DEFAULT_SLOW_WARNING_S = 120  # avisar si la generación tarda >2 min


def render_improve_block(
    *,
    source: str,
    context: str,
    title: str = "✨ Mejorar con IA",
    default_prompt: str = "Sugiere mejoras concretas a este componente.",
    system: str = _DEFAULT_SYSTEM,
    extra_context_builder: Callable[[], str] | None = None,
    model: str | None = None,
    kind: str = "improvement",
    verbose: bool = True,
    slow_warning_seconds: int = DEFAULT_SLOW_WARNING_S,
) -> None:
    """Renderiza el expander de mejora.

    Args:
      source: identificador del componente (e.g. "page:estado").
      context: texto que describe el componente al modelo.
      extra_context_builder: si se pasa, se llama al pulsar Ejecutar para añadir
        contexto fresco. Evita gasto en render.
      verbose: si True, streaming visible + contador.
      slow_warning_seconds: umbral en segundos para mostrar aviso de tarea lenta.
    """
    import streamlit as st

    with st.expander(title, expanded=False):
        st.caption(
            f"Pide a Claude sugerencias sobre **{source}**. Los tokens consumidos "
            "se registran en `logs/ai_usage.jsonl` y aparecen en la página Tokens."
        )

        prompt = st.text_area(
            "Tu petición",
            value=default_prompt,
            key=f"_improve_prompt_{source}",
            height=80,
        )
        col_model, col_verbose = st.columns([2, 1])
        model_pick = col_model.selectbox(
            "Modelo",
            options=["claude-sonnet-4-6", "claude-haiku-4-5", "claude-opus-4-7"],
            index=(
                0
                if model is None
                else [
                    "claude-sonnet-4-6",
                    "claude-haiku-4-5",
                    "claude-opus-4-7",
                ].index(model)
            ),
            key=f"_improve_model_{source}",
            help=(
                "Sonnet equilibra calidad/coste. Haiku para iteración rápida. "
                "Opus solo cuando Sonnet falle."
            ),
        )
        verbose_pick = col_verbose.toggle(
            "Modo verbose",
            value=verbose,
            key=f"_improve_verbose_{source}",
            help="Muestra la salida de Claude en streaming y un contador en vivo.",
        )

        if st.button("Generar sugerencias", key=f"_improve_btn_{source}"):
            extra = extra_context_builder() if extra_context_builder else ""
            user_msg = _build_user_message(context, extra, prompt)
            try:
                if verbose_pick:
                    text, usage = _stream_with_progress(
                        st,
                        system=system,
                        user_msg=user_msg,
                        source=source,
                        kind=kind,
                        model=model_pick,
                        slow_warning_seconds=slow_warning_seconds,
                    )
                else:
                    with st.spinner("Pidiendo a Claude…"):
                        text, usage = ai_client.improve_with_claude(
                            system=system,
                            user=user_msg,
                            source=source,
                            kind=kind,
                            model=model_pick,
                        )
            except ai_client.AIClientError as e:
                st.error(f"No se pudo completar la mejora: {e}")
                return

            st.success("Sugerencias generadas.")
            _warn_if_mentions_forbidden_paths(text)
            if not verbose_pick:
                # En verbose ya se mostró durante el streaming.
                st.markdown(text)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Input tokens", usage.input_tokens)
            col2.metric("Output tokens", usage.output_tokens)
            col3.metric("Coste (USD)", f"${usage.cost_usd:.4f}")
            col4.metric("Latencia (ms)", usage.latency_ms)


def _stream_with_progress(
    st,
    *,
    system: str,
    user_msg: str,
    source: str,
    kind: str,
    model: str,
    slow_warning_seconds: int,
):
    """Itera el stream cediendo updates a `st`. Devuelve (texto_final, CallUsage)."""
    status = st.status("Conectando con Claude…", expanded=True)
    timer_area = status.empty()
    text_area = status.empty()
    warning_shown = [False]

    chunks: list[str] = []
    usage_final = None
    t0 = time.monotonic()

    def _render_timer(elapsed: float, tokens: int) -> None:
        marker = "🟢" if elapsed < 30 else "🟡" if elapsed < slow_warning_seconds else "🔴"
        timer_area.caption(
            f"{marker} {elapsed:.1f}s transcurridos · {tokens} tokens recibidos"
        )

    try:
        for tag, payload in ai_client.improve_with_claude_stream(
            system=system,
            user=user_msg,
            source=source,
            kind=kind,
            model=model,
        ):
            elapsed = time.monotonic() - t0
            if tag == "text":
                chunks.append(payload)  # type: ignore[arg-type]
                # Throttle visual: render cada chunk es OK porque Streamlit
                # solo repinta el `empty()` afectado.
                text_area.markdown("".join(chunks))
                _render_timer(elapsed, sum(len(c) for c in chunks) // 4)
            elif tag == "usage":
                usage_final = payload  # type: ignore[assignment]

            if not warning_shown[0] and elapsed > slow_warning_seconds:
                warning_shown[0] = True
                st.warning(
                    f"⏱️ La generación lleva {elapsed:.0f}s "
                    f"(>{slow_warning_seconds}s). Si necesitas más velocidad, "
                    "cancela y prueba con un modelo más rápido (haiku) o un "
                    "prompt más corto."
                )
    except Exception:
        status.update(label="Falló la conexión con Claude", state="error")
        raise
    else:
        elapsed = time.monotonic() - t0
        if usage_final is not None:
            status.update(
                label=(
                    f"✅ Completado en {elapsed:.1f}s · "
                    f"{usage_final.input_tokens} in / {usage_final.output_tokens} out · "
                    f"${usage_final.cost_usd:.4f}"
                ),
                state="complete",
            )
        else:
            status.update(label="Completado", state="complete")

    assert usage_final is not None
    return "".join(chunks), usage_final


_FORBIDDEN_HINTS = (
    "cockpit/",
    "pyproject.toml",
    "requirements-cockpit.txt",
    ".github/",
    "generar_guion.py",
    "generar_episodio_v2.py",
    "validar_episodio.py",
    "normalizar_guiones.py",
    "podcast_spec.py",
)


def _warn_if_mentions_forbidden_paths(text: str) -> None:
    import streamlit as st

    hits = [p for p in _FORBIDDEN_HINTS if p in text]
    if not hits:
        return
    st.warning(
        "⚠️ La respuesta menciona paths fuera del sandbox de la IA: "
        + ", ".join(f"`{h}`" for h in hits)
        + ". Esos cambios requieren acción humana (revisión + commit manual). "
        "Claude no puede aplicarlos desde aquí."
    )


def _build_user_message(context: str, extra: str, prompt: str) -> str:
    parts = ["## Contexto del componente", context.strip()]
    if extra:
        parts.append("\n## Estado actual\n" + extra.strip())
    parts.append("\n## Petición\n" + prompt.strip())
    return "\n".join(parts)


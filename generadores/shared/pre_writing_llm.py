"""Extracción de pre-writing vía tool call de Haiku 4.5 (Fase 5.1, opt-in).

Activación: `MP_PREWRITING_LLM=1` en el entorno. Cuando NO está activo, los
generadores siguen usando `pre_writing.extract_pre_writing_cached` (regex
gratis y determinista).

Ventaja del LLM: mejor recall sobre PDFs largos o noisy. Coste residual
(~$0.0005 por extracción con Haiku) amortizado por el cache en disco.

Schema de tool: `extract_pre_writing` con strict=True para que Anthropic
fuerce la estructura.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from generadores.shared.pre_writing import PreWriting, extract_pre_writing

logger = logging.getLogger(__name__)

_TOOL_NAME = "extract_pre_writing"
_HAIKU_MODEL = "claude-haiku-4-5-20251001"
_MAX_PDF_CHARS = 15000

EXTRACT_TOOL_SCHEMA: dict = {
    "name": _TOOL_NAME,
    "description": (
        "Extrae datos numéricos, casos empresariales con nombre propio, "
        "frases-fuerza y datos contraintuitivos del PDF fuente para guiar la "
        "redacción del guion del podcast."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "datos_numericos": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 10,
                "description": (
                    "Cifras concretas con contexto breve (ej: '88% de "
                    "proyectos de IA empresarial no llegan a producción')."
                ),
            },
            "casos_nombre_propio": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 8,
                "description": (
                    "Nombres de empresas o instituciones mencionadas como "
                    "caso (ej: 'Harvey AI', 'Morgan Stanley')."
                ),
            },
            "frase_fuerza": {
                "type": "string",
                "description": (
                    "Una sola frase memorable del documento, citable casi "
                    "literal en el HOOK."
                ),
            },
            "contraintuitivos": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
                "description": (
                    "Hechos que contradicen la intuición común sobre el tema."
                ),
            },
        },
        "required": [
            "datos_numericos", "casos_nombre_propio", "frase_fuerza",
            "contraintuitivos",
        ],
    },
}


def is_enabled() -> bool:
    return os.environ.get("MP_PREWRITING_LLM", "").strip() in {"1", "true", "yes"}


def extract_with_llm(pdf_text: str) -> PreWriting:
    """Llama a Haiku con tool call. Si falla, cae al extractor regex."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("MP_PREWRITING_LLM activo pero falta ANTHROPIC_API_KEY")
        return extract_pre_writing(pdf_text)
    try:
        import anthropic
    except ImportError:  # pragma: no cover
        return extract_pre_writing(pdf_text)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=_HAIKU_MODEL,
            max_tokens=2000,
            temperature=0.0,
            tools=[EXTRACT_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[{
                "role": "user",
                "content": (
                    "Extrae la pre-escritura del siguiente PDF "
                    "(formato JSON vía tool call):\n\n"
                    f"{pdf_text[:_MAX_PDF_CHARS]}"
                ),
            }],
        )
        tool_use = next(
            (b for b in response.content if getattr(b, "type", "") == "tool_use"),
            None,
        )
        if tool_use is None:
            logger.warning("Haiku no devolvió tool_use; cae a regex")
            return extract_pre_writing(pdf_text)
        data = tool_use.input
        return PreWriting(
            datos_numericos=list(data.get("datos_numericos", []))[:10],
            casos_nombre_propio=list(data.get("casos_nombre_propio", []))[:8],
            frase_fuerza=str(data.get("frase_fuerza", "") or ""),
            contraintuitivos=list(data.get("contraintuitivos", []))[:5],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fallo extracción LLM (%s); cae a regex", exc)
        return extract_pre_writing(pdf_text)


def extract_cached_llm(pdf_text: str, cache_dir: Path) -> PreWriting:
    """Variante cacheada de extract_with_llm.

    Cache key: sha256(pdf_text) + sufijo `_llm` para no colisionar con el
    cache del extractor regex.
    """
    if not pdf_text:
        return PreWriting()
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(pdf_text.encode("utf-8")).hexdigest()[:16]
    cache_file = cache_dir / f"{key}_llm.json"
    if cache_file.exists():
        try:
            return PreWriting(**json.loads(cache_file.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, TypeError, OSError):
            pass
    pw = extract_with_llm(pdf_text)
    try:
        cache_file.write_text(
            json.dumps(asdict(pw), ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass
    return pw


def extract_auto(pdf_text: str, cache_dir: Path) -> PreWriting:
    """Helper que respeta el flag `MP_PREWRITING_LLM`.

    Llamado por m/t_generator: si el flag está activo usa Haiku, si no,
    usa el extractor regex cacheado del módulo `pre_writing`.
    """
    if is_enabled():
        return extract_cached_llm(pdf_text, cache_dir)
    from generadores.shared.pre_writing import extract_pre_writing_cached
    return extract_pre_writing_cached(pdf_text, cache_dir)

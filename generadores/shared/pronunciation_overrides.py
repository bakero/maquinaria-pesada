"""Overrides de pronunciación para anglicismos técnicos.

Audio-Regla del invariante TTS v6: a velocidad acelerada, palabras técnicas
inglesas pierden claridad. Esta capa pre-TTS sustituye o anota anglicismos por
formas más leíbles para ElevenLabs en español.

El diccionario se carga de `pronunciation_overrides.json` en la raíz del repo.
Si no existe o no se puede leer, se genera el JSON inicial híbrido (extraído
del glosario `PDFs/auxiliares/glosario_unificado.md` + añadidos manuales).
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

DEFAULT_OVERRIDES_PATH = Path(__file__).resolve().parents[2] / "pronunciation_overrides.json"

# Añadidos manuales obvios: nombres propios cuya pronunciación TTS conviene fijar.
_MANUAL_BASELINE: dict[str, str] = {
    "LLM": "elemen",
    "LLMs": "elemenes",
    "RAG": "rag",
    "MLOps": "eme ele ops",
    "LLMOps": "elemen ops",
    "PyTorch": "paitorch",
    "Hugging Face": "hagin feis",
    "GPT-4": "yi pi ti cuatro",
    "GPT-3": "yi pi ti tres",
    "Claude": "clod",
    "OpenAI": "open ei ai",
    "Anthropic": "anzropic",
    "DeepMind": "dipmaind",
    "TensorFlow": "tensorflou",
    "embeddings": "embedins",
    "embedding": "embedin",
    "fine-tuning": "fain tiuning",
    "fine tuning": "fain tiuning",
    "prompt": "promp",
    "tokens": "tokens",
    "transformer": "transformer",
    "backpropagation": "back propa gation",
}


def load_overrides(path: Path | None = None) -> dict[str, str]:
    """Carga el diccionario de overrides. Si el JSON falta, devuelve baseline."""
    path = path or DEFAULT_OVERRIDES_PATH
    if not path.exists():
        return dict(_MANUAL_BASELINE)
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return dict(_MANUAL_BASELINE)
        # Merge baseline + JSON, con prioridad al JSON.
        merged = dict(_MANUAL_BASELINE)
        merged.update({str(k): str(v) for k, v in data.items()})
        return merged
    except (OSError, json.JSONDecodeError):
        return dict(_MANUAL_BASELINE)


def save_overrides(overrides: dict[str, str], path: Path | None = None) -> Path:
    """Guarda el diccionario de overrides en disco."""
    path = path or DEFAULT_OVERRIDES_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(overrides, fh, ensure_ascii=False, indent=2, sort_keys=True)
    return path


_GLOSARIO_HEADING = re.compile(r"^##\s+(.+?)(?:\s+\((.+?)\))?\s*$", re.MULTILINE)


def extract_from_glosario(glosario_text: str) -> dict[str, str]:
    """Genera la primera versión automática desde el glosario.

    Reglas:
    - Entradas con paréntesis (siglas) → la sigla canónica entra como override
      con su forma deletreada en castellano cuando sea anglicismo de ≥3 letras.
    - Términos en CamelCase (PyTorch, OpenAI) → preservar tal cual con
      pronunciación aproximada si está en _MANUAL_BASELINE.

    Aporta un primer ~70-80% de cobertura. Los faltantes se añaden a mano.
    """
    out: dict[str, str] = {}
    for m in _GLOSARIO_HEADING.finditer(glosario_text):
        term = m.group(1).strip()
        sigla = (m.group(2) or "").strip()
        # Si el título es una sigla en mayúsculas (LLM, RAG) → pronunciación.
        if re.fullmatch(r"[A-Z]{2,5}s?", term):
            if term not in out:
                out[term] = _spell_sigla(term)
        if sigla and re.fullmatch(r"[A-Z][A-Za-z\s\-]+", sigla):
            out.setdefault(term, sigla)
    return out


def _spell_sigla(sigla: str) -> str:
    """Pronunciación letra a letra en español (LLM → 'ele ele eme')."""
    letters = {
        "A": "a", "B": "be", "C": "ce", "D": "de", "E": "e", "F": "efe",
        "G": "ge", "H": "hache", "I": "i", "J": "jota", "K": "ka", "L": "ele",
        "M": "eme", "N": "ene", "Ñ": "eñe", "O": "o", "P": "pe", "Q": "cu",
        "R": "erre", "S": "ese", "T": "te", "U": "u", "V": "uve", "W": "uve doble",
        "X": "equis", "Y": "i griega", "Z": "zeta",
    }
    return " ".join(letters.get(c.upper(), c) for c in sigla if c.isalpha())


def apply_overrides(text: str, overrides: dict[str, str] | None = None) -> str:
    """Sustituye los términos del diccionario por su forma pronunciable."""
    overrides = overrides or load_overrides()
    if not overrides:
        return text
    # Sustituimos de más largo a más corto para no romper términos compuestos.
    keys: Iterable[str] = sorted(overrides.keys(), key=len, reverse=True)
    out = text
    for k in keys:
        if not k.strip():
            continue
        # Coincidencia palabra-completa case-sensitive para no machacar texto normal.
        pattern = re.compile(r"(?<![\w])" + re.escape(k) + r"(?![\w])")
        out = pattern.sub(overrides[k], out)
    return out

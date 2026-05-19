"""Datos normativos del proyecto (constantes).

Cargados de los JSON embebidos en PODCAST_*_SPEC.md cuando están disponibles;
en caso contrario usa los defaults documentados en EVALUADOR_GUIONES.md §10.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------- Frases canónicas (defaults) ----------

HOOK_CLOSING_PHRASE = "Esto es MaquinarIA Pesada. Arrancamos."
INTRO_COMMENT_PATTERN = re.compile(r"\[\s*INTRO\b.*?\]", re.IGNORECASE)
CIERRE_CONCEPTOS_OPENER = (
    "No te puedes ir de este capitulo sin haber entendido estos conceptos"
)
CIERRE_FINAL_LITERAL = (
    "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. "
    "Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A."
)
S_CLOSING_TEMPLATE = "Más sobre {tema} en el episodio T de MaquinarIA Pesada."
S_CLOSING_REGEX = re.compile(
    r"M[aá]s\s+sobre\s+.+?\s+en\s+el\s+episodio\s+T\s+de\s+MaquinarIA\s+Pesada\.?\s*$",
    re.IGNORECASE,
)

# ---------- Aviso IA ----------

AVISO_IA_KEYWORDS = ["sistema automatico", "puede contener errores"]

# ---------- Secciones M v6 ----------

M_REQUIRED_SECTIONS = [
    "HOOK",
    "INTRO_SONIDO",
    "SALUDO_Y_PRESENTACION",
    "BLOQUE_PANORAMA",
    "BLOQUE_DESTACADO",
    "APLICACION_PRACTICA",
    "BLOQUE_FUENTES",
    "CIERRE_CONCEPTOS",
    "CIERRE_FINAL",
]
# VERIFICACIONES es opcional fin-de-archivo, lo manejamos aparte.
M_OPTIONAL_SECTIONS = ["VERIFICACIONES"]

# ---------- Secciones T v6 ----------

T_REQUIRED_SECTIONS = [
    "HOOK",
    "INTRO_SONIDO",
    "SALUDO_Y_PRESENTACION",
    "BLOQUE_PANORAMA",
    "BLOQUE_COMO",
    "BLOQUE_REALIDAD",  # alias: BLOQUE_CASOS
    "BLOQUE_LIMITES",
    "BLOQUE_FUENTES",
    "CIERRE_CONCEPTOS",
    "CIERRE_FINAL",
]
T_OPTIONAL_SECTIONS = ["VERIFICACIONES"]

# BLOQUE_REALIDAD y BLOQUE_CASOS son equivalentes (T v6 los usa de forma intercambiable)
T_REALIDAD_ALIASES = {"BLOQUE_REALIDAD", "BLOQUE_CASOS"}

# ---------- Secciones prohibidas ----------

FORBIDDEN_LEGACY_SECTIONS = {
    "BLOQUE_1",
    "BLOQUE_2",
    "BLOQUE_3",
    "BLOQUE_4",
    "BLOQUE_5",
    "BLOQUE_6",
    "BLOQUE_QUE",
    "BLOQUE_TEMAS_CLAVE",
    "INSERCION_1",
    "INSERCION_2",
    "INSERCION_3",
    "INSERCION_EMPRESA",
}

# APLICACION_PRACTICA es exclusivo de M (prohibido en T)
T_FORBIDDEN_SECTIONS = {"APLICACION_PRACTICA"}

# ---------- Word count por tipo ----------

WORD_COUNT_RANGES = {
    "M": (2700, 3300),
    "T": (3700, 4500),
    "S": (157, 198),
}

# ---------- Paridad opener ----------

# M par → Maria, M impar → Yago
# T impar → Yago, T par → Maria
# S impar → Yago (voz), S par → Maria (voz)
def expected_opener_M(module_n: int) -> str:
    return "IAGO" if module_n % 2 == 1 else "MARIA"


def expected_opener_T(tema_n: int) -> str:
    return "IAGO" if tema_n % 2 == 1 else "MARIA"


def expected_voice_S(s_n: int) -> str:
    return "IAGO" if s_n % 2 == 1 else "MARIA"


# ---------- Blacklist de interjecciones coro ----------

BLACKLIST_INTERJECTIONS = [
    "exactamente",
    "claro que sí",
    "claro que si",
    "muy bien dicho",
    "tienes toda la razón",
    "tienes toda la razon",
    "exacto",
    "por supuesto",
    "eso es",
    "totalmente",
]

# ---------- Catálogo de etiquetas TTS permitidas ----------

TTS_TAGS_ALLOWED = {
    "didactico",
    "explicativo",
    "directo",
    "serio",
    "firme",
    "contundente",
    "grave",
    "tenso",
    "conversacional",
    "reflexivo",
    "reflexiva",
    "curioso",
    "curiosa",
    "ironico",
    "esceptico",
    "escéptica",
    "esceptica",
    "natural",
    "pausado",
    "calido",
    "claro",
    "clara",
    "analitico",
    "analitica",
    "enfatico",
}


def normalize_tag(tag: str) -> str:
    """Normaliza una etiqueta TTS quitando acentos y pasando a minúsculas."""
    repl = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return tag.strip().lower().translate(repl)


# ---------- Términos críticos para pedagogía ----------

PEDAGOGY_COMPLEX_TERMS = [
    "backpropagation",
    "embedding",
    "attention",
    "transformer",
    "prompt injection",
    "RAG",
    "fine tuning",
    "fine-tuning",
    "RLHF",
    "chain of thought",
    "golden dataset",
    "agentic AI",
    "hallucination",
    "BERT",
    "MCP",
    "PCA",
    "LLM as judge",
    "HITL",
    "prompt",
]

PEDAGOGY_ANALOGY_MARKERS = [
    "imagina que",
    "es como cuando",
    "piensa en",
    "el equivalente sería",
    "el equivalente seria",
    "en tu día a día",
    "en tu dia a dia",
    "igual que",
    "lo mismo que pasa cuando",
    "es como",
]

# ---------- Carga de JSON desde specs ----------

_SPEC_JSON_CACHE: dict[str, dict] = {}


def load_spec_json(kind: str) -> dict | None:
    """Carga el bloque JSON embebido en PODCAST_{kind}_SPEC.md.

    Devuelve None si no está disponible.
    """
    if kind in _SPEC_JSON_CACHE:
        return _SPEC_JSON_CACHE[kind]

    spec_file = REPO_ROOT / f"PODCAST_{kind}_SPEC.md"
    if not spec_file.exists():
        return None

    text = spec_file.read_text(encoding="utf-8")
    start_marker = f"<!-- PODCAST_{kind}_SPEC_JSON_START -->"
    end_marker = f"<!-- PODCAST_{kind}_SPEC_JSON_END -->"
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start < 0 or end < 0 or end <= start:
        return None

    block = text[start + len(start_marker) : end]
    # extraer contenido entre ```json y ```
    m = re.search(r"```json\s*(\{.*?\})\s*```", block, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    _SPEC_JSON_CACHE[kind] = data
    return data

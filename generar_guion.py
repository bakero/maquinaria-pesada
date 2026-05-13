#!/usr/bin/env python3
"""
generar_guion.py — Generador de guiones M (Módulo) para MaquinarIA Pesada.

Genera guiones de episodios M usando:
  - PDF RESUMEN del módulo como fuente conceptual
  - 4 documentos vivos del proyecto (BIBLIA_SISTEMA, PRIMERPODCAST, VIDEOPODCAST, PODCAST)
    como fuente de APLICACION_PRACTICA
  - Claude Sonnet 4.5 para generación y Claude Haiku para extracción de conceptos

Nomenclatura de salida:
  Guiones/M{n}_Nombre_del_Modulo.txt

Uso:
  python generar_guion.py --modulo 0 --pdf PDFs/resumenes/RESUMEN_M0_Introduccion_Estrategica.pdf
  python generar_guion.py --modulo 6 --pdf PDFs/resumenes/RESUMEN_M6_Ingenieria_Prompts.pdf --nombre "Ingenieria de Prompts"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR  = Path(__file__).parent
SPEC_PATH = BASE_DIR / "PODCAST_M_SPEC.md"

sys.path.insert(0, str(BASE_DIR))
from podcast_spec import (
    build_script_stats,
    extract_theme_concepts,
    guion_to_ep_code,
    load_spec,
    normalize_text_for_match,
    opening_speaker,
    read_text,
    remove_leading_tag,
    validate_script_text,
)

# ---------------------------------------------------------------------------
# Uso de tokens Anthropic
# ---------------------------------------------------------------------------

@dataclass
class TokenUsage:
    input_tokens:  int = 0
    output_tokens: int = 0
    cache_read:    int = 0
    cache_create:  int = 0

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, response) -> None:
        usage = getattr(response, "usage", None)
        if not usage:
            return
        self.input_tokens  += getattr(usage, "input_tokens",             0) or 0
        self.output_tokens += getattr(usage, "output_tokens",            0) or 0
        self.cache_read    += getattr(usage, "cache_read_input_tokens",  0) or 0
        self.cache_create  += getattr(usage, "cache_creation_input_tokens", 0) or 0

    def report(self) -> str:
        return (
            f"input={self.input_tokens} output={self.output_tokens} "
            f"cache_read={self.cache_read} cache_create={self.cache_create} "
            f"total={self.total}"
        )


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def extract_pdf_text(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {path}")
    parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t.strip())
    text = "\n\n".join(parts)
    if not text:
        raise ValueError(f"No se pudo extraer texto de {path}")
    return text


# ---------------------------------------------------------------------------
# Documentos vivos
# ---------------------------------------------------------------------------

LIVE_DOCS = [
    ("BIBLIA_SISTEMA",  "BIBLIA_SISTEMA.md"),
    ("PRIMERPODCAST",   "PRIMERPODCAST.md"),
    ("VIDEOPODCAST",    "VIDEOPODCAST.md"),
    ("PODCAST",         "PODCAST.md"),
]


def load_live_docs(base: Path) -> dict[str, str]:
    """Carga los 4 documentos vivos. Registra WARN si alguno falta."""
    docs: dict[str, str] = {}
    for name, filename in LIVE_DOCS:
        path = base / filename
        if path.exists():
            docs[name] = read_text(path)
        else:
            print(f"[WARN] Documento vivo no encontrado: {filename}")
    return docs


def extract_aplicacion_material(
    docs: dict[str, str],
    modulo_n: int,
    concept_keywords: list[str],
    spec: dict,
) -> dict:
    """Extrae material verificable de los docs vivos para APLICACION_PRACTICA.

    Busca párrafos que mencionen conceptos del módulo o tecnologías relacionadas.
    Devuelve un dict con la ficha de aplicación.
    Returns None fields as empty strings if insufficient material.
    """
    # Keywords de búsqueda: conceptos del PDF + número de módulo
    search_terms = [normalize_text_for_match(k) for k in concept_keywords[:6]]
    search_terms.append(f"m{modulo_n}")

    # Marcadores de decisión en PODCAST.md
    decision_markers = ["[decisión]", "[cambio]", "[incidencia]", "[regla]", "[producción]"]

    hits: dict[str, list[str]] = {name: [] for name in docs}

    for doc_name, doc_text in docs.items():
        paragraphs = [
            re.sub(r"\s+", " ", p).strip()
            for p in re.split(r"\n{2,}", doc_text)
            if p.strip() and len(p.strip()) > 80
        ]
        for para in paragraphs:
            para_norm = normalize_text_for_match(para)
            # Match si contiene algún término de búsqueda O un marcador de decisión
            has_concept = any(term in para_norm for term in search_terms)
            has_marker  = any(m in para_norm for m in decision_markers)
            if has_concept or has_marker:
                hits[doc_name].append(para[:600])

    # Construir ficha
    all_hits = [p for paragraphs in hits.values() for p in paragraphs]
    ficha = {
        "modulo_n":              modulo_n,
        "paragraphs_found":      len(all_hits),
        "hits_by_doc":           {k: len(v) for k, v in hits.items()},
        "problema_concreto":     "",
        "decision_tomada":       "",
        "cifras_verificables":   [],
        "conexion_conceptos":    [],
        "fuentes_consultadas":   [],
        "material_snippet":      "",
    }

    # Seleccionar los mejores párrafos por doc
    selected_paragraphs: list[str] = []
    for doc_name, paragraphs in hits.items():
        if paragraphs:
            ficha["fuentes_consultadas"].append(doc_name)
            selected_paragraphs.extend(paragraphs[:3])

    if selected_paragraphs:
        ficha["material_snippet"] = "\n\n".join(selected_paragraphs[:8])

    # Mínimo requerido: 1 problema + 1 decisión + 1 cifra (verificado en caller)
    ficha["paragraphs_sufficient"] = len(all_hits) >= 3

    return ficha


def save_aplicacion_artifact(ficha: dict, modulo_n: int, base: Path) -> Path:
    """Guarda la ficha de extracción en episodios/temp/aplicacion_extraida_M{n}.md."""
    temp_dir = base / "episodios" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = temp_dir / f"aplicacion_extraida_M{modulo_n}.md"
    lines = [
        f"# Ficha de aplicación del módulo M{modulo_n}",
        "",
        f"**Párrafos encontrados:** {ficha['paragraphs_found']}",
        f"**Por documento:** {ficha['hits_by_doc']}",
        f"**Fuentes consultadas:** {', '.join(ficha['fuentes_consultadas'])}",
        "",
        "## Material extraído",
        "",
        ficha.get("material_snippet", "(sin material)"),
    ]
    artifact_path.write_text("\n".join(lines), encoding="utf-8")
    return artifact_path


# ---------------------------------------------------------------------------
# Cliente Anthropic
# ---------------------------------------------------------------------------

def make_anthropic_client():
    try:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise SystemExit("ANTHROPIC_API_KEY no encontrada en .env")
        return anthropic.Anthropic(api_key=api_key)
    except ImportError as err:
        raise SystemExit("Faltan dependencias: pip install anthropic") from err


def call_claude(client, model: str, system: str, user: str, max_tokens: int, temperature: float) -> tuple[str, object]:
    """Llama a Claude y devuelve (content_text, response)."""
    import time as _t
    _t0 = _t.monotonic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    try:
        from cockpit.core.usage_tracker import track_anthropic
        track_anthropic(
            response, model=model, source="generar_guion.py", kind="generation",
            latency_ms=int((_t.monotonic() - _t0) * 1000),
        )
    except ImportError:
        pass
    return response.content[0].text, response


# ---------------------------------------------------------------------------
# Extracción de conceptos del PDF
# ---------------------------------------------------------------------------

def extract_concepts_with_claude(
    client,
    spec: dict,
    pdf_text: str,
    topic: str,
    usage: TokenUsage,
) -> tuple[list[str], list[str]]:
    """Extrae conceptos clave con Claude Haiku. Devuelve (concepts, hard_for_audio)."""
    model = spec["anthropic"]["default_concept_model"]
    system = (
        "Extrae conceptos clave de un PDF técnico. "
        "Devuelve solo JSON válido. No expliques nada."
    )
    user = (
        f"TEMA: {topic}\n\n"
        "PDF:\n"
        f"{pdf_text[:15000]}\n\n"
        "Devuelve JSON exactamente así (usa nombres CORTOS de 1-3 palabras, sin paréntesis ni explicaciones):\n"
        '{"key_concepts": ["RPA", "embeddings", "RAG"], '
        '"hard_for_audio": ["backpropagation"]}'
        "\nLos key_concepts deben ser las palabras/siglas exactas tal como aparecen en el PDF."
    )
    try:
        text, resp = call_claude(client, model, system, user, max_tokens=1000, temperature=0.0)
        usage.add(resp)
        # Strip markdown code fences if Haiku wraps the JSON
        raw = text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw.strip())
        data = json.loads(raw)
        concepts   = [c.strip() for c in data.get("key_concepts", []) if c.strip()][:10]
        hard_audio = [c.strip() for c in data.get("hard_for_audio", []) if c.strip()][:5]
        return concepts, hard_audio
    except Exception as e:
        print(f"[WARN] Extracción de conceptos con Haiku fallida ({e}), usando heurística.")
        return extract_theme_concepts(pdf_text, limit=8), []


# ---------------------------------------------------------------------------
# Generación del guion
# ---------------------------------------------------------------------------

def build_generation_prompt(
    spec: dict,
    spec_markdown: str,
    modulo_n: int,
    topic: str,
    pdf_text: str,
    opener: str,
    concept_list: list[str],
    ficha: dict,
    hard_audio: list[str],
) -> tuple[str, str]:
    """Construye system + user para la generación del guion M."""

    other = "IAGO" if opener == "MARIA" else "MARIA"

    system = (
        "Eres el sistema de producción del podcast MaquinarIA Pesada. "
        "Generas guiones de episodios M (módulo): piezas de captación/marketing con contenido riguroso. "
        "Audiencia: oyentes nuevos + profesionales que ya conocen los T del módulo. "
        "El episodio M cubre los 2-3 conceptos MÁS IMPACTANTES del módulo (no todos). "
        "Sigues la especificación PODCAST_M_SPEC.md v5 al pie de la letra. "
        "Devuelves SOLO el guion. Sin explicaciones, sin markdown adicional. "
        "Todas las intervenciones empiezan por IAGO: o MARIA:. "
        "No incluyas la sección # VERIFICACIONES; el sistema la añade después."
    )

    ficha_text = (
        f"Párrafos encontrados en docs vivos: {ficha['paragraphs_found']}\n"
        f"Por documento: {ficha['hits_by_doc']}\n"
        f"Material:\n{ficha.get('material_snippet', '(sin material externo verificable)')}"
    )

    rules = spec["script_rules"]

    user = f"""ESPECIFICACION MAESTRA (PODCAST_M_SPEC.md v5):
{spec_markdown}

PARÁMETROS DEL EPISODIO:
- Módulo: M{modulo_n}
- Tema: {topic}
- Hook abre: {opener} (paridad del módulo)
- Duración objetivo: {spec['episode_defaults']['duration_minutes']} min (rango: {spec['episode_defaults']['duration_range_minutes']})

PDF RESUMEN DEL MÓDULO (fuente primaria para bloques conceptuales):
{pdf_text[:20000]}

CONCEPTOS CLAVE EXTRAÍDOS DEL PDF (cubre al menos el 75%):
{json.dumps(concept_list, ensure_ascii=False)}

TÉRMINOS DIFÍCILES PARA AUDIO (traduce y aterriza en el guion):
{json.dumps(hard_audio, ensure_ascii=False)}

MATERIAL DE APLICACION_PRACTICA (extraído de los 4 documentos vivos):
{ficha_text}

INSTRUCCIONES CRÍTICAS:
1. El hook lo abre {opener}. Cierra exactamente con: {rules['hook_closing_phrase']}
2. Después del hook incluye exactamente: # INTRO_SONIDO  (siguiente línea: {rules['intro_comment']})
3. SALUDO_Y_PRESENTACION — FORMATO OBLIGATORIO DE TRES INTERVENCIONES SEPARADAS:
   (siendo OPENER = {opener} y OTRO = {other}; nombres hablados: IAGO->"Yago", MARIA->"Maria")
   Linea 1 — OPENER: [natural] Bienvenidos a MaquinarIA Pesada... Soy <nombre_opener>.
   Linea 2 — OTRO:   [natural] Y yo soy <nombre_otro>.
   Linea 3 — OPENER: [directo] Antes de empezar, lo de siempre: este episodio lo genera un sistema automatico de inteligencia artificial. Puede contener errores. Si oyes algo que no te cuadra, contrastalo. El sistema que produce este podcast tambien es contenido del podcast: al final del episodio veremos como se aplica lo de hoy a ese sistema.
   HARD-FAIL si: (a) un mismo speaker concatena su nombre y el del otro en una misma linea, (b) el aviso lo dice cualquiera que no sea {opener}, (c) faltan "sistema automatico" o "puede contener errores".
   PROHIBIDO: apellidos. Los presentadores se llaman Maria y Yago, sin apellidos.
4. Estructura obligatoria en orden (v5 — SIN BLOQUE_LIMITES):
   # HOOK → # INTRO_SONIDO → # SALUDO_Y_PRESENTACION → # BLOQUE_PANORAMA → # BLOQUE_DESTACADO → # APLICACION_PRACTICA → # CIERRE_CONCEPTOS → # CIERRE_FINAL
5. Secciones PROHIBIDAS (no las generes): BLOQUE_LIMITES, BLOQUE_TEMAS_CLAVE, BLOQUE_REALIDAD, BLOQUE_1, BLOQUE_2, BLOQUE_3, BLOQUE_4, BLOQUE_QUE, BLOQUE_COMO, INSERCION_1, INSERCION_2, INSERCION_3, INSERCION_EMPRESA
6. BLOQUE_DESTACADO — criterios y estructura OBLIGATORIA:
   Criterios de selección de los 2-3 conceptos (aplica en este orden):
   a) El más contraintuitivo del módulo (lo que la mayoría no sabe o cree lo contrario).
   b) El más relevante para profesionales no técnicos (CTOs, CEOs, directores de área).
   c) El que mejor conecta con la APLICACION_PRACTICA.
   REPARTO POR CONCEPTO — el "líder" da la explicación COMPLETA del concepto (4-6 frases, 60-100 palabras):
   - Con 2 conceptos: Concepto A → IAGO lidera (4-6 frases desarrollo) + MARIA 1-2 preguntas.
                      Concepto B → MARIA lidera (4-6 frases desarrollo completo) + IAGO 1-2 preguntas.
   - Con 3 conceptos: A→IAGO lidera, B→MARIA lidera, C→IAGO lidera.
   OBLIGATORIO: MARIA debe tener al menos UN bloque de desarrollo de 4-6 frases (60-100 palabras).
   EJEMPLO CORRECTO de MARIA liderando:
     MARIA: [explicativo] La gobernanza de IA no es solo un conjunto de reglas formales. Es el sistema de toma de decisiones que determina quién es responsable de qué cuando un modelo falla. Piénsalo como la diferencia entre tener un reglamento interno y tener una estructura de auditoría real. El reglamento dice qué hacer. La gobernanza decide quién lo verifica y qué consecuencias hay si no se cumple.
   PROHIBIDO: que MARIA solo haga preguntas de 5-10 palabras en BLOQUE_DESTACADO.
   Objetivo cuantitativo: IAGO 40-60%, MARIA 40-60% del total de palabras del bloque.
7. APLICACION_PRACTICA: 3 momentos internos SIEMPRE así:
   - Momento 1 (MARIA plantea, ~45-60s): "Ahora veamos cómo todo esto se aplica en un sistema real. Concretamente, en el sistema que está generando este podcast. La pregunta es: ¿[pregunta operativa del módulo]?"
   - Momento 2 (IAGO detalla en HIGH-LEVEL, ~2-2.5 min): IAGO conecta el módulo con el sistema de forma CONCEPTUAL, NO técnica. Patrón: "esto que acabas de aprender es exactamente lo que hace posible que [X del sistema]". NO citar nombres de archivos, funciones, parámetros ni costes específicos. NO dar detalles de implementación. Debe sonar como revelación natural. Usa el material de los docs vivos en nivel conceptual.
   - Momento 3 (cierre conjunto MARIA+IAGO, ~30-45s): MARIA pregunta o señala el aprendizaje. IAGO lo aterriza. Frase final que conecta de vuelta con el módulo.
8. CIERRE_CONCEPTOS — estructura EXACTA:
   La sección tiene entre 3 y 5 bloques hablados EN TOTAL (el validador cuenta todos los bloques, incluida la apertura).
   Bloque 1 (apertura): {opener} dice exactamente: "{rules['concepts_closing_phrase']}"
   Bloques 2-4: lista de 2 a 4 conceptos clave (uno por bloque, alternando speakers).
   TOTAL bloques: 3 (1 apertura + 2 conceptos) a 5 (1 apertura + 4 conceptos). NUNCA 6.
   Al menos un concepto conectado con APLICACION_PRACTICA.
9. CIERRE_FINAL incluye exactamente: {rules['final_closing_phrase']}
   SOLO {opener} pronuncia el cierre (paridad). {other} NO responde ni añade nada. El guion termina cuando {opener} dice su última frase. HARD-FAIL si hay intervención de {other} tras el cierre.
   CTA OBLIGATORIA (integrar de forma natural antes de la frase final): mencionar que los episodios del módulo ya están disponibles. Ejemplo: "...y si quieres profundizar en cualquiera de estos conceptos, los episodios del módulo ya están disponibles en nuestras plataformas habituales." Debe sonar natural, no como anuncio.
10. Interjecciones PROHIBIDAS: {json.dumps(rules['blacklist_validation_interjections'], ensure_ascii=False)}
11. Usa "Yago" en el texto hablado, nunca "Iago".
12. LONGITUD DEL GUION — REGLA DURA:
    El total del guion (incluyendo sección VERIFICACIONES) debe estar entre {rules['minimum_word_count']} y {rules['maximum_word_count']} palabras.
    La sección VERIFICACIONES añade ~200 palabras. Por tanto el DIÁLOGO puro debe tener entre {rules['minimum_word_count']-200} y {rules['maximum_word_count']-200} palabras.
    OBJETIVO DE DIÁLOGO: apunta a {rules['minimum_word_count']+200} palabras de diálogo (margen de seguridad frente al mínimo total).
    CONTROL EN TIEMPO REAL: antes de APLICACION_PRACTICA cuenta las palabras del diálogo generado hasta ahí.
    Si llevas menos de {rules['minimum_word_count']-500} palabras, AÑADE un bloque extra completo en BLOQUE_DESTACADO antes de continuar.
    REGLA DE DENSIDAD POR SECCIÓN:
    - BLOQUE_PANORAMA: cada bloque IAGO debe tener 4-6 frases (70-100 palabras). MARIA solo hace preguntas ≤20 palabras.
    - BLOQUE_DESTACADO: cada bloque de desarrollo debe tener 4-6 frases. Ambos speakers desarrollan conceptos completos.
    - APLICACION_PRACTICA: mínimo 5 bloques de desarrollo de 4-6 frases (no 4). Cada bloque: 70-100 palabras.
    REGLA ABSOLUTA: todo bloque de desarrollo (no preguntas ni reacciones) DEBE tener EXACTAMENTE 4-6 frases. Está PROHIBIDO escribir un bloque de desarrollo con 3 frases o menos. Cuenta antes de avanzar.
    Si al llegar a APLICACION_PRACTICA llevas más de {int(rules['maximum_word_count'] * 0.72)} palabras, limita APLICACION_PRACTICA a 400 palabras.
13. REGLA CIERRE — PRIMERA:
    Antes de escribir BLOQUE_PANORAMA, redacta mentalmente los 3-5 puntos del CIERRE_CONCEPTOS.
    Cuando llegues al CIERRE_CONCEPTOS, escribe EXACTAMENTE esos puntos.
14. BALANCE OBLIGATORIO DE PALABRAS POR BLOQUE:
    - BLOQUE_PANORAMA: IAGO debe tener ≥65% de las palabras. MARIA hace ≤3 preguntas cortas (≤20 palabras cada una).
    - BLOQUE_DESTACADO: COMPARTIDO. OBLIGATORIO que IAGO y MARIA tengan cada uno ENTRE 40%-60% del total de palabras del bloque.
      Para lograrlo: MARIA debe tener AL MENOS 2 bloques de desarrollo de 4-6 frases (70-100 palabras cada uno) dentro de BLOQUE_DESTACADO.
      NO es válido que MARIA solo haga preguntas cortas en BLOQUE_DESTACADO. MARIA debe explicar conceptos completos.
    - APLICACION_PRACTICA: MARIA 30-40%, IAGO 60-70%.
15. REGLA ANALOGÍA — DURA:
    Cada concepto técnico complejo en BLOQUE_PANORAMA o BLOQUE_DESTACADO debe ir precedido de UNA analogía cotidiana en 1-2 frases.
    MAL: "Los embeddings son vectores en espacio de alta dimensión."
    BIEN: "Imagina que cada palabra es una posición en un mapa. Las palabras similares están cerca. Eso son los embeddings."
16. REGLA AUDIO — LONGITUD DE INTERVENCIÓN:
    Intervención de desarrollo: 60-120 palabras (4-6 frases) — zona óptima TTS a 1.32x velocidad.
    Máximo absoluto por intervención: 190 palabras. Si un concepto necesita más, pártelo en DOS bloques:
    el primero explica la primera parte (≤190 palabras), el otro speaker hace una pregunta breve,
    y el primero retoma con la segunda parte (≤190 palabras).
    Reacciones/preguntas: máximo 20 palabras (preferiblemente 8-15). NO usar interjecciones de validación.
17. REGLA AUDIO — NÚMEROS EN PALABRAS:
    TODOS los números van en palabras. El TTS a 1.32x pronuncia mal "3.7%" o "$3M".
    MAL: "el 3.7% de empresas", "costó $3M". BIEN: "el tres punto siete por ciento", "costó tres millones".
18. REGLA DE DIÁLOGO NATURAL — PROHIBICIONES:
    PROHIBIDO: enumeraciones "Primero... Segundo... Tercero... Cuarto..." en el turno de un solo speaker.
    Si necesitas listar 3+ puntos, distribúyelos entre los dos speakers o introduce reacciones entre ellos.
    PROHIBIDO: que un speaker se haga una pregunta y la responda él mismo en el turno siguiente.
    Si IAGO termina con una pregunta retórica, la respuesta la da MARIA (y viceversa).
    PROHIBIDO: intervenciones genéricas de relleno sin contenido específico del tema ("Bien apuntado,
    déjame añadir la perspectiva técnica...", "Hay algo que me genera curiosidad en este punto...").
    Excepción: años de papers donde el año es parte del nombre ("el informe McKinsey 2024").
18. REGLA TECNICISMO ACELERADO:
    Todo tecnicismo largo (>3 sílabas, inglés o compuesto) necesita frase introductoria previa.
    MAL: "backpropagation es el algoritmo..." BIEN: "El algoritmo clave, que llamamos backpropagation, es..."
19. REFERENCIAS TEMPORALES — REGLA DURA:
    Cuando hables del ESTADO ACTUAL, NO cites año: usa "hoy", "actualmente", "en este momento".
    Solo cita año pegado a publicación identificable por nombre propio.
    PROHIBIDO: "en 2024", "en 2025", "en dos mil veinticinco" como marcador del presente.
20. ANTIPINGPONG: nunca pongas 3 intervenciones del MISMO speaker seguidas. Intercala.
21. ANTIPINGPONG en detalle: Tras 2 bloques del MISMO speaker, el siguiente DEBE ser del otro. Revisa antes de finalizar que nunca hay 3 del mismo seguidos.
22. CIERRE_CONCEPTOS recuento: ANTES de escribirlo, cuenta: apertura (1 bloque) + conceptos (2-4 bloques) = 3-5 bloques TOTALES. Si escribes 5 conceptos → son 6 bloques totales = FAIL. Máximo 4 conceptos (4 + apertura = 5 bloques = VÁLIDO).
"""
    return system, user


_DIGIT_TO_WORD_ES = {
    "0": "cero", "1": "uno", "2": "dos", "3": "tres", "4": "cuatro",
    "5": "cinco", "6": "seis", "7": "siete", "8": "ocho", "9": "nueve",
    "10": "diez", "11": "once", "12": "doce", "13": "trece", "14": "catorce",
    "15": "quince", "16": "dieciséis", "17": "diecisiete", "18": "dieciocho",
    "19": "diecinueve", "20": "veinte", "30": "treinta", "40": "cuarenta",
    "50": "cincuenta", "60": "sesenta", "70": "setenta", "80": "ochenta",
    "90": "noventa", "100": "cien",
}

_DIGIT_NUMBER_PATTERNS = [
    # Porcentajes: "3.7%" → "tres punto siete por ciento"
    (re.compile(r"\b(\d+)[.,](\d+)\s*%"), lambda m: f"{_DIGIT_TO_WORD_ES.get(m.group(1), m.group(1))} punto {_DIGIT_TO_WORD_ES.get(m.group(2), m.group(2))} por ciento"),
    (re.compile(r"\b(\d+)\s*%"), lambda m: f"{_DIGIT_TO_WORD_ES.get(m.group(1), m.group(1))} por ciento"),
    # Cifras monetarias: "$3M" "$500K"
    (re.compile(r"\$\s*(\d+(?:[.,]\d+)?)\s*[Mm]"), lambda m: f"{_DIGIT_TO_WORD_ES.get(m.group(1).split('.')[0].split(',')[0], m.group(1))} millones de dólares"),
    (re.compile(r"\$\s*(\d+(?:[.,]\d+)?)\s*[Kk]"), lambda m: f"{_DIGIT_TO_WORD_ES.get(m.group(1).split('.')[0], m.group(1))} mil dólares"),
]


def _fix_digit_numbers_in_dialogue(script_text: str) -> str:
    """Convierte patrones de números en dígitos a palabras en las líneas de diálogo.

    Solo actúa sobre líneas que empiezan con IAGO: o MARIA: para no tocar
    headers, comentarios ni la sección VERIFICACIONES.
    """
    lines = script_text.split("\n")
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(IAGO|MARIA)\s*:", stripped, re.IGNORECASE):
            for pattern, replacer in _DIGIT_NUMBER_PATTERNS:
                line = pattern.sub(replacer, line)
        out.append(line)
    return "\n".join(out)


def _fix_antipingpong(script_text: str, spec: dict) -> str:
    """Inserta un bridge cuando hay 3+ bloques consecutivos del mismo speaker.

    Actúa en todos los runs de 3+, sin límite de inserciones, para eliminar
    el hard-fail de bloques consecutivos. Los bridges tienen 4+ frases y no
    contienen interjecciones de la blacklist.
    """
    rules = spec.get("script_rules", {})
    max_c = rules.get("max_consecutive_blocks_same_speaker", 2)
    speaker_pat = re.compile(r"^(IAGO|MARIA)\s*:", re.IGNORECASE)

    # Secciones donde NO insertamos bridges (estructura fija)
    _NO_BRIDGE_SECTIONS = {
        "HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
        "CIERRE_CONCEPTOS", "CIERRE_FINAL", "VERIFICACIONES",
    }

    lines = script_text.split("\n")

    # Construir mapa línea→sección
    section_map: dict[int, str] = {}
    current_section = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("# #"):
            current_section = stripped[2:].strip()
        section_map[i] = current_section

    speaker_lines: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        m = speaker_pat.match(stripped)
        if m and section_map.get(i, "") not in _NO_BRIDGE_SECTIONS:
            speaker_lines.append((i, m.group(1).upper()))

    # Encontrar posiciones donde hay que insertar (3er bloque consecutivo del mismo speaker)
    inserts: list[tuple[int, str]] = []  # (line_i, dominant_speaker)
    consec = 1
    for idx in range(1, len(speaker_lines)):
        prev_line_i, prev_speaker = speaker_lines[idx - 1]
        cur_line_i, cur_speaker = speaker_lines[idx]
        if cur_speaker == prev_speaker:
            consec += 1
            if consec > max_c:
                inserts.append((prev_line_i, prev_speaker))
        else:
            consec = 1

    if not inserts:
        return script_text

    # Bridges cortos (≤30 palabras → exentos del check min-frases con reaction_word_limit=30)
    BRIDGES_FROM_IAGO: list[str] = [
        "MARIA: [curioso] ¿Dónde suele aparecer el primer problema en producción?",
        "MARIA: [reflexivo] ¿Y si los datos de partida no están limpios?",
        "MARIA: [directo] ¿Cuánto tiempo lleva implementarlo correctamente?",
        "MARIA: [serio] ¿Hay casos donde este enfoque no escale bien?",
        "MARIA: [curioso] ¿Qué riesgo real implica ignorar ese punto?",
        "MARIA: [reflexivo] ¿Cómo lo validas antes de ponerlo en producción?",
        "MARIA: [directo] ¿Y en equipos sin experiencia técnica funciona igual?",
        "MARIA: [serio] ¿Dónde está el límite de este enfoque?",
    ]
    BRIDGES_FROM_MARIA: list[str] = [
        "IAGO: [reflexivo] Añadiría una dimensión técnica a ese punto.",
        "IAGO: [explicativo] Desde la arquitectura, eso tiene una consecuencia directa.",
        "IAGO: [directo] La escala cambia ese escenario por completo.",
        "IAGO: [serio] El sistema tiene que manejar eso explícitamente.",
        "IAGO: [reflexivo] En producción real, ese factor determina la arquitectura.",
        "IAGO: [explicativo] Hay un aspecto de rendimiento que completa ese cuadro.",
        "IAGO: [directo] El trade-off técnico aquí es latencia versus precisión.",
        "IAGO: [serio] Técnicamente, ese patrón tiene un coste que hay que gestionar.",
    ]

    result = list(lines)
    iago_bridge_idx = 0
    maria_bridge_idx = 0
    for line_i, dominant in sorted(inserts, key=lambda x: x[0], reverse=True):
        if dominant == "IAGO":
            bridge = BRIDGES_FROM_IAGO[iago_bridge_idx % len(BRIDGES_FROM_IAGO)]
            iago_bridge_idx += 1
        else:
            bridge = BRIDGES_FROM_MARIA[maria_bridge_idx % len(BRIDGES_FROM_MARIA)]
            maria_bridge_idx += 1
        result.insert(line_i + 1, bridge)

    return "\n".join(result)


def _trim_cierre_conceptos_if_excess(script_text: str, spec: dict) -> str:
    """Ajusta CIERRE_CONCEPTOS al número de bloques hablados permitido.

    M-type: máximo key_concepts_block_count_max (5). Elimina bloques del penúltimo.
    T-type: exactamente key_concepts_block_count_exact (3).
      Caso habitual: LLM genera 4 bloques [opener, concepto1, concepto2, concepto3].
      Si opener y concepto1 son del mismo speaker, los fusiona en uno solo → 3 bloques.
      Si no son del mismo speaker, elimina el penúltimo bloque → 3 bloques.
    """
    rules = spec["script_rules"]
    exact = rules.get("key_concepts_block_count_exact")
    max_c = rules.get("key_concepts_block_count_max", 5)
    target = exact if exact is not None else max_c

    lines = script_text.split("\n")
    speaker_pat = re.compile(r"^(IAGO|MARIA)\s*:", re.IGNORECASE)

    # Collect speaker line indices within CIERRE_CONCEPTOS
    speaker_idxs: list[int] = []
    in_cierre = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "# CIERRE_CONCEPTOS":
            in_cierre = True
            continue
        if in_cierre and stripped.startswith("# "):
            break
        if in_cierre and speaker_pat.match(stripped):
            speaker_idxs.append(i)

    count = len(speaker_idxs)
    if count <= target:
        return script_text  # ya dentro del rango

    # T-type: exact count via fusion or removal
    if exact is not None:
        result = list(lines)
        while True:
            # Recalcular índices en result actual
            cur_idxs: list[int] = []
            in_c = False
            for i, ln in enumerate(result):
                s = ln.strip()
                if s == "# CIERRE_CONCEPTOS":
                    in_c = True
                    continue
                if in_c and s.startswith("# "):
                    break
                if in_c and speaker_pat.match(s):
                    cur_idxs.append(i)

            if len(cur_idxs) <= exact:
                break

            idx0, idx1 = cur_idxs[0], cur_idxs[1]
            m0 = re.match(r"^(IAGO|MARIA)\s*:", result[idx0].strip(), re.IGNORECASE)
            m1 = re.match(r"^(IAGO|MARIA)\s*:", result[idx1].strip(), re.IGNORECASE)
            if m0 and m1 and m0.group(1).upper() == m1.group(1).upper():
                # Mismo speaker: fusionar opener en bloque siguiente
                opener_body = re.sub(
                    r"^(IAGO|MARIA)\s*:\s*(\[.*?\])?\s*", "", result[idx0], flags=re.IGNORECASE
                ).strip()
                result[idx1] = result[idx1].rstrip() + " " + opener_body
                result[idx0] = ""
            else:
                # Distinto speaker: eliminar penúltimo bloque
                result[cur_idxs[-2]] = ""

        return "\n".join(ln for ln in result if ln != "" or True).replace("\n\n\n", "\n\n")

    # M-type: eliminar bloques del penúltimo hacia el antepenúltimo
    excess = count - target
    to_remove = set(speaker_idxs[-(excess + 1):-1])
    out = [line for i, line in enumerate(lines) if i not in to_remove]
    return "\n".join(out)


def _rebalance_shared_block(script_text: str, spec: dict) -> str:
    """Rebalancea BLOQUE_DESTACADO (M) o BLOQUE_COMO (T) si un speaker supera el 60%.

    Estrategia mecánica: busca el bloque de desarrollo más largo del speaker dominante
    en la zona central del bloque compartido y cambia su etiqueta al speaker minoritario.
    No altera el contenido, solo el speaker. Itera hasta que ambos speakers estén en 40-60%.
    Máximo 3 iteraciones para evitar loops.
    """
    # Obtener secciones compartidas igual que validate_shared_block_balance
    shared_sections: list[str] = []
    for cfg in spec.get("speakers", {}).values():
        for section in cfg.get("shares_blocks", []):
            if section not in shared_sections:
                shared_sections.append(section)
    if not shared_sections:
        shared_sections = ["BLOQUE_DESTACADO"]
    lo, hi = 0.40, 0.60
    speaker_pat = re.compile(r"^(IAGO|MARIA)\s*:", re.IGNORECASE)

    lines = script_text.split("\n")
    # Construir mapa sección → lista de índices de bloques hablados
    current_section = ""
    line_sections: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("# #"):
            current_section = stripped[2:].strip()
        line_sections.append(current_section)

    for shared_section in shared_sections:
        for _iter in range(3):
            # Identificar bloques en esta sección
            block_indices = [
                i for i, line in enumerate(lines)
                if line_sections[i] == shared_section and speaker_pat.match(line.strip())
            ]
            if not block_indices:
                break

            # Calcular palabras por speaker
            words_by_speaker: dict[str, int] = {"IAGO": 0, "MARIA": 0}
            block_words: list[tuple[int, str, int]] = []  # (line_idx, speaker, word_count)
            for idx in block_indices:
                m = speaker_pat.match(lines[idx].strip())
                spk = m.group(1).upper() if m else "IAGO"
                body = re.sub(r"^(IAGO|MARIA)\s*:\s*(\[[^\]]+\])?\s*", "", lines[idx], flags=re.IGNORECASE)
                wc = len(body.split())
                words_by_speaker[spk] = words_by_speaker.get(spk, 0) + wc
                block_words.append((idx, spk, wc))

            total = sum(words_by_speaker.values())
            if total == 0:
                break

            iago_pct = words_by_speaker["IAGO"] / total

            if lo <= iago_pct <= hi:
                break  # En rango

            dominant = "IAGO" if iago_pct > hi else "MARIA"
            minority = "MARIA" if dominant == "IAGO" else "IAGO"

            # Bloques del speaker dominante (excluir primero y último)
            dom_blocks = [(idx, wc) for idx, spk, wc in block_words if spk == dominant]
            candidates = dom_blocks[1:-1] if len(dom_blocks) > 2 else dom_blocks
            if not candidates:
                break

            # Elegir el bloque central más largo del speaker dominante
            mid = len(candidates) // 2
            target_idx = min(
                candidates[max(0, mid - 1): mid + 2],
                key=lambda x: -x[1]
            )[0]

            # Cambiar el speaker de ese bloque
            old_line = lines[target_idx]
            new_line = re.sub(
                r"^(IAGO|MARIA)(\s*:)", minority + r"\2", old_line, count=1, flags=re.IGNORECASE
            )
            lines[target_idx] = new_line

    return "\n".join(lines)


def _inject_cta_if_missing(script_text: str, spec: dict) -> str:
    """Si CIERRE_FINAL no contiene la CTA obligatoria, la inyecta antes de la frase de cierre."""
    cta_marker = "los episodios del modulo ya estan disponibles"
    final_phrase = spec["script_rules"].get("final_closing_phrase", "")

    # Detectar si ya hay CTA (búsqueda normalizada)
    import unicodedata as _ud
    def _norm(s: str) -> str:
        return "".join(
            c for c in _ud.normalize("NFD", s.lower())
            if _ud.category(c) != "Mn"
        ).replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    if cta_marker in _norm(script_text):
        return script_text  # CTA ya presente

    # Buscar la línea que contiene la frase final para inyectar la CTA justo antes
    lines = script_text.split("\n")
    final_norm = _norm(final_phrase)
    cta_text = "Y si quieres profundizar en cualquiera de estos conceptos, los episodios del módulo ya están disponibles en nuestras plataformas habituales."

    for i, line in enumerate(lines):
        if final_phrase and final_norm and final_norm in _norm(line):
            # Inyectar CTA en la misma línea, antes de la frase final
            lines[i] = line.replace(final_phrase, cta_text + " " + final_phrase)
            return "\n".join(lines)

    return script_text  # No se encontró la frase final, no se modifica


# Bridges usados por _split_oversized_blocks.
# Bridges cortos (≤30 palabras → exentos del check min-frases con reaction_word_limit=30)
# Distintos de los de _fix_antipingpong para maximizar variedad en el guion.
_SPLIT_BRIDGES_FROM_IAGO = [
    "MARIA: [curioso] ¿Y qué pasa cuando ese supuesto no se cumple?",
    "MARIA: [reflexivo] ¿Cuál es el principal riesgo en ese punto?",
    "MARIA: [directo] ¿Cómo se mide eso en un sistema real?",
    "MARIA: [serio] ¿Hay alternativas más sencillas para equipos pequeños?",
    "MARIA: [curioso] ¿Cuándo deja de ser suficiente este enfoque?",
    "MARIA: [reflexivo] ¿Qué caso de uso lo justifica mejor?",
    "MARIA: [directo] ¿Existe alguna trampa habitual al implementarlo?",
    "MARIA: [serio] ¿Y si el volumen de datos es bajo al principio?",
]
_SPLIT_BRIDGES_FROM_MARIA = [
    "IAGO: [reflexivo] Hay un matiz técnico que conviene añadir.",
    "IAGO: [explicativo] Desde la implementación, ese punto tiene una capa más.",
    "IAGO: [directo] El rendimiento en producción depende de eso.",
    "IAGO: [serio] La arquitectura condiciona mucho cómo se gestiona eso.",
    "IAGO: [reflexivo] Técnicamente hay un caso límite que importa aquí.",
    "IAGO: [explicativo] Ese comportamiento cambia con la escala.",
    "IAGO: [directo] El sistema distribuido introduce un factor extra.",
    "IAGO: [serio] Vale la pena ver el impacto en latencia de eso.",
]

# Secciones donde NO se parte: el modelo ya controla la longitud allí
_NO_SPLIT_SECTIONS = {
    "HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
    "CIERRE_FINAL", "VERIFICACIONES",
}


def _split_oversized_blocks(script_text: str, max_words: int = 190, spec: dict | None = None) -> str:
    """Divide bloques con > max_words palabras insertando una pregunta puente.

    El TTS a 1.32× velocidad genera artefactos en intervenciones > 200 palabras.
    Busca el primer fin de frase entre la palabra 120 y 160 para partir ahí.
    Solo actúa en secciones de desarrollo (no en HOOK, SALUDO, CIERRE_FINAL…).
    Garantiza que la continuación no empiece con frase de la blacklist.
    """
    blacklist: list[str] = []
    if spec:
        blacklist = [
            normalize_text_for_match(p)
            for p in spec.get("script_rules", {}).get("blacklist_validation_interjections", [])
        ]

    lines = script_text.split("\n")
    result: list[str] = []
    speaker_pat = re.compile(r"^(IAGO|MARIA)\s*:\s*(\[[^\]]+\])?\s*(.*)", re.DOTALL)
    bridge_counter = 0
    skip_section = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            section_name = stripped[2:].strip()
            skip_section = section_name in _NO_SPLIT_SECTIONS
            result.append(line)
            continue

        if skip_section:
            result.append(line)
            continue

        m = speaker_pat.match(stripped)
        if not m:
            result.append(line)
            continue

        speaker = m.group(1).upper()
        tag = (m.group(2) or "").strip()
        text = m.group(3).strip()
        words = text.split()

        if len(words) <= max_words:
            result.append(line)
            continue

        # Buscar fin de frase entre palabra 120 y 160, evitando que la
        # continuación empiece con una frase de la blacklist.
        search_start = min(120, max(0, len(words) - 30))
        search_end = min(160, len(words) - 5)

        split_pos = len(words) * 2 // 3  # fallback
        for i in range(search_start, search_end):
            if words[i].endswith((".", "?", "!")):
                candidate_start = " ".join(words[i + 1:i + 4]).lower() if i + 1 < len(words) else ""
                # Rechazar si el inicio de la continuación es una frase blacklisted
                starts_blacklisted = any(
                    candidate_start.startswith(bl) for bl in blacklist
                )
                if not starts_blacklisted:
                    split_pos = i + 1
                    break

        first_text = " ".join(words[:split_pos])
        second_text = " ".join(words[split_pos:])
        bridges = _SPLIT_BRIDGES_FROM_IAGO if speaker == "IAGO" else _SPLIT_BRIDGES_FROM_MARIA
        bridge = bridges[bridge_counter % len(bridges)]
        bridge_counter += 1

        # La continuación usa el mismo tag que el bloque original para coherencia
        cont_tag = tag if tag else "[directo]"
        prefix = f"{speaker}: {tag}" if tag else f"{speaker}:"
        result.append(f"{prefix} {first_text}")
        result.append(bridge)
        result.append(f"{speaker}: {cont_tag} {second_text}")

    return "\n".join(result)


def _split_oversized_sentence_blocks(script_text: str, max_sentences: int = 10, spec: dict | None = None) -> str:
    """Divide bloques con > max_sentences frases en dos mitades, insertando un puente.

    El validador emite soft-warn para bloques con más de max_sentences frases.
    Esta función los parte en la frase N//2 para eliminar el warn.
    Solo actúa fuera de HOOK/INTRO/SALUDO/CIERRE_FINAL/VERIFICACIONES.
    """
    if spec:
        max_sentences = spec.get("script_rules", {}).get("maximum_sentences_per_intervention", max_sentences)
    lines = script_text.split("\n")
    result: list[str] = []
    speaker_pat = re.compile(r"^(IAGO|MARIA)\s*:\s*(\[[^\]]+\])?\s*(.*)", re.DOTALL)
    bridge_counter = 0
    skip_section = False

    # Sentence boundary: ends with .!? not preceded by digit (decimal) or single letter (abbrev)
    sent_end_pat = re.compile(r"[.!?]+\s+")

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            section_name = stripped[2:].strip()
            skip_section = section_name in _NO_SPLIT_SECTIONS
            result.append(line)
            continue

        if skip_section:
            result.append(line)
            continue

        m = speaker_pat.match(stripped)
        if not m:
            result.append(line)
            continue

        speaker = m.group(1).upper()
        tag = (m.group(2) or "").strip()
        text = m.group(3).strip()

        # Count sentences
        sentences = [s.strip() for s in sent_end_pat.split(text) if s.strip()]
        # Handle last sentence (no trailing space after sentence end)
        if text and text[-1] in ".!?":
            pass  # already split correctly
        else:
            # Merge the last partial segment (no sentence-ending punctuation)
            pass

        if len(sentences) <= max_sentences:
            result.append(line)
            continue

        # Split at the midpoint
        mid = len(sentences) // 2
        # Reconstruct first and second halves from original text
        # Find split position in original text by finding end of mid-th sentence
        pos = 0
        for _i in range(mid):
            m_end = sent_end_pat.search(text, pos)
            if m_end:
                pos = m_end.end()
            else:
                pos = len(text)
                break

        first_text = text[:pos].strip()
        second_text = text[pos:].strip()

        if not second_text:
            result.append(line)
            continue

        bridges = _SPLIT_BRIDGES_FROM_IAGO if speaker == "IAGO" else _SPLIT_BRIDGES_FROM_MARIA
        bridge = bridges[bridge_counter % len(bridges)]
        bridge_counter += 1

        cont_tag = tag if tag else "[directo]"
        prefix = f"{speaker}: {tag}" if tag else f"{speaker}:"
        result.append(f"{prefix} {first_text}")
        result.append(bridge)
        result.append(f"{speaker}: {cont_tag} {second_text}")

    return "\n".join(result)


def _fix_tts_closing_tags(content: str) -> str:
    """Reemplaza tags de cierre erroneos (</iago>, </maria>) por el tag de apertura correcto."""
    open_match = re.search(r"<([a-zA-Z_]+)>", content)
    if open_match:
        tag = open_match.group(1).lower()
        content = re.sub(r"</(iago|maria|yago|IAGO|MARIA|YAGO)>", f"</{tag}>", content, flags=re.IGNORECASE)
    return content


_TAG_REMAP = {
    "curiosa": "curioso", "esceptica": "esceptico", "ironica": "ironico",
    "didactica": "didactico", "explicativa": "explicativo", "directa": "directo",
    "seria": "serio", "firme": "firme", "contundenta": "contundente",
    "reflexiva": "reflexivo", "natural": "natural", "pausada": "pausado",
    "calida": "calido", "clara": "claro", "analitico": "analitica",
    "tensa": "tenso", "tecnico": "explicativo", "tecnica": "explicativo",
}


def _fix_gendered_tags(content: str) -> str:
    """Remapea variantes de genero de tags TTS a la forma canonica del spec.
    Soporta formato [tag] (T-type) y <tag></tag> (M-type).
    """
    def _remap_sq(m: re.Match) -> str:          # [tag]
        canonical = _TAG_REMAP.get(m.group(1).lower(), m.group(1).lower())
        return f"[{canonical}]"

    def _remap_ang(m: re.Match) -> str:          # <tag> o </tag>
        slash = m.group(1) or ""
        canonical = _TAG_REMAP.get(m.group(2).lower(), m.group(2).lower())
        return f"<{slash}{canonical}>"

    content = re.sub(r"\[([a-zA-Z_]+)\]", _remap_sq, content)
    content = re.sub(r"<(/?)([a-zA-Z_]+)>", _remap_ang, content)
    return content


def _remove_blacklisted_opening(content: str, spec: dict) -> str:
    """Elimina interjecciones prohibidas.
    - Si el bloque empieza con [tag] + interjeccion → elimina la interjeccion.
    - Si el bloque es corto (≤ reaction_word_limit) → elimina la interjeccion de cualquier posicion.
    """
    rules = spec.get("script_rules", {})
    blacklist = rules.get("blacklist_validation_interjections") or rules.get("blacklisted_interjections") or []
    short_limit = rules.get("reaction_word_limit", 12)

    # Calcular palabra count sin tag
    plain = re.sub(r"^\[[^\]]+\]\s*", "", content.strip())
    word_count = len(plain.split())
    is_short = word_count <= short_limit

    LEADING_TAG = r"(?:(\[[^\]]+\])\s*)?"
    for phrase in blacklist:
        # Caso 1: al inicio del bloque (con o sin tag previo)
        pat_start = re.compile(
            r"^" + LEADING_TAG + re.escape(phrase) + r"[.,!]?\s*",
            re.IGNORECASE,
        )
        content = pat_start.sub(r"\1 ", content).strip()

        # Caso 2: en bloque corto, en cualquier posicion
        if is_short:
            pat_any = re.compile(r"\b" + re.escape(phrase) + r"\b[.,!]?\s*", re.IGNORECASE)
            content = pat_any.sub("", content).strip()

    return content


def normalize_generated_script(script_text: str, spec: dict) -> str:
    """Normaliza speaker names, elimina 'Iago', corrige tags TTS y quita interjecciones."""
    SPEAKER_PAT = re.compile(r"^(IAGO|MARIA|MARÍA)\s*:\s*(.*)$", re.IGNORECASE)
    lines = script_text.replace("\r\n", "\n").split("\n")
    normalized: list[str] = []
    for line in lines:
        raw = line.rstrip()
        stripped = raw.strip()
        m = SPEAKER_PAT.match(stripped)
        if m:
            speaker  = m.group(1).upper().replace("Í", "I")
            content  = m.group(2).strip()
            content  = re.sub(r"\bIago\b", "Yago", content, flags=re.IGNORECASE)
            content  = _fix_tts_closing_tags(content)
            content  = _fix_gendered_tags(content)
            content  = _remove_blacklisted_opening(content, spec)
            normalized.append(f"{speaker}: {content}")
        else:
            normalized.append(stripped)
    cleaned = "\n".join(normalized)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def strip_verification_block(text: str) -> str:
    return re.sub(r"\n# VERIFICACIONES[\s\S]*$", "", text.strip(), flags=re.MULTILINE).strip()


def enforce_fixed_phrases(text: str, spec: dict) -> str:
    """Inyecta frases fijas del spec si el modelo no las incluyo exactamente.

    Opera sobre el cuerpo del guion (sin bloque de verificaciones).
    Preserva la etiqueta TTS del bloque si existe.
    """
    from podcast_spec import extract_leading_tag, normalize_text_for_match

    rules = spec["script_rules"]
    SPEAKER_RE = re.compile(r"^(IAGO|MARIA)\s*:\s*(.*)$", re.IGNORECASE | re.MULTILINE)

    def _inject_into_section(
        body: str,
        section_marker: str,
        phrase: str,
        position: str,  # "first_block" | "last_block"
    ) -> str:
        """Sustituye el bloque objetivo de la sección con la frase fija si no está."""
        norm_phrase = normalize_text_for_match(phrase)
        if norm_phrase in normalize_text_for_match(body):
            return body  # ya está, nada que hacer

        lines = body.split("\n")
        sec_idx = None
        for i, ln in enumerate(lines):
            if ln.strip().upper() == f"# {section_marker}":
                sec_idx = i
                break
        if sec_idx is None:
            return body  # sección no encontrada

        # Encontrar bloques hablados en la sección
        next_sec_idx = len(lines)
        for i in range(sec_idx + 1, len(lines)):
            if lines[i].strip().startswith("# ") and not lines[i].strip().startswith("## "):
                next_sec_idx = i
                break

        block_indices = [
            i for i in range(sec_idx + 1, next_sec_idx)
            if SPEAKER_RE.match(lines[i].strip())
        ]
        if not block_indices:
            return body

        target_idx = block_indices[0] if position == "first_block" else block_indices[-1]
        target_line = lines[target_idx].strip()
        m = SPEAKER_RE.match(target_line)
        if not m:
            return body

        speaker = m.group(1).upper()
        content = m.group(2).strip()
        tag = extract_leading_tag(content)

        if position == "last_block":
            # Reemplazar contenido completo del bloque con la frase fija
            new_content = f"[calido]{phrase}" if not tag else f"[{tag}]{phrase}"
            lines[target_idx] = f"{speaker}: {new_content}"
        else:
            # Prefijar la frase al bloque (para conceptos_closing)
            plain = remove_leading_tag(content)
            new_content = f"[{tag}]{phrase} {plain}" if tag else f"{phrase} {plain}"
            lines[target_idx] = f"{speaker}: {new_content}"

        return "\n".join(lines)

    # ── final_closing_phrase → último bloque de CIERRE_FINAL ─────────────────
    if rules.get("final_closing_phrase"):
        text = _inject_into_section(text, "CIERRE_FINAL", rules["final_closing_phrase"], "last_block")

    # ── concepts_closing_phrase → primer bloque de CIERRE_CONCEPTOS ──────────
    if rules.get("concepts_closing_phrase"):
        text = _inject_into_section(text, "CIERRE_CONCEPTOS", rules["concepts_closing_phrase"], "first_block")

    # ── hook_closing_phrase → último bloque de HOOK ───────────────────────────
    if rules.get("hook_closing_phrase"):
        text = _inject_into_section(text, "HOOK", rules["hook_closing_phrase"], "last_block")

    return text


# ---------------------------------------------------------------------------
# Sección de verificaciones
# ---------------------------------------------------------------------------

def build_verification_section(
    script_body: str,
    spec: dict,
    concept_list: list[str],
    usage: TokenUsage,
    ficha: dict,
) -> str:
    stats = build_script_stats(script_body, spec, concept_list)
    rules = spec["script_rules"]
    coverage_hits = [c for c, m in stats["concept_mentions"].items() if m >= 1]
    coverage_pct  = int(round(len(coverage_hits) / max(len(concept_list), 1) * 100))

    lines = [
        "# VERIFICACIONES",
        "##",
        f"## PALABRAS TOTALES : {stats['word_count_total']} "
        f"(objetivo: {rules['minimum_word_count']}-{rules['maximum_word_count']})",
        f"## MEDIA PALABRAS/INTERVENCION : {stats['avg_words_per_intervention']:.1f}",
        "##",
        "## COBERTURA DE CONCEPTOS DEL PDF:",
    ]
    for concept in concept_list:
        mentions = stats["concept_mentions"].get(concept, 0)
        marker = "[OK]" if mentions >= 1 else "[--]"
        lines.append(f"## {marker} {concept}: {mentions} menciones")
    lines.append(f"## Cobertura total: {coverage_pct}% (objetivo: {rules.get('minimum_pdf_coverage_percent', 75)}%)")
    lines.extend([
        "##",
        "## APLICACION_PRACTICA:",
        f"## Parrafos encontrados en docs vivos: {ficha.get('paragraphs_found', 0)}",
        f"## Por documento: {ficha.get('hits_by_doc', {})}",
        "##",
        "## TOKENS ANTHROPIC:",
        f"## input_tokens: {usage.input_tokens}",
        f"## output_tokens: {usage.output_tokens}",
        f"## cache_read: {usage.cache_read}",
        f"## total: {usage.total}",
    ])
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Inferencia del nombre del módulo desde el PDF
# ---------------------------------------------------------------------------

def infer_module_name(pdf_path: Path) -> str:
    """Extrae nombre del módulo desde el nombre del PDF.

    RESUMEN_M0_Introduccion_Estrategica.pdf → Introduccion_Estrategica
    """
    stem = pdf_path.stem  # RESUMEN_M0_Introduccion_Estrategica
    name = re.sub(r"^RESUMEN_M\d+_", "", stem, flags=re.IGNORECASE)
    return name  # Introduccion_Estrategica (sin espacios, para el filename)


def infer_topic_display(pdf_path: Path) -> str:
    """Nombre legible del módulo para el prompt."""
    return infer_module_name(pdf_path).replace("_", " ")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de guiones M — MaquinarIA Pesada")
    parser.add_argument("--modulo",  type=int,  required=True,  help="Número de módulo (0-14)")
    parser.add_argument("--pdf",     required=True, help="Ruta al PDF RESUMEN del módulo")
    parser.add_argument("--nombre",  default=None,  help="Nombre del módulo para el archivo (ej: Ingenieria_de_Prompts). Opcional.")
    parser.add_argument("--spec",    default=str(SPEC_PATH), help="Ruta a PODCAST_M_SPEC.md")
    parser.add_argument("--max-intentos", type=int, default=3, help="Intentos si falla la validación")
    args = parser.parse_args()

    # ── Cargar spec ─────────────────────────────────────────────────────────
    spec          = load_spec(args.spec)
    spec_markdown = read_text(Path(args.spec))

    # ── PDF ──────────────────────────────────────────────────────────────────
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        # Intentar relativo a BASE_DIR
        pdf_path = BASE_DIR / args.pdf
    pdf_text = extract_pdf_text(pdf_path)
    topic    = infer_topic_display(pdf_path)
    modulo_n = args.modulo

    # ── Nombre de archivo de salida ──────────────────────────────────────────
    module_name = args.nombre or infer_module_name(pdf_path)
    guion_filename = f"M{modulo_n}_{module_name}.txt"
    guion_path     = BASE_DIR / spec["directories"]["scripts_dir"] / guion_filename
    ep_code        = guion_to_ep_code(Path(guion_filename).stem)

    print(f"\n{'='*60}")
    print("  GENERADOR GUION M — MaquinarIA Pesada")
    print(f"  Módulo   : M{modulo_n} — {topic}")
    print(f"  PDF      : {pdf_path.name}")
    print(f"  Salida   : {guion_path.name}")
    print(f"  ep_code  : {ep_code}")
    print(f"{'='*60}\n")

    # ── Cliente Anthropic ────────────────────────────────────────────────────
    client = make_anthropic_client()
    usage  = TokenUsage()

    # ── Extracción de conceptos ──────────────────────────────────────────────
    print("  [1/4] Extrayendo conceptos del PDF...")
    concept_list, hard_audio = extract_concepts_with_claude(client, spec, pdf_text, topic, usage)
    if not concept_list:
        concept_list = extract_theme_concepts(pdf_text, limit=8)
    print(f"         Conceptos: {concept_list[:5]}...")

    # ── Documentos vivos ─────────────────────────────────────────────────────
    print("  [2/4] Cargando documentos vivos y extrayendo APLICACION_PRACTICA...")
    live_docs = load_live_docs(BASE_DIR)
    ficha     = extract_aplicacion_material(live_docs, modulo_n, concept_list, spec)
    artifact  = save_aplicacion_artifact(ficha, modulo_n, BASE_DIR)
    print(f"         Párrafos encontrados: {ficha['paragraphs_found']} | Artifact: {artifact.name}")

    if not ficha["paragraphs_sufficient"]:
        print(
            "\n[WARN] Material insuficiente para APLICACION_PRACTICA "
            f"(M{modulo_n}): solo {ficha['paragraphs_found']} párrafos encontrados.\n"
            "  El generador continuará pero el bloque puede ser débil.\n"
            f"  Considera enriquecer los docs vivos o crear PDFs/aplicacion_practica/M{modulo_n}.md"
        )

    # ── Apertura del episodio ────────────────────────────────────────────────
    opener = opening_speaker(ep_code, spec)

    # ── Generación ───────────────────────────────────────────────────────────
    gen_model = spec["anthropic"]["default_generation_model"]
    max_tokens = spec["anthropic"]["max_output_tokens"]
    temperature = spec["anthropic"]["temperature"]

    system_prompt, user_prompt = build_generation_prompt(
        spec, spec_markdown, modulo_n, topic, pdf_text,
        opener, concept_list, ficha, hard_audio,
    )

    local_issues: list[str] = []
    draft = ""
    best_draft = ""
    best_issues: list[str] = []
    best_score: tuple[int, int, int] = (999, 999, 999)  # (hard_count, word_deficit, soft_count)

    for attempt in range(1, args.max_intentos + 1):
        print(f"\n  [3/4] Generando guion (intento {attempt}/{args.max_intentos})...")

        # Use best_issues for feedback (not necessarily last attempt's issues)
        feedback_issues = best_issues if best_issues else local_issues
        if attempt > 1 and feedback_issues:
            hard_issues = [i for i in feedback_issues if not i.startswith("[WARN]")]
            soft_issues_retry = [i for i in feedback_issues if i.startswith("[WARN]")]
            if hard_issues:
                # Feedback específico para word count bajo y bloques cortos
                feedback_parts = []
                has_word_count_fail = False
                for issue in hard_issues:
                    wc_m = re.search(r"tiene (\d+) palabras \(minimo: (\d+)\)", issue)
                    if wc_m:
                        has_word_count_fail = True
                        actual, needed = int(wc_m.group(1)), int(wc_m.group(2))
                        diff = needed - actual
                        # Find specific short blocks to call out (all sections)
                        short_block_msgs = [
                            s for s in soft_issues_retry
                            if re.search(r"solo [123] frase", s)
                        ]
                        short_hint = ""
                        if short_block_msgs:
                            short_hint = (
                                " Bloques con pocas frases que DEBES ampliar a 4-6: "
                                + "; ".join(short_block_msgs[:4])
                                + "."
                            )
                        feedback_parts.append(
                            f"- {issue}\n"
                            f"  ACCIÓN REQUERIDA: añade {diff} palabras más."
                            f"{short_hint} "
                            f"Cada bloque de desarrollo debe tener MÍNIMO 4 frases (70-100 palabras). "
                            f"NO recortes nada, solo AÑADE contenido."
                        )
                    elif "BLOQUE_DESTACADO" in issue or "BLOQUE_COMO" in issue:
                        feedback_parts.append(
                            f"- {issue}\n"
                            f"  ACCIÓN: el speaker minoritario DEBE tener 2+ bloques de desarrollo "
                            f"de 4-6 frases cada uno. Redistribuye los conceptos."
                        )
                    else:
                        feedback_parts.append(f"- {issue}")
                # Always include soft warns about short blocks (≤3 frases) in feedback
                short_soft = [s for s in soft_issues_retry if re.search(r"solo [123] frase", s)]
                if short_soft and not has_word_count_fail:
                    for s in short_soft[:4]:
                        feedback_parts.append(
                            f"- {s}\n"
                            f"  ACCIÓN: amplía ese bloque a mínimo 4 frases completas (70-100 palabras)."
                        )
                # Include enumerated list warns in feedback
                enum_soft = [s for s in soft_issues_retry if "lista enumerada" in s]
                for s in enum_soft[:3]:
                    if has_word_count_fail:
                        feedback_parts.append(
                            f"- {s}\n"
                            f"  ACCIÓN: Convierte cada lista (Primero/Segundo/Tercero) en diálogo extendido: "
                            f"IAGO explica el punto 1 en 3-4 frases → MARIA reacciona con 3-4 frases → "
                            f"IAGO explica el punto 2 en 3-4 frases → MARIA elabora con 3-4 frases. "
                            f"Esto añade palabras Y elimina la lista. NO uses 'Primero/Segundo/Tercero'."
                        )
                    else:
                        feedback_parts.append(
                            f"- {s}\n"
                            f"  ACCIÓN: NO uses Primero/Segundo/Tercero en un mismo turno. "
                            f"Distribuye los puntos: IAGO explica uno, MARIA reacciona, IAGO continúa."
                        )
                user_prompt_ext = (
                    user_prompt
                    + "\n\nFEEDBACK OBLIGATORIO DEL INTENTO ANTERIOR (corrige todos estos puntos):\n"
                    + "\n".join(feedback_parts)
                )
            else:
                user_prompt_ext = user_prompt
        else:
            user_prompt_ext = user_prompt

        text, resp = call_claude(
            client, gen_model,
            system_prompt, user_prompt_ext,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        usage.add(resp)
        draft = normalize_generated_script(strip_verification_block(text), spec)
        draft = enforce_fixed_phrases(draft, spec)
        draft = _fix_digit_numbers_in_dialogue(draft)
        draft = _inject_cta_if_missing(draft, spec)
        draft = _trim_cierre_conceptos_if_excess(draft, spec)
        draft = _rebalance_shared_block(draft, spec)
        draft = _fix_antipingpong(draft, spec)
        draft = _split_oversized_blocks(draft, spec=spec)
        draft = _split_oversized_sentence_blocks(draft, spec=spec)

        # ── Validación ───────────────────────────────────────────────────────
        verification = build_verification_section(draft, spec, concept_list, usage, ficha)
        draft_with_ver = draft.rstrip() + "\n\n" + verification

        local_issues = validate_script_text(draft_with_ver, ep_code, spec, concept_list, base_dir=BASE_DIR)
        hard_issues  = [i for i in local_issues if not i.startswith("[WARN]")]
        soft_issues  = [i for i in local_issues if i.startswith("[WARN]")]

        # Tratar el exceso de palabras y la falta de CTA como hard en el retry
        word_count_issues = [i for i in soft_issues if "maximo recomendado" in i and "palabras" in i]
        cta_issues = [i for i in soft_issues if "CTA" in i]
        # Normalizar: quitar prefijo [WARN] de los issues que promocionamos a hard
        promoted = [i.removeprefix("[WARN] ") for i in word_count_issues + cta_issues]
        if promoted:
            hard_issues = hard_issues + promoted

        print(f"         Issues hard: {len(hard_issues)} | soft: {len(soft_issues)}")
        for issue in hard_issues:
            print(f"         [HARD] {issue}")
        for issue in soft_issues:
            print(f"         [WARN] {issue}")

        # Track best attempt by (hard_count, word_deficit, soft_count)
        wc_issue = next((i for i in hard_issues if "palabras (minimo:" in i), None)
        word_deficit = 0
        if wc_issue:
            m_wc = re.search(r"tiene (\d+) palabras \(minimo: (\d+)\)", wc_issue)
            if m_wc:
                word_deficit = max(0, int(m_wc.group(2)) - int(m_wc.group(1)))
        score = (len(hard_issues), word_deficit, len(soft_issues))
        if score < best_score:
            best_score = score
            best_draft = draft_with_ver
            best_issues = local_issues[:]

        if not hard_issues:
            draft = draft_with_ver
            print("         [PASS] Validacion OK")
            break

        if attempt == args.max_intentos:
            print(f"\n  [WARN] Superado máximo de intentos. Guardando mejor intento ({best_score[0]} hard, {best_score[2]} soft).")
            draft = best_draft

    # ── Guardar ──────────────────────────────────────────────────────────────
    print("\n  [4/4] Guardando guion...")
    guion_path.parent.mkdir(parents=True, exist_ok=True)
    guion_path.write_text(draft.rstrip() + "\n", encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  GUION GENERADO : {guion_path}")
    print(f"  ep_code        : {ep_code}")
    print(f"  Tokens         : {usage.report()}")
    if local_issues:
        hard_issues = [i for i in local_issues if not i.startswith("[WARN]")]
        soft_issues = [i for i in local_issues if i.startswith("[WARN]")]
        if hard_issues:
            print(f"  Issues hard    : {len(hard_issues)}")
        if soft_issues:
            print(f"  Issues soft    : {len(soft_issues)}")
    else:
        print("  Validacion     : PASS")
    print(f"{'='*60}\n")

    # Resumen de estado del proyecto
    try:
        from estado_proyecto import print_estado_resumen
        print_estado_resumen()
    except Exception:
        pass

    hard_issues = [i for i in local_issues if not i.startswith("[WARN]")]
    if hard_issues:
        raise SystemExit(
            f"Guion generado con {len(hard_issues)} issue(s) hard. "
            "Revisa el archivo antes de generar audio."
        )


if __name__ == "__main__":
    main()

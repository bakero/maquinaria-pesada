#!/usr/bin/env python3
# ruff: noqa
"""
generar_guion.py — Generador de guiones M (Módulo) para MaquinarIA Pesada.

🚫 SCRIPT LEGACY — RETIRADO 2026-05-19.
   Reemplazado por `lanzar_produccion_v6.py --tipo M` que usa el paquete
   `generadores/m_generator.py` + `validators/m_validator.py`. Ver
   `GENERACION.md` para el mapa canónico.
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.stderr.write(
        "\n❌ generar_guion.py está retirado (era v5).\n"
        "   Usa el pipeline canónico:\n"
        "       python lanzar_produccion_v6.py --kind M --ep M<N>\n"
        "   Ver GENERACION.md para el mapa completo.\n\n"
    )
    raise SystemExit(2)

# ---- Código histórico inaccesible ----------------------------------------
# Mantenido temporalmente para que `import generar_guion` siga resolviendo
# en docs/auditorías legacy. Se elimina entero en un PR de limpieza dedicado.
# --------------------------------------------------------------------------

import argparse
import json
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR  = Path(__file__).parent
SPEC_PATH = BASE_DIR / "PODCAST_M_SPEC.md"

sys.path.insert(0, str(BASE_DIR))
# Núcleo compartido de generación (ver guion_common.py y GENERACION.md).
from guion_common import (
    TokenUsage,
    _fix_antipingpong,
    _fix_digit_numbers_in_dialogue,
    _inject_cta_if_missing,
    _rebalance_shared_block,
    _soften_inline_enumerations,
    _split_oversized_blocks,
    _split_oversized_sentence_blocks,
    _trim_cierre_conceptos_if_excess,
    call_claude,
    enforce_fixed_phrases,
    extract_pdf_text,
    make_anthropic_client,
    normalize_generated_script,
    strip_verification_block,
)
from podcast_spec import (
    build_script_stats,
    compute_glossary_coverage,
    extract_theme_concepts,
    glossary_concepts_for_sources,
    guion_to_ep_code,
    load_spec,
    normalize_text_for_match,
    opening_speaker,
    parse_glossary,
    read_text,
    source_code_from_pdf_path,
    validate_script_text,
)

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
    glossary_concepts: list[str] | None = None,
) -> tuple[str, str]:
    """Construye system + user para la generación del guion M."""
    glossary_concepts = glossary_concepts or []

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

CONCEPTOS DEL GLOSARIO UNIFICADO ASOCIADOS A ESTA FUENTE
(son los términos canónicos del corpus presentes en el PDF fuente; intégralos de
forma natural en el guion con su definición canónica — el validador medirá qué
porcentaje aparece realmente, objetivo >= 75%):
{json.dumps(glossary_concepts, ensure_ascii=False)}

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
    OBJETIVO DE DIÁLOGO: apunta a {rules['minimum_word_count']+300} palabras de diálogo (margen de seguridad frente al mínimo total).
    CONTROL EN TIEMPO REAL — DOS CHECKPOINTS OBLIGATORIOS:
    1. Al terminar BLOQUE_PANORAMA: debes llevar al menos {rules['minimum_word_count']-700} palabras. Si no, añade 1-2 bloques IAGO más.
    2. Al terminar BLOQUE_DESTACADO: debes llevar al menos {rules['minimum_word_count']-300} palabras. Si no, añade un sub-bloque completo (4-6 frases, 70-100 palabras) antes de continuar.
    Si al llegar a APLICACION_PRACTICA llevas menos de {rules['minimum_word_count']-200} palabras, AÑADE un bloque extra completo antes de continuar.
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


# ---------------------------------------------------------------------------
# Sección de verificaciones
# ---------------------------------------------------------------------------

def build_verification_section(
    script_body: str,
    spec: dict,
    concept_list: list[str],
    usage: TokenUsage,
    ficha: dict,
    glossary_concepts: list[str] | None = None,
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

    # Cobertura de conceptos del glosario unificado asociados a la fuente.
    if glossary_concepts:
        gloss = compute_glossary_coverage(script_body, glossary_concepts)
        lines.extend([
            "##",
            "## COBERTURA DE CONCEPTOS DEL GLOSARIO UNIFICADO:",
            f"## Conceptos del glosario en la fuente: {gloss['total']}",
            f"## Cubiertos en el guion: {len(gloss['covered'])}",
            f"## Cobertura glosario: {gloss['coverage_pct']}%",
        ])
        if gloss["missing"]:
            lines.append(f"## Sin mencionar: {', '.join(gloss['missing'][:10])}")

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
    from cockpit.core.log_helpers import get_run_logger
    log = get_run_logger("generar_guion")

    parser = argparse.ArgumentParser(description="Generador de guiones M — MaquinarIA Pesada")
    parser.add_argument("--modulo",  type=int,  required=True,  help="Número de módulo (0-14)")
    parser.add_argument("--pdf",     required=True, help="Ruta al PDF RESUMEN del módulo")
    parser.add_argument("--nombre",  default=None,  help="Nombre del módulo para el archivo (ej: Ingenieria_de_Prompts). Opcional.")
    parser.add_argument("--spec",    default=str(SPEC_PATH), help="Ruta a PODCAST_M_SPEC.md")
    parser.add_argument("--max-intentos", type=int, default=3, help="Intentos si falla la validación")
    args = parser.parse_args()

    # ── Cargar spec ─────────────────────────────────────────────────────────
    log.step("load_spec", spec=args.spec)
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
    log.step("extract_concepts", pdf=str(pdf_path), topic=topic, modulo=modulo_n)
    print("  [1/4] Extrayendo conceptos del PDF...")
    concept_list, hard_audio = extract_concepts_with_claude(client, spec, pdf_text, topic, usage)
    if not concept_list:
        concept_list = extract_theme_concepts(pdf_text, limit=8)
    print(f"         Conceptos: {concept_list[:5]}...")

    # ── Conceptos del glosario unificado asociados a la fuente ───────────────
    source_code = source_code_from_pdf_path(pdf_path)
    glossary_concepts: list[str] = []
    if source_code:
        # El PDF fuente es el RESUMEN del módulo; si no hubiera conceptos
        # etiquetados con MX_RESUMEN, se cae a todos los del módulo (MX y MX_TY).
        glossary_path = BASE_DIR / "PDFs" / "auxiliares" / "glosario_unificado.md"
        glossary_concepts = glossary_concepts_for_sources(source_code, path=glossary_path)
        if not glossary_concepts and "_RESUMEN" in source_code:
            mod_prefix = source_code.split("_")[0]  # "M3"
            full = parse_glossary(glossary_path)
            glossary_concepts = [
                term for term, codes in full.items()
                if any(c == mod_prefix or c.startswith(mod_prefix + "_") for c in codes)
            ]
        print(f"         Glosario ({source_code}): {len(glossary_concepts)} conceptos")

    # ── Documentos vivos ─────────────────────────────────────────────────────
    log.step("load_live_docs")
    print("  [2/4] Cargando documentos vivos y extrayendo APLICACION_PRACTICA...")
    live_docs = load_live_docs(BASE_DIR)
    ficha     = extract_aplicacion_material(live_docs, modulo_n, concept_list, spec)
    artifact  = save_aplicacion_artifact(ficha, modulo_n, BASE_DIR)
    print(f"         Párrafos encontrados: {ficha['paragraphs_found']} | Artifact: {artifact.name}")
    log.info("APLICACION_PRACTICA material",
             paragraphs=ficha["paragraphs_found"],
             sufficient=ficha["paragraphs_sufficient"])

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
        opener, concept_list, ficha, hard_audio, glossary_concepts,
    )

    local_issues: list[str] = []
    draft = ""
    best_draft = ""
    best_issues: list[str] = []
    best_score: tuple[int, int, int] = (999, 999, 999)  # (hard_count, word_deficit, soft_count)

    log.step("generate", model=gen_model, max_intentos=args.max_intentos)
    for attempt in range(1, args.max_intentos + 1):
        if attempt > 1:
            log.retry(attempt=attempt, reason="hard_fails",
                      previous_hard=len([i for i in best_issues if not i.startswith("[WARN]")]))
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
                    elif "consecutivos del mismo speaker" in issue:
                        feedback_parts.append(
                            f"- {issue}\n"
                            f"  ACCIÓN: NUNCA escribas 3 bloques seguidos del mismo speaker. "
                            f"Después de cada 2 bloques de IAGO, MARIA debe intervenir. "
                            f"Alterna obligatoriamente en toda la sección."
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
        draft = _soften_inline_enumerations(draft)
        draft = _inject_cta_if_missing(draft, spec)
        draft = _trim_cierre_conceptos_if_excess(draft, spec)
        draft = _rebalance_shared_block(draft, spec)
        draft = _split_oversized_blocks(draft, spec=spec)
        draft = _split_oversized_sentence_blocks(draft, spec=spec)
        draft = _fix_antipingpong(draft, spec)

        # ── Validación ───────────────────────────────────────────────────────
        verification = build_verification_section(
            draft, spec, concept_list, usage, ficha, glossary_concepts,
        )
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
        log.info("validate · intento", attempt=attempt,
                 hard=len(hard_issues), soft=len(soft_issues))
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

    # ── Validate (last) + Guardar ───────────────────────────────────────────
    log.step("validate")
    final_hard = [i for i in local_issues if not i.startswith("[WARN]")]
    final_soft = [i for i in local_issues if i.startswith("[WARN]")]
    log.info("validación final", hard=len(final_hard), soft=len(final_soft))

    log.step("save", path=str(guion_path))
    print("\n  [4/4] Guardando guion...")
    guion_path.parent.mkdir(parents=True, exist_ok=True)
    guion_path.write_text(draft.rstrip() + "\n", encoding="utf-8")
    if final_hard:
        log.warn("guion guardado con hard-fails", path=str(guion_path),
                 hard=len(final_hard), tokens_total=usage.total)
    else:
        log.ok("guion guardado", path=str(guion_path),
               tokens_total=usage.total)

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


# El bloque `if __name__ == "__main__"` original se ha movido al inicio del
# archivo (ver guard arriba). No se ejecutará por debajo del SystemExit.

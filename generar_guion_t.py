#!/usr/bin/env python3
"""
generar_guion_t.py — Generador de guiones T (Tema) para MaquinarIA Pesada.

Genera guiones de episodios T usando:
  - PDF del tema específico en PDFs/temas/M{n}_T{k}_*.pdf
  - claude-sonnet-4-5 para generación, claude-haiku para conceptos
  - Estructura: BLOQUE_PANORAMA / BLOQUE_COMO / BLOQUE_REALIDAD (v5)

Nomenclatura de salida:
  Guiones/M{n}_TX_{topic_name}.txt
  (ej: M1_TX_T11_limitaciones_llms.txt)

Uso:
  python generar_guion_t.py --pdf PDFs/temas/M1_T11_limitaciones_llms.pdf
  python generar_guion_t.py --pdf PDFs/temas/M7_T1_que_es_rag.pdf
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR  = Path(__file__).parent
SPEC_PATH = BASE_DIR / "PODCAST_T_SPEC.md"

sys.path.insert(0, str(BASE_DIR))
# Núcleo compartido de generación (ver guion_common.py y GENERACION.md).
from guion_common import (  # noqa: E402
    TokenUsage,
    _fix_antipingpong,
    _fix_digit_numbers_in_dialogue,
    _rebalance_shared_block,
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
from podcast_spec import (  # noqa: E402
    build_script_stats,
    extract_theme_concepts,
    guion_to_ep_code,
    load_spec,
    opening_speaker,
    read_text,
    validate_script_text,
)

# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------

def infer_topic_name_from_pdf(pdf_path: Path) -> str:
    """M1_T11_limitaciones_llms.pdf → T11_limitaciones_llms"""
    stem = pdf_path.stem  # M1_T11_limitaciones_llms
    # Remove M{n}_ prefix
    name = re.sub(r"^M\d+_", "", stem, flags=re.IGNORECASE)
    return name  # T11_limitaciones_llms


def infer_module_n(pdf_path: Path) -> int:
    """Extrae número de módulo del nombre del PDF."""
    m = re.match(r"M(\d+)_", pdf_path.name, re.IGNORECASE)
    if not m:
        raise ValueError(f"No se puede inferir módulo de: {pdf_path.name}")
    return int(m.group(1))


def infer_topic_display(pdf_path: Path) -> str:
    """M1_T11_limitaciones_llms.pdf → Limitaciones LLMs"""
    name = infer_topic_name_from_pdf(pdf_path)
    # Remove T{k}_ prefix if present
    clean = re.sub(r"^T\d+_", "", name, flags=re.IGNORECASE)
    return clean.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Extracción de conceptos
# ---------------------------------------------------------------------------

def extract_concepts_with_claude(
    client,
    spec: dict,
    pdf_text: str,
    topic: str,
    usage: TokenUsage,
) -> list[str]:
    model = spec["anthropic"]["default_concept_model"]
    system = "Extrae conceptos clave de un PDF técnico. Devuelve solo JSON válido."
    user = (
        f"TEMA: {topic}\n\nPDF:\n{pdf_text[:12000]}\n\n"
        "Devuelve JSON: {\"key_concepts\": [\"concepto1\", \"concepto2\"]}"
    )
    try:
        text, resp = call_claude(
            client, model, system, user, max_tokens=800, temperature=0.0,
            source="generar_guion_t.py",
        )
        usage.add(resp)
        data = json.loads(text)
        return [c.strip() for c in data.get("key_concepts", []) if c.strip()][:8]
    except Exception as e:
        print(f"[WARN] Extracción de conceptos fallida ({e}), usando heurística.")
        return extract_theme_concepts(pdf_text, limit=8)


# ---------------------------------------------------------------------------
# Generación del guion T
# ---------------------------------------------------------------------------

def build_generation_prompt(
    spec: dict,
    spec_markdown: str,
    modulo_n: int,
    topic_display: str,
    pdf_text: str,
    opener: str,
    concept_list: list[str],
) -> tuple[str, str]:
    """Construye system + user para el guion T."""

    # Asignación de roles por bloque según T-spec v5
    # Yago lidera BLOQUE_PANORAMA, compartido BLOQUE_COMO, Maria lidera BLOQUE_REALIDAD
    rules = spec["script_rules"]
    other = "MARIA" if opener == "IAGO" else "IAGO"

    # Carga fuente de casos empresariales verificados para BLOQUE_REALIDAD
    casos_path = BASE_DIR / "PDFs" / "auxiliares" / "casos_empresariales_ia.md"
    casos_text = ""
    if casos_path.exists():
        try:
            casos_text = casos_path.read_text(encoding="utf-8")[:6000]  # primeras 6K chars
        except Exception:
            casos_text = ""

    system = (
        "Eres el sistema de producción del podcast MaquinarIA Pesada. "
        "Generas guiones de episodios T (tema): formativos, técnicos y amenos. "
        "Audiencia principal: estudiantes del máster cursando este módulo. "
        "Sigues la especificación PODCAST_T_SPEC.md v5 al pie de la letra. "
        "Devuelves SOLO el guion. Sin explicaciones, sin markdown adicional. "
        "Todas las intervenciones empiezan por IAGO: o MARIA:. "
        "No incluyas la sección # VERIFICACIONES; el sistema la añade después."
    )

    user = f"""ESPECIFICACION (PODCAST_T_SPEC.md v5):
{spec_markdown}

PARÁMETROS DEL EPISODIO:
- Módulo: M{modulo_n}
- Tema: {topic_display}
- Hook abre: {opener} (paridad del TEMA)
- Duración objetivo: {spec['episode_defaults']['duration_minutes']} min (rango: {spec['episode_defaults']['duration_range_minutes']})

PDF DEL TEMA (fuente principal):
{pdf_text[:18000]}

CONCEPTOS CLAVE DEL PDF (cubre al menos el 75%):
{json.dumps(concept_list, ensure_ascii=False)}

FUENTE DE CASOS EMPRESARIALES VERIFICADOS (usar prioritariamente en BLOQUE_REALIDAD):
{casos_text if casos_text else "(archivo no disponible — usar formulaciones prudentes sin cifras inventadas)"}

INSTRUCCIONES CRÍTICAS:
1. El hook lo abre {opener}. Cierra exactamente con: {rules['hook_closing_phrase']}
2. Después del hook: # INTRO_SONIDO  (línea siguiente: {rules['intro_comment']})
3. SALUDO_Y_PRESENTACION — FORMATO OBLIGATORIO DE TRES INTERVENCIONES SEPARADAS:
   (siendo OPENER = {opener} y OTRO = {other}; nombres hablados: IAGO->"Yago", MARIA->"Maria")
   Linea 1 — OPENER: Soy <nombre_opener>.
   Linea 2 — OTRO:   Y yo soy <nombre_otro>.
   Linea 3 — OPENER: [directo] Antes de empezar, el aviso de siempre: este episodio lo genera un sistema automatico de inteligencia artificial. Puede contener errores. Si oyes algo que no te cuadra, contrastalo.
   HARD-FAIL si: (a) un mismo speaker concatena su nombre y el del otro en la misma linea, (b) el aviso lo dice cualquiera que no sea {opener}, (c) faltan "sistema automatico" o "puede contener errores".
   PROHIBIDO: apellidos. Los presentadores se llaman Maria y Yago, sin apellidos.
4. Estructura obligatoria en orden (v5):
   # HOOK → # INTRO_SONIDO → # SALUDO_Y_PRESENTACION → # BLOQUE_PANORAMA → # BLOQUE_COMO → # BLOQUE_REALIDAD → # CIERRE_CONCEPTOS → # CIERRE_FINAL
5. Secciones PROHIBIDAS (NO generes): BLOQUE_QUE, BLOQUE_LIMITES, BLOQUE_1, BLOQUE_2, BLOQUE_3, BLOQUE_4, APLICACION_PRACTICA, INSERCION_1, INSERCION_2, INSERCION_3
6. ROLES POR BLOQUE (obligatorio):
   - BLOQUE_PANORAMA: IAGO es la voz principal (min 65% palabras). MARIA hace 1-2 preguntas de matiz (≤20 palabras cada una). IAGO abre el bloque. Explica QUÉ es el concepto, definición precisa, por qué importa.
   - BLOQUE_COMO: COMPARTIDO. OBLIGATORIO: IAGO y MARIA deben tener ENTRE 40%-60% cada uno del total de palabras del bloque. Para lograrlo: si hay 2+ sub-conceptos, sub1 lo lidera IAGO (4-6 frases, 70-120 palabras), sub2 lo lidera MARIA (4-6 frases, 70-120 palabras). PROHIBIDO que MARIA solo haga preguntas en BLOQUE_COMO; MARIA debe explicar al menos un sub-concepto completo.
   - BLOQUE_REALIDAD: MARIA es la VOZ EXPERTA de empresa en este bloque. MARIA presenta los casos reales, datos de adopción y retos empresariales (mínimo 5 intervenciones de desarrollo, cada una con ≥4 frases). IAGO solo aporta contexto técnico breve cuando sea estrictamente necesario (máximo 2 intervenciones, ≤3 frases cada una). Si IAGO habla más que MARIA en este bloque, el guion está INCORRECTO. Usa prioritariamente la FUENTE DE CASOS EMPRESARIALES VERIFICADOS. Incluye al menos 2 de: dato adopción con fuente, caso empresa real con resultado, reto documentado, oportunidad de negocio.
7. Interjecciones PROHIBIDAS: {json.dumps(rules['blacklist_validation_interjections'], ensure_ascii=False)}
8. # CIERRE_CONCEPTOS — ESTRUCTURA OBLIGATORIA (hard-fail si no cumple):
   Exactamente 3 bloques hablados. El speaker que ABRE el episodio (HOOK) es el "líder".
   BLOQUE 1 (líder): Dice "{rules['concepts_closing_phrase']}" + inmediatamente "Primero: [concepto 1]" — TODO EN UN SOLO BLOQUE.
   BLOQUE 2 (apoyo): "Segundo: [concepto 2]"
   BLOQUE 3 (líder): "Tercero: [concepto 3]"
   PROHIBIDO: opener en bloque separado. El "No te puedes ir..." y el primer concepto VAN JUNTOS en un único bloque del líder.
   Cada concepto en una sola frase concisa, no expandidos.
9. # CIERRE_FINAL incluye exactamente: {rules['final_closing_phrase']}
   SOLO {other if opener != "IAGO" else "IAGO" if opener == "IAGO" else other} pronuncia el cierre según paridad. El otro speaker NO responde, NO añade nada. El guion termina cuando el closer dice su última frase. HARD-FAIL si hay intervención adicional tras el cierre.
10. Usa "Yago" en el texto hablado, nunca "Iago".
11. REGLA DE LONGITUD — DURA (BIDIRECCIONAL):
    El diálogo total DEBE estar entre {rules['minimum_word_count']} y {rules['maximum_word_count']} palabras.
    MÍNIMO OBLIGATORIO: {rules['minimum_word_count']} palabras totales. Si llegas a CIERRE_CONCEPTOS con menos de {rules['minimum_word_count']-150} palabras de diálogo, AMPLÍA los bloques centrales antes de continuar.
    MÁXIMO: {rules['maximum_word_count']} palabras. Si llegas a BLOQUE_REALIDAD habiendo gastado más de {int(rules['maximum_word_count'] * 0.72)} palabras, RECORTA ese bloque.
    NUNCA recortes HOOK ni CIERRE_CONCEPTOS.
    CONTROL: cada bloque de desarrollo (no preguntas ni reacciones) debe tener EXACTAMENTE 4-6 frases (60-100 palabras). Está PROHIBIDO escribir un bloque de desarrollo con 3 frases o menos. Si tienes menos de 4, amplía antes de continuar.
12. REGLA CIERRE — PRIMERA:
    Antes de escribir BLOQUE_PANORAMA, redacta mentalmente los 3 puntos del CIERRE_CONCEPTOS.
    Esos puntos deben derivarse directamente de los bloques centrales.
    Cuando llegues al CIERRE_CONCEPTOS, escribe EXACTAMENTE esos 3 puntos, ni uno más ni uno menos.
13. REGLA ANALOGÍA — DURA:
    Cada concepto técnico complejo (>3 sílabas, inglés o compuesto) debe ir precedido de UNA analogía cotidiana en 1-2 frases, ANTES de cualquier explicación técnica.
    MAL: "Los embeddings son vectores en espacio de alta dimensión."
    BIEN: "Imagina que cada palabra es una posición en un mapa. Las palabras similares están cerca. Eso son los embeddings."
    Marcadores válidos: "imagina que", "es como cuando", "piensa en", "el equivalente sería", "igual que".
14. REGLA AUDIO — LONGITUD DE INTERVENCIÓN:
    Intervención de desarrollo: 60-120 palabras (4-6 frases) — zona óptima TTS a 1.32x velocidad.
    Máximo absoluto por intervención: 190 palabras. Si un concepto necesita más, pártelo en DOS bloques:
    el primero ≤190 palabras, el otro speaker hace una pregunta breve, y el primero retoma ≤190 palabras.
    Reacciones/preguntas: máximo 20 palabras (preferiblemente 8-15). NO usar interjecciones de validación.
15. REGLA AUDIO — NÚMEROS EN PALABRAS:
    TODOS los números van en palabras. El TTS a 1.32x pronuncia mal "3.7%" o "$3M".
    MAL: "el 3.7% de empresas", "costó $3M", "en Q3 2026".
    BIEN: "el tres punto siete por ciento", "costó tres millones de dólares", "en el tercer trimestre".
    Excepción: años de papers donde el año es parte del nombre ("el informe McKinsey 2024").
16. REGLA TECNICISMO ACELERADO — AUDIO:
    Todo tecnicismo largo (>3 sílabas, inglés o compuesto) necesita frase introductoria previa.
    MAL: "backpropagation es el algoritmo que..."
    BIEN: "El algoritmo clave, que llamamos backpropagation, es..."
17. ANTIPINGPONG: nunca pongas 3 intervenciones del MISMO speaker seguidas. Intercala.
18. REGLA DE DIÁLOGO NATURAL — PROHIBICIONES:
    PROHIBIDO: enumeraciones "Primero... Segundo... Tercero... Cuarto..." en el turno de un solo speaker.
    Si necesitas listar 3+ puntos, distribúyelos entre ambos speakers con reacciones entre ellos.
    PROHIBIDO: que un speaker se haga una pregunta y la responda él mismo en el turno siguiente.
    PROHIBIDO: intervenciones genéricas de relleno sin contenido específico del tema ("Bien apuntado,
    déjame añadir la perspectiva técnica...", "Hay algo que me genera curiosidad en este punto...").
18. REFERENCIAS TEMPORALES — REGLA DURA:
    Cuando hables del ESTADO ACTUAL, NO cites año: usa "hoy", "actualmente", "en este momento".
    Solo cita un año cuando esté pegado a una publicación identificable por nombre propio.
    PROHIBIDO usar "en 2024", "en 2025", "en dos mil veinticinco" como marcador del presente.
19. BLOQUE_REALIDAD — REGLA ANTI-HALLUCINATION:
    Para datos y casos empresariales, usa EXCLUSIVAMENTE la FUENTE DE CASOS EMPRESARIALES VERIFICADOS.
    Si el dato no está en esa fuente, usa "según estudios recientes de [institución conocida]" sin inventar cifras.
    NUNCA inventes nombres de empresa, estadísticas exactas o citas a estudios que no puedas verificar.
"""
    return system, user


def build_verification_section(
    script_body: str,
    spec: dict,
    concept_list: list[str],
    usage: TokenUsage,
) -> str:
    stats = build_script_stats(script_body, spec, concept_list)
    rules = spec["script_rules"]
    coverage_hits = [c for c, m in stats["concept_mentions"].items() if m >= 1]
    coverage_pct  = int(round(len(coverage_hits) / max(len(concept_list), 1) * 100))
    lines = [
        "# VERIFICACIONES",
        "##",
        f"## PALABRAS TOTALES : {stats['word_count_total']} "
        f"(objetivo: {rules['minimum_word_count']}-{rules.get('maximum_word_count', '?')})",
        f"## MEDIA PALABRAS/INTERVENCION : {stats['avg_words_per_intervention']:.1f}",
        "##",
        "## COBERTURA DE CONCEPTOS DEL PDF:",
    ]
    for concept in concept_list:
        mentions = stats["concept_mentions"].get(concept, 0)
        marker = "OK" if mentions >= 1 else "FALTA"
        lines.append(f"## [{marker}] {concept}: {mentions} menciones")
    lines.append(f"## Cobertura: {coverage_pct}% (objetivo: {rules.get('minimum_pdf_coverage_percent', 75)}%)")
    lines.extend([
        "##",
        "## TOKENS ANTHROPIC:",
        f"## input_tokens: {usage.input_tokens}",
        f"## output_tokens: {usage.output_tokens}",
        f"## cache_read: {usage.cache_read}",
        f"## total: {usage.total}",
    ])
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de guiones T — MaquinarIA Pesada")
    parser.add_argument("--pdf",          required=True,  help="Ruta al PDF del tema (ej: PDFs/temas/M1_T11_limitaciones_llms.pdf)")
    parser.add_argument("--spec",         default=str(SPEC_PATH), help="Ruta a PODCAST_T_SPEC.md")
    parser.add_argument("--max-intentos", type=int, default=3)
    args = parser.parse_args()

    # ── Cargar spec ─────────────────────────────────────────────────────────
    spec          = load_spec(args.spec)
    spec_markdown = read_text(Path(args.spec))

    # ── PDF ──────────────────────────────────────────────────────────────────
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        pdf_path = BASE_DIR / args.pdf
    pdf_text      = extract_pdf_text(pdf_path)
    modulo_n      = infer_module_n(pdf_path)
    topic_name    = infer_topic_name_from_pdf(pdf_path)   # T11_limitaciones_llms
    topic_display = infer_topic_display(pdf_path)          # Limitaciones LLMs

    # ── Naming de salida ─────────────────────────────────────────────────────
    guion_filename = f"M{modulo_n}_TX_{topic_name}.txt"   # M1_TX_T11_limitaciones_llms.txt
    guion_path     = BASE_DIR / spec["directories"]["scripts_dir"] / guion_filename
    ep_code        = guion_to_ep_code(Path(guion_filename).stem)  # M1_TX_E_T11_limitaciones_llms

    print(f"\n{'='*60}")
    print("  GENERADOR GUION T — MaquinarIA Pesada")
    print(f"  Módulo   : M{modulo_n} — {topic_display}")
    print(f"  PDF      : {pdf_path.name}")
    print(f"  Salida   : {guion_filename}")
    print(f"  ep_code  : {ep_code}")
    print(f"{'='*60}\n")

    # ── Anthropic ────────────────────────────────────────────────────────────
    client = make_anthropic_client()
    usage  = TokenUsage()

    # ── Conceptos ────────────────────────────────────────────────────────────
    print("  [1/3] Extrayendo conceptos del PDF...")
    concept_list = extract_concepts_with_claude(client, spec, pdf_text, topic_display, usage)
    if not concept_list:
        concept_list = extract_theme_concepts(pdf_text, limit=8)
    print(f"         Conceptos: {concept_list[:4]}...")

    # ── Apertura ─────────────────────────────────────────────────────────────
    opener = opening_speaker(ep_code, spec)

    # ── Generación ───────────────────────────────────────────────────────────
    gen_model   = spec["anthropic"]["default_generation_model"]
    max_tokens  = spec["anthropic"]["max_output_tokens"]
    temperature = spec["anthropic"]["temperature"]

    system_prompt, user_prompt = build_generation_prompt(
        spec, spec_markdown, modulo_n, topic_display,
        pdf_text, opener, concept_list,
    )

    local_issues: list[str] = []
    draft = ""
    best_draft = ""
    best_issues: list[str] = []
    best_score: tuple[int, int, int] = (999, 999, 999)  # (hard_count, word_deficit, soft_count)

    for attempt in range(1, args.max_intentos + 1):
        print(f"\n  [2/3] Generando guion (intento {attempt}/{args.max_intentos})...")

        feedback_issues = best_issues if best_issues else local_issues
        if attempt > 1 and feedback_issues:
            all_hard = [i for i in feedback_issues if not i.startswith("[WARN]")]
            if all_hard:
                feedback_parts = []
                for issue in all_hard:
                    wc_min = re.search(r"tiene (\d+) palabras \(minimo: (\d+)\)", issue)
                    wc_max = re.search(r"tiene (\d+) palabras \(maximo recomendado: (\d+)\)", issue)
                    if wc_min:
                        actual, needed = int(wc_min.group(1)), int(wc_min.group(2))
                        diff = needed - actual
                        feedback_parts.append(
                            f"- {issue}\n"
                            f"  ACCIÓN: añade {diff} palabras más. Amplía BLOQUE_PANORAMA "
                            f"(+1 bloque IAGO de 4+ frases) y BLOQUE_COMO (+2-3 frases). NO recortes nada."
                        )
                    elif wc_max:
                        actual, limit = int(wc_max.group(1)), int(wc_max.group(2))
                        diff = actual - limit
                        feedback_parts.append(
                            f"- {issue}\n"
                            f"  ACCIÓN: elimina {diff} palabras. Recorta BLOQUE_REALIDAD "
                            f"quitando el ejemplo menos relevante."
                        )
                    elif "BLOQUE_COMO" in issue:
                        feedback_parts.append(
                            f"- {issue}\n"
                            f"  ACCIÓN: MARIA debe liderar al menos UN sub-concepto completo "
                            f"en BLOQUE_COMO con 4-6 frases (70-120 palabras)."
                        )
                    elif "CIERRE_CONCEPTOS" in issue:
                        feedback_parts.append(
                            f"- {issue}\n"
                            f"  ACCIÓN: CIERRE_CONCEPTOS debe tener EXACTAMENTE 3 bloques. "
                            f"El opener 'No te puedes ir...' y el primer concepto van EN UN SOLO bloque del líder."
                        )
                    elif "consecutivos del mismo speaker" in issue:
                        feedback_parts.append(
                            f"- {issue}\n"
                            f"  ACCIÓN: NUNCA escribas 3 bloques seguidos del mismo speaker. "
                            f"Después de cada 2 bloques de IAGO, MARIA debe intervenir (al menos 1 bloque). "
                            f"Revisa toda la sección y alterna obligatoriamente."
                        )
                    else:
                        feedback_parts.append(f"- {issue}")
                # Include soft warns about short blocks and enumerated lists
                soft_retry = [i for i in feedback_issues if i.startswith("[WARN]")]
                for s in [x for x in soft_retry if re.search(r"solo [123] frase", x)][:3]:
                    feedback_parts.append(
                        f"- {s}\n"
                        f"  ACCIÓN: amplía ese bloque a mínimo 4 frases completas (70-100 palabras)."
                    )
                for s in [x for x in soft_retry if "lista enumerada" in x][:3]:
                    feedback_parts.append(
                        f"- {s}\n"
                        f"  ACCIÓN: NO uses Primero/Segundo/Tercero en un mismo turno. "
                        f"Distribuye: un speaker explica un punto, el otro reacciona, continúa."
                    )
                user_prompt_ext = (
                    user_prompt
                    + "\n\nFEEDBACK OBLIGATORIO (corrige TODOS estos puntos antes de generar):\n"
                    + "\n".join(feedback_parts)
                )
            else:
                user_prompt_ext = user_prompt
        else:
            user_prompt_ext = user_prompt

        text, resp = call_claude(
            client, gen_model, system_prompt, user_prompt_ext,
            max_tokens=max_tokens, temperature=temperature,
            source="generar_guion_t.py",
        )
        usage.add(resp)
        draft = normalize_generated_script(strip_verification_block(text), spec)
        draft = enforce_fixed_phrases(draft, spec)
        draft = _fix_digit_numbers_in_dialogue(draft)
        draft = _trim_cierre_conceptos_if_excess(draft, spec)
        draft = _rebalance_shared_block(draft, spec)
        draft = _split_oversized_blocks(draft, spec=spec)
        draft = _split_oversized_sentence_blocks(draft, spec=spec)
        draft = _fix_antipingpong(draft, spec)

        verification = build_verification_section(draft, spec, concept_list, usage)
        draft_with_ver = draft.rstrip() + "\n\n" + verification

        local_issues = validate_script_text(draft_with_ver, ep_code, spec, concept_list, base_dir=BASE_DIR)
        hard_issues  = [i for i in local_issues if not i.startswith("[WARN]")]
        soft_issues  = [i for i in local_issues if i.startswith("[WARN]")]

        # Promover ciertos soft warns a hard para forzar retry
        extra_hard = [
            i.removeprefix("[WARN] ") for i in soft_issues
            if ("maximo recomendado" in i and "palabras" in i and "por intervencion" not in i)
        ]
        if extra_hard:
            hard_issues = hard_issues + extra_hard

        print(f"         Issues hard: {len(hard_issues)} | soft: {len(soft_issues)}")
        for issue in hard_issues:
            print(f"         FAIL: {issue}")
        for issue in soft_issues:
            print(f"         WARN: {issue}")

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
            print("         OK")
            break

        if attempt == args.max_intentos:
            print(f"\n  [WARN] Max intentos. Guardando mejor intento ({best_score[0]} hard, {best_score[2]} soft).")
            draft = best_draft

    # ── Guardar ──────────────────────────────────────────────────────────────
    print("\n  [3/3] Guardando...")
    guion_path.parent.mkdir(parents=True, exist_ok=True)
    guion_path.write_text(draft.rstrip() + "\n", encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  GUION T GENERADO : {guion_path}")
    print(f"  Tokens           : {usage.report()}")
    if not [i for i in local_issues if not i.startswith("[WARN]")]:
        print("  Validacion       : PASS")
    else:
        print(f"  Issues hard      : {len([i for i in local_issues if not i.startswith('[WARN]')])}")
    print(f"{'='*60}\n")

    hard_issues = [i for i in local_issues if not i.startswith("[WARN]")]
    if hard_issues:
        raise SystemExit(
            f"Guion T generado con {len(hard_issues)} issue(s) hard. Revisa antes de generar audio."
        )


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el pipeline
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="generar_guion_t.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()

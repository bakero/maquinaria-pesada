#!/usr/bin/env python3
"""
generar_guion_t.py — Generador de guiones T (Tema) para MaquinarIA Pesada.

Genera guiones de episodios T usando:
  - PDF del tema específico en PDFs/temas/M{n}_T{k}_*.pdf
  - claude-sonnet-4-5 para generación, claude-haiku para conceptos
  - Estructura: BLOQUE_QUE / BLOQUE_COMO / BLOQUE_LIMITES

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
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR  = Path(__file__).parent
SPEC_PATH = BASE_DIR / "PODCAST_T_SPEC.md"

sys.path.insert(0, str(BASE_DIR))
from podcast_spec import (
    load_spec,
    read_text,
    build_script_stats,
    count_words,
    extract_theme_concepts,
    normalize_text_for_match,
    opening_speaker,
    remove_leading_tag,
    validate_script_text,
    guion_to_ep_code,
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
            f"cache_read={self.cache_read} total={self.total}"
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
# Anthropic client
# ---------------------------------------------------------------------------

def make_anthropic_client():
    try:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise SystemExit("ANTHROPIC_API_KEY no encontrada en .env")
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        raise SystemExit("Faltan dependencias: pip install anthropic")


def call_claude(
    client, model: str, system: str, user: str,
    max_tokens: int, temperature: float
) -> tuple[str, object]:
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text, response


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
        text, resp = call_claude(client, model, system, user, max_tokens=800, temperature=0.0)
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

    # Asignación de roles por bloque según T-spec
    # Yago lidera BLOQUE_QUE, compartido BLOQUE_COMO, Maria lidera BLOQUE_LIMITES
    rules = spec["script_rules"]

    system = (
        "Eres el sistema de producción del podcast MaquinarIA Pesada. "
        "Generas guiones de episodios T (tema): concisos, técnicos y amenos. "
        "Sigues la especificación PODCAST_T_SPEC.md al pie de la letra. "
        "Devuelves SOLO el guion. Sin explicaciones, sin markdown adicional. "
        "Todas las intervenciones empiezan por IAGO: o MARIA:. "
        "No incluyas la sección # VERIFICACIONES; el sistema la añade después."
    )

    user = f"""ESPECIFICACION (PODCAST_T_SPEC.md):
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

INSTRUCCIONES CRÍTICAS:
1. El hook lo abre {opener}. Cierra exactamente con: {rules['hook_closing_phrase']}
2. Después del hook: # INTRO_SONIDO  (línea siguiente: {rules['intro_comment']})
3. Aviso de IA en # SALUDO_Y_PRESENTACION, dicho por {opener}.
   Debe contener EXACTAMENTE: "sistema automatico" y "puede contener errores".
4. Estructura obligatoria en orden:
   # HOOK → # INTRO_SONIDO → # SALUDO_Y_PRESENTACION → # BLOQUE_QUE → # BLOQUE_COMO → # BLOQUE_LIMITES → # CIERRE_CONCEPTOS → # CIERRE_FINAL
5. Secciones PROHIBIDAS (NO generes): BLOQUE_1, BLOQUE_2, BLOQUE_3, BLOQUE_4, APLICACION_PRACTICA, INSERCION_1, INSERCION_2, INSERCION_3
6. ROLES POR BLOQUE (obligatorio):
   - BLOQUE_QUE: IAGO lidera (min 65% palabras). MARIA hace 1-2 preguntas de matiz.
     Explica QUÉ es el concepto: definición precisa, mecanismo, por qué existe.
   - BLOQUE_COMO: compartido (40-60% cada uno). Líder rota por sub-concepto.
     Explica CÓMO funciona: implementación, proceso, flujo técnico.
   - BLOQUE_LIMITES: MARIA lidera (min 65% palabras). IAGO da contexto técnico.
     Explica LÍMITES: qué falla, cuándo no funciona, contraintuitivos, riesgos.
7. Interjecciones PROHIBIDAS: {json.dumps(rules['blacklist_validation_interjections'], ensure_ascii=False)}
8. # CIERRE_CONCEPTOS abre con: {rules['concepts_closing_phrase']}
   Exactamente 3 conceptos (ni 2 ni 4 — hard-fail si hay otra cantidad).
   Alternados: líder-apoyo-líder o apoyo-líder-apoyo según paridad del TEMA.
   Cada concepto en una sola frase, no expandidos.
9. # CIERRE_FINAL incluye exactamente: {rules['final_closing_phrase']}
10. Usa "Yago" en el texto hablado, nunca "Iago".
11. Objetivo de palabras habladas: {rules['minimum_word_count']}-{rules['maximum_word_count']}.
12. Intervenciones de desarrollo: mínimo {rules['minimum_sentences_per_intervention']} frases.
13. Traduce o aterriza cualquier tecnicismo en la misma intervención.
14. Un solo [tag] al inicio de cada intervención cuando aporte tono.
    Tags disponibles: {json.dumps(spec['speakers']['IAGO']['allowed_tags'][:10])}, etc.
"""
    return system, user


def _fix_tts_closing_tags(content: str) -> str:
    open_match = re.search(r"<([a-zA-Z_]+)>", content)
    if open_match:
        tag = open_match.group(1).lower()
        content = re.sub(r"</(iago|maria|yago|IAGO|MARIA|YAGO)>", f"</{tag}>", content, flags=re.IGNORECASE)
    return content


_TAG_REMAP = {
    "curiosa": "curioso", "esceptica": "esceptico", "ironica": "ironico",
    "didactica": "didactico", "explicativa": "explicativo", "directa": "directo",
    "seria": "serio", "contundenta": "contundente", "reflexiva": "reflexivo",
    "natural": "natural", "pausada": "pausado", "calida": "calido",
    "clara": "claro", "analitico": "analitica",
}


def _fix_gendered_tags(content: str) -> str:
    def _remap_sq(m: re.Match) -> str:
        canonical = _TAG_REMAP.get(m.group(1).lower(), m.group(1).lower())
        return f"[{canonical}]"
    def _remap_ang(m: re.Match) -> str:
        slash = m.group(1) or ""
        canonical = _TAG_REMAP.get(m.group(2).lower(), m.group(2).lower())
        return f"<{slash}{canonical}>"
    content = re.sub(r"\[([a-zA-Z_]+)\]", _remap_sq, content)
    content = re.sub(r"<(/?)([a-zA-Z_]+)>", _remap_ang, content)
    return content


def _remove_blacklisted_opening(content: str, spec: dict) -> str:
    rules = spec.get("script_rules", {})
    blacklist = rules.get("blacklist_validation_interjections") or rules.get("blacklisted_interjections") or []
    short_limit = rules.get("reaction_word_limit", 12)
    plain = re.sub(r"^\[[^\]]+\]\s*", "", content.strip())
    word_count = len(plain.split())
    is_short = word_count <= short_limit
    LEADING_TAG = r"(?:(\[[^\]]+\])\s*)?"
    for phrase in blacklist:
        pat_start = re.compile(r"^" + LEADING_TAG + re.escape(phrase) + r"[.,!]?\s*", re.IGNORECASE)
        content = pat_start.sub(r"\1 ", content).strip()
        if is_short:
            pat_any = re.compile(r"\b" + re.escape(phrase) + r"\b[.,!]?\s*", re.IGNORECASE)
            content = pat_any.sub("", content).strip()
    return content


def normalize_generated_script(script_text: str, spec: dict) -> str:
    SPEAKER_PAT = re.compile(r"^(IAGO|MARIA|MARÍA)\s*:\s*(.*)$", re.IGNORECASE)
    lines = script_text.replace("\r\n", "\n").split("\n")
    normalized: list[str] = []
    for line in lines:
        stripped = line.rstrip().strip()
        m = SPEAKER_PAT.match(stripped)
        if m:
            speaker = m.group(1).upper().replace("Í", "I")
            content = re.sub(r"\bIago\b", "Yago", m.group(2).strip(), flags=re.IGNORECASE)
            content = _fix_tts_closing_tags(content)
            content = _fix_gendered_tags(content)
            content = _remove_blacklisted_opening(content, spec)
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

    Idéntica a la de generar_guion.py; opera sin bloque de verificaciones.
    """
    rules = spec["script_rules"]
    SPEAKER_RE = re.compile(r"^(IAGO|MARIA)\s*:\s*(.*)$", re.IGNORECASE | re.MULTILINE)

    def _inject_into_section(
        body: str,
        section_marker: str,
        phrase: str,
        position: str,  # "first_block" | "last_block"
    ) -> str:
        norm_phrase = normalize_text_for_match(phrase)
        if norm_phrase in normalize_text_for_match(body):
            return body
        lines = body.split("\n")
        sec_idx = None
        for i, ln in enumerate(lines):
            if ln.strip().upper() == f"# {section_marker}":
                sec_idx = i
                break
        if sec_idx is None:
            return body
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
            new_content = f"[calido]{phrase}" if not tag else f"{tag}{phrase}"
            lines[target_idx] = f"{speaker}: {new_content}"
        else:
            plain = remove_leading_tag(content)
            new_content = f"{tag}{phrase} {plain}" if tag else f"{phrase} {plain}"
            lines[target_idx] = f"{speaker}: {new_content}"
        return "\n".join(lines)

    if rules.get("final_closing_phrase"):
        text = _inject_into_section(text, "CIERRE_FINAL", rules["final_closing_phrase"], "last_block")
    if rules.get("concepts_closing_phrase"):
        text = _inject_into_section(text, "CIERRE_CONCEPTOS", rules["concepts_closing_phrase"], "first_block")
    if rules.get("hook_closing_phrase"):
        text = _inject_into_section(text, "HOOK", rules["hook_closing_phrase"], "last_block")
    return text


def extract_leading_tag(text: str) -> str | None:
    """Extrae [tag] al inicio si existe."""
    import re as _re
    m = _re.match(r"^\[(.+?)\]\s*", text.strip())
    return f"[{m.group(1).strip()}]" if m else None


def remove_leading_tag(text: str) -> str:
    """Elimina [tag] al inicio si existe."""
    import re as _re
    return _re.sub(r"^\[(.+?)\]\s*", "", text.strip(), count=1)


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
    parser.add_argument("--max-intentos", type=int, default=2)
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
    print(f"  GENERADOR GUION T — MaquinarIA Pesada")
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

    for attempt in range(1, args.max_intentos + 1):
        print(f"\n  [2/3] Generando guion (intento {attempt}/{args.max_intentos})...")

        if attempt > 1:
            hard_issues = [i for i in local_issues if not i.startswith("[WARN]")]
            if hard_issues:
                user_prompt_ext = (
                    user_prompt
                    + "\n\nFEEDBACK (corrige todos estos puntos):\n"
                    + "\n".join(f"- {i}" for i in hard_issues)
                )
            else:
                user_prompt_ext = user_prompt
        else:
            user_prompt_ext = user_prompt

        text, resp = call_claude(
            client, gen_model, system_prompt, user_prompt_ext,
            max_tokens=max_tokens, temperature=temperature,
        )
        usage.add(resp)
        draft = normalize_generated_script(strip_verification_block(text), spec)
        draft = enforce_fixed_phrases(draft, spec)

        verification = build_verification_section(draft, spec, concept_list, usage)
        draft_with_ver = draft.rstrip() + "\n\n" + verification

        local_issues = validate_script_text(draft_with_ver, ep_code, spec, concept_list, base_dir=BASE_DIR)
        hard_issues  = [i for i in local_issues if not i.startswith("[WARN]")]
        soft_issues  = [i for i in local_issues if i.startswith("[WARN]")]

        print(f"         Issues hard: {len(hard_issues)} | soft: {len(soft_issues)}")
        for issue in hard_issues:
            print(f"         FAIL: {issue}")
        for issue in soft_issues:
            print(f"         WARN: {issue}")

        if not hard_issues:
            draft = draft_with_ver
            print("         OK")
            break

        if attempt == args.max_intentos:
            print(f"\n  [WARN] Max intentos. Guardando con {len(hard_issues)} issue(s) hard.")
            draft = draft_with_ver

    # ── Guardar ──────────────────────────────────────────────────────────────
    print(f"\n  [3/3] Guardando...")
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
    main()

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
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR  = Path(__file__).parent
SPEC_PATH = BASE_DIR / "PODCAST_M_SPEC.md"

sys.path.insert(0, str(BASE_DIR))
from podcast_spec import (
    load_spec,
    read_text,
    build_script_stats,
    count_concept_mentions,
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
    except ImportError:
        raise SystemExit("Faltan dependencias: pip install anthropic")


def call_claude(client, model: str, system: str, user: str, max_tokens: int, temperature: float) -> tuple[str, object]:
    """Llama a Claude y devuelve (content_text, response)."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
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
        "Devuelve JSON exactamente así:\n"
        '{"key_concepts": ["concepto1", "concepto2"], '
        '"hard_for_audio": ["termino_visual1"]}'
    )
    try:
        text, resp = call_claude(client, model, system, user, max_tokens=1000, temperature=0.0)
        usage.add(resp)
        data = json.loads(text)
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
        "Generas guiones de episodios M (módulo): largos, técnicos, rigurosos y amenos. "
        "Sigues la especificación PODCAST_M_SPEC.md al pie de la letra. "
        "Devuelves SOLO el guion. Sin explicaciones, sin markdown adicional. "
        "Todas las intervenciones empiezan por IAGO: o MARIA:. "
        "No incluyas la sección # VERIFICACIONES; el sistema la añade después."
    )

    ficha_text = (
        f"Párrafos encontrados en docs vivos: {ficha['paragraphs_found']}\n"
        f"Por documento: {ficha['hits_by_doc']}\n"
        f"Material:\n{ficha.get('material_snippet', '(sin material externo verificable)')}"
    )

    user = f"""ESPECIFICACION MAESTRA (PODCAST_M_SPEC.md):
{spec_markdown}

PARÁMETROS DEL EPISODIO:
- Módulo: M{modulo_n}
- Tema: {topic}
- Hook abre: {opener} (paridad del módulo)
- Duración objetivo: {spec['episode_defaults']['duration_minutes']} min

PDF RESUMEN DEL MÓDULO (fuente primaria para bloques conceptuales):
{pdf_text[:20000]}

CONCEPTOS CLAVE EXTRAÍDOS DEL PDF (cubre al menos el 75%):
{json.dumps(concept_list, ensure_ascii=False)}

TÉRMINOS DIFÍCILES PARA AUDIO (traduce y aterriza):
{json.dumps(hard_audio, ensure_ascii=False)}

MATERIAL DE APLICACION_PRACTICA (extraído de los 4 documentos vivos):
{ficha_text}

INSTRUCCIONES CRÍTICAS:
1. El hook lo abre {opener}. Cierra exactamente con: {spec['script_rules']['hook_closing_phrase']}
2. Después del hook incluye exactamente: # INTRO_SONIDO  (siguiente línea: {spec['script_rules']['intro_comment']})
3. El aviso de IA va en # SALUDO_Y_PRESENTACION, 18-25s, dicho por {opener}.
   Debe contener EXACTAMENTE las palabras: "sistema automatico" y "puede contener errores".
   Añade una frase que conecte con APLICACION_PRACTICA (ej: "al final del episodio veremos cómo se aplica lo de hoy a ese sistema").
4. Estructura obligatoria en orden:
   # HOOK → # INTRO_SONIDO → # SALUDO_Y_PRESENTACION → # BLOQUE_PANORAMA → # BLOQUE_TEMAS_CLAVE → # BLOQUE_LIMITES → # APLICACION_PRACTICA → # CIERRE_CONCEPTOS → # CIERRE_FINAL
5. Secciones PROHIBIDAS (no las generes): BLOQUE_1, BLOQUE_2, BLOQUE_3, BLOQUE_4, BLOQUE_QUE, BLOQUE_COMO, INSERCION_1, INSERCION_2, INSERCION_3, INSERCION_EMPRESA
6. APLICACION_PRACTICA: 3 momentos internos (SIEMPRE así, independiente del opener del hook):
   - Momento 1 (MARIA plantea, ~45-60s): "Ahora veamos cómo todo esto se aplica en un sistema real..."
   - Momento 2 (IAGO detalla, ~2-2.5 min): usa el material de los docs vivos. NO inventes hechos.
     Si el material es escaso, hazlo explícito en el texto ("en nuestro sistema hemos tenido que resolver...").
   - Momento 3 (cierre conjunto MARIA+IAGO, ~30-45s)
7. CIERRE_CONCEPTOS abre con: {spec['script_rules']['concepts_closing_phrase']}
   Lista 3-5 conceptos. Al menos uno conectado con APLICACION_PRACTICA.
8. CIERRE_FINAL incluye exactamente: {spec['script_rules']['final_closing_phrase']}
9. Interjecciones PROHIBIDAS: {json.dumps(spec['script_rules']['blacklist_validation_interjections'], ensure_ascii=False)}
10. Usa "Yago" en el texto hablado, nunca "Iago".
11. Objetivo de palabras habladas (sin headers ni speakers): {spec['script_rules']['minimum_word_count']}-{spec['script_rules']['maximum_word_count']}.
12. Intervenciones de desarrollo: mínimo {spec['script_rules']['minimum_sentences_per_intervention']} frases.
13. Traduce o aterriza al castellano cualquier tecnicismo en la misma intervención.
14. BALANCE OBLIGATORIO DE PALABRAS POR BLOQUE (cuéntalas mentalmente antes de pasar al siguiente bloque):
    - BLOQUE_PANORAMA: IAGO debe tener ≥65% de las palabras del bloque. MARIA hace preguntas cortas (≤12 palabras cada una, máx 3 intervenciones).
    - BLOQUE_TEMAS_CLAVE: COMPARTIDO. Cada speaker debe tener ENTRE 40% y 60% de las palabras totales del bloque. Alterna el liderazgo por concepto. Si IAGO lleva 2 conceptos seguidos, el siguiente lo lidera MARIA.
    - BLOQUE_LIMITES: MARIA debe tener ≥65% de las palabras del bloque. IAGO da contexto técnico corto.
    - En BLOQUE_TEMAS_CLAVE si tienes 4 conceptos: IAGO-MARIA-IAGO-MARIA (150-200 palabras por concepto líder, el otro hace 1-2 preguntas de ≤20 palabras cada una).
"""
    return system, user


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
    from podcast_spec import normalize_text_for_match, extract_leading_tag, remove_leading_tag

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
            new_content = f"<calido>{phrase}</calido>" if not tag else f"{tag}{phrase}</{tag.strip('<>')}>"
            lines[target_idx] = f"{speaker}: {new_content}"
        else:
            # Prefijar la frase al bloque (para conceptos_closing)
            plain = remove_leading_tag(content)
            if tag:
                inner_tag = tag.strip("<>")
                new_content = f"{tag}{phrase} {plain}</{inner_tag}>"
            else:
                new_content = f"{phrase} {plain}"
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
    parser.add_argument("--max-intentos", type=int, default=2, help="Intentos si falla la validación")
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
    print(f"  GENERADOR GUION M — MaquinarIA Pesada")
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

    for attempt in range(1, args.max_intentos + 1):
        print(f"\n  [3/4] Generando guion (intento {attempt}/{args.max_intentos})...")

        if attempt > 1 and local_issues:
            # Añadir feedback de problemas previos al prompt
            hard_issues = [i for i in local_issues if not i.startswith("[WARN]")]
            if hard_issues:
                user_prompt_ext = (
                    user_prompt
                    + "\n\nFEEDBACK OBLIGATORIO DEL INTENTO ANTERIOR (corrige todos estos puntos):\n"
                    + "\n".join(f"- {i}" for i in hard_issues)
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

        # ── Validación ───────────────────────────────────────────────────────
        verification = build_verification_section(draft, spec, concept_list, usage, ficha)
        draft_with_ver = draft.rstrip() + "\n\n" + verification

        local_issues = validate_script_text(draft_with_ver, ep_code, spec, concept_list, base_dir=BASE_DIR)
        hard_issues  = [i for i in local_issues if not i.startswith("[WARN]")]
        soft_issues  = [i for i in local_issues if i.startswith("[WARN]")]

        print(f"         Issues hard: {len(hard_issues)} | soft: {len(soft_issues)}")
        for issue in hard_issues:
            print(f"         [HARD] {issue}")
        for issue in soft_issues:
            print(f"         [WARN] {issue}")

        if not hard_issues:
            draft = draft_with_ver
            print("         [PASS] Validacion OK")
            break

        if attempt == args.max_intentos:
            print(f"\n  [WARN] Superado máximo de intentos. Guardando con {len(hard_issues)} issue(s) hard.")
            draft = draft_with_ver

    # ── Guardar ──────────────────────────────────────────────────────────────
    print(f"\n  [4/4] Guardando guion...")
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

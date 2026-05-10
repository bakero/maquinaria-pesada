"""podcast_spec.py — Cargador y validador de specs M y T para MaquinarIA Pesada.

Soporta:
  - PODCAST_M_SPEC.md  (marker: PODCAST_M_SPEC_JSON_START/END)
  - PODCAST_T_SPEC.md  (marker: PODCAST_T_SPEC_JSON_START/END)

Todas las funciones de validación y parsing son agnósticas al tipo;
leen las reglas directamente del JSON embebido en el spec correspondiente.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


# ---------------------------------------------------------------------------
# Rutas por defecto
# ---------------------------------------------------------------------------

DEFAULT_M_SPEC_PATH = Path("PODCAST_M_SPEC.md")
DEFAULT_T_SPEC_PATH = Path("PODCAST_T_SPEC.md")

# Marcadores soportados: (start, end)
_MARKERS: list[tuple[str, str]] = [
    ("<!-- PODCAST_M_SPEC_JSON_START -->", "<!-- PODCAST_M_SPEC_JSON_END -->"),
    ("<!-- PODCAST_T_SPEC_JSON_START -->", "<!-- PODCAST_T_SPEC_JSON_END -->"),
    # Compatibilidad con spec genérico anterior (por si acaso)
    ("<!-- PODCAST_SPEC_JSON_START -->",   "<!-- PODCAST_SPEC_JSON_END -->"),
]

WORD_RE = re.compile(
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:[-'][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)?"
)
_SENT_PLACEHOLDER = "\x01"


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Carga de spec
# ---------------------------------------------------------------------------

def load_spec(path: str | Path = DEFAULT_M_SPEC_PATH) -> dict:
    """Carga y devuelve el JSON de spec incrustado en el archivo Markdown.

    Auto-detecta el marcador correcto (M, T o genérico).
    Lanza ValueError si no encuentra ningún bloque JSON válido.
    """
    path = Path(path)
    text = read_text(path)
    for start_marker, end_marker in _MARKERS:
        pattern = (
            re.escape(start_marker)
            + r"\s*```json\s*(.*?)\s*```"
            + r"\s*"
            + re.escape(end_marker)
        )
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(1))
    raise ValueError(
        f"No se encontró bloque JSON en {path}. "
        "Comprueba que el archivo contiene el marcador correcto."
    )


# Alias de compatibilidad hacia atrás
def load_master_spec(path: str | Path = DEFAULT_M_SPEC_PATH) -> dict:
    return load_spec(path)


# ---------------------------------------------------------------------------
# Texto y normalización
# ---------------------------------------------------------------------------

def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text_for_match(value: str) -> str:
    return strip_accents(value).lower()


def normalize_speaker(value: str, spec: dict) -> str:
    clean = normalize_text_for_match(value.strip().upper())
    aliases = spec["script_rules"]["speaker_aliases"]
    for canonical, items in aliases.items():
        normalized_items = {normalize_text_for_match(i.upper()) for i in items}
        if clean in normalized_items:
            return canonical
    if value.strip().upper() in spec["speakers"]:
        return value.strip().upper()
    raise ValueError(f"Speaker no reconocido: {value}")


# ---------------------------------------------------------------------------
# Helpers de episodio
# ---------------------------------------------------------------------------

def episode_number(ep_code: str) -> int:
    """Extrae el número de módulo del código de episodio (M0, M3, M12…)."""
    match = re.search(r"M(\d+)", ep_code, re.IGNORECASE)
    if not match:
        raise ValueError(f"No se pudo extraer número de módulo de: {ep_code}")
    return int(match.group(1))


def opening_speaker(ep_code: str, spec: dict) -> str:
    """Devuelve MARIA o IAGO según paridad del módulo y la spec.

    Pares (M0, M2, M4…) → MARIA
    Impares (M1, M3, M5…) → IAGO
    """
    number = episode_number(ep_code)
    for speaker, cfg in spec["speakers"].items():
        if number % 2 == 0 and cfg.get("opens_even_modules"):
            return speaker
        if number % 2 == 1 and cfg.get("opens_odd_modules"):
            return speaker
    # fallback: par=MARIA, impar=IAGO
    return "MARIA" if number % 2 == 0 else "IAGO"


# ---------------------------------------------------------------------------
# Contadores
# ---------------------------------------------------------------------------

def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def sentence_count(text: str) -> int:
    plain = remove_leading_tag(text)
    plain = re.sub(r"(\d)\.(\d)", lambda m: m.group(1) + _SENT_PLACEHOLDER + m.group(2), plain)
    plain = re.sub(
        r"\b([A-ZÁÉÍÓÚÜ])\.\s*([A-ZÁÉÍÓÚÜ]\.?)",
        lambda m: m.group().replace(".", _SENT_PLACEHOLDER),
        plain,
    )
    parts = [p.strip() for p in re.split(r"[.!?]+", plain) if p.strip()]
    return len(parts)


# ---------------------------------------------------------------------------
# Tags TTS
# ---------------------------------------------------------------------------

def extract_leading_tag(text: str) -> str | None:
    match = re.match(r"^\[(.+?)\]\s*", text.strip())
    return match.group(1).strip() if match else None


def remove_leading_tag(text: str) -> str:
    return re.sub(r"^\[(.+?)\]\s*", "", text.strip(), count=1)


def count_tags(text: str) -> int:
    return len(re.findall(r"\[[^\]]+\]", text))


def allowed_tags_for_speaker(speaker: str, spec: dict) -> set[str]:
    return set(spec["speakers"][speaker]["allowed_tags"])


# ---------------------------------------------------------------------------
# Secciones
# ---------------------------------------------------------------------------

def section_title(line: str) -> str | None:
    stripped = line.strip()
    if stripped.startswith("# "):
        candidate = stripped[2:].strip().upper()
        # Excluye líneas que empiezan con "# VERIFICACION" (comentarios de verificación)
        if candidate and not candidate.startswith("VERIFICACI"):
            return candidate
    return None


def extract_sections(text: str) -> list[str]:
    return [section_title(line) for line in text.splitlines() if section_title(line)]


# ---------------------------------------------------------------------------
# Parsing de bloques hablados
# ---------------------------------------------------------------------------

def parse_script_blocks(text: str, spec: dict) -> list[dict]:
    blocks: list[dict] = []
    current_section: str | None = None
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        title = section_title(raw_line)
        if title:
            current_section = title
            continue
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        speaker_raw, content = line.split(":", 1)
        try:
            speaker = normalize_speaker(speaker_raw, spec)
        except ValueError:
            continue
        blocks.append({
            "speaker": speaker,
            "text": content.strip(),
            "line_number": line_number,
            "section": current_section,
        })
    for index, block in enumerate(blocks, start=1):
        block["index"] = index
    return blocks


# ---------------------------------------------------------------------------
# Estadísticas de guion
# ---------------------------------------------------------------------------

def build_script_stats(text: str, spec: dict, concepts: list[str] | None = None) -> dict:
    blocks = parse_script_blocks(text, spec)
    sections = extract_sections(text)
    word_counts = [count_words(remove_leading_tag(b["text"])) for b in blocks]
    sent_counts = [sentence_count(b["text"]) for b in blocks]
    rules = spec["script_rules"]
    short_threshold = rules.get("reaction_word_limit", 12)
    long_threshold = rules.get("target_avg_words_per_intervention_max", 100)
    short_count = sum(1 for w in word_counts if w <= short_threshold)
    long_count  = sum(1 for w in word_counts if w > long_threshold)
    total = len(blocks) or 1
    concept_mentions = {
        concept: count_concept_mentions(text, concept)
        for concept in (concepts or [])
    }
    return {
        "blocks": blocks,
        "sections": sections,
        "word_count_total": sum(word_counts),
        "avg_words_per_intervention": (sum(word_counts) / len(word_counts)) if word_counts else 0.0,
        "max_words_per_intervention": max(word_counts) if word_counts else 0,
        "min_words_per_intervention": min(word_counts) if word_counts else 0,
        "long_percentage": (long_count * 100.0) / total,
        "short_percentage": (short_count * 100.0) / total,
        "sentence_counts": sent_counts,
        "concept_mentions": concept_mentions,
    }


# ---------------------------------------------------------------------------
# Extracción de conceptos del PDF
# ---------------------------------------------------------------------------

def extract_theme_concepts(pdf_text: str, limit: int = 10) -> list[str]:
    lines = [line.strip() for line in pdf_text.splitlines() if line.strip()]
    candidates: list[str] = []
    for line in lines:
        normalized = normalize_text_for_match(line)
        if " vs " in normalized:
            for part in re.split(r"\bvs\b", line, flags=re.IGNORECASE):
                part = part.strip(" .,:;()-")
                if 3 <= len(part.split()) <= 6:
                    candidates.append(part)
        for match in re.finditer(r"\b[A-Z]{2,10}\b", line):
            candidates.append(match.group(0))
        for match in re.finditer(
            r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]+(?:\s+[a-zA-ZáéíóúÁÉÍÓÚñÑ]+){0,2}\b", line
        ):
            phrase = match.group(0).strip()
            if 1 <= len(phrase.split()) <= 3 and len(phrase) > 5:
                candidates.append(phrase)
    stop_phrases = {
        "modulo", "master", "introduccion", "bloque", "contexto",
        "relevancia", "tema", "objetivo", "profesional", "empresa",
    }
    scored: dict[str, int] = {}
    for candidate in candidates:
        normalized = normalize_text_for_match(candidate)
        normalized = re.sub(r"[^a-z0-9áéíóúüñ\s-]", "", normalized).strip()
        if not normalized or normalized in stop_phrases:
            continue
        if len(normalized.split()) > 4 or count_words(normalized) == 0:
            continue
        scored[normalized] = scored.get(normalized, 0) + 1
    ranked = sorted(scored.items(), key=lambda x: (-x[1], -len(x[0]), x[0]))
    return [c for c, _ in ranked[:limit]]


def concept_aliases(concept: str) -> list[str]:
    normalized = normalize_text_for_match(concept)
    aliases = {normalized}
    if ":" in normalized:
        left, right = [p.strip() for p in normalized.split(":", 1)]
        if left:
            aliases.add(left)
        if right:
            aliases.add(right)
    return [
        re.sub(r"\s+", " ", re.sub(r"[^a-z0-9áéíóúüñ\s-]", " ", a)).strip()
        for a in aliases
        if a and len(a.split()) <= 5
    ]


def count_concept_mentions(script_text: str, concept: str) -> int:
    normalized_script = normalize_text_for_match(script_text)
    counts = []
    for alias in concept_aliases(concept):
        if not alias:
            continue
        pattern = r"\b" + re.escape(alias) + r"\b"
        counts.append(len(re.findall(pattern, normalized_script)))
    return max(counts, default=0)


# ---------------------------------------------------------------------------
# Validación de blacklist de interjecciones
# ---------------------------------------------------------------------------

def check_blacklist_interjections(text: str, spec: dict) -> list[str]:
    """Devuelve lista de interjecciones de la blacklist encontradas en el texto hablado.

    Se considera interjección si la frase aparece como intervención corta
    (<= 15 palabras en el bloque completo) O como inicio de intervención.
    """
    blacklist = spec["script_rules"].get("blacklist_validation_interjections", [])
    if not blacklist:
        return []

    blocks = parse_script_blocks(text, spec)
    found: list[str] = []
    for block in blocks:
        plain = normalize_text_for_match(remove_leading_tag(block["text"]))
        word_count = count_words(plain)
        for phrase in blacklist:
            phrase_norm = normalize_text_for_match(phrase)
            # Solo cuenta como interjección si el bloque es corto o empieza con la frase
            if phrase_norm in plain and (word_count <= 15 or plain.startswith(phrase_norm)):
                if phrase not in found:
                    found.append(phrase)
    return found


# ---------------------------------------------------------------------------
# Validación principal del guion
# ---------------------------------------------------------------------------

def validate_script_text(
    text: str,
    ep_code: str,
    spec: dict,
    concepts: list[str] | None = None,
) -> list[str]:
    """Valida el guion contra el spec.

    Devuelve lista de issues. Lista vacía = válido.
    Separación hard/soft según el spec:
      - issues que son hard-fail van directamente en la lista
      - issues soft-warn llevan el prefijo [WARN]
    """
    issues: list[str] = []
    rules = spec["script_rules"]
    sections = extract_sections(text)

    # ── 1. Secciones obligatorias (orden y presencia) ──────────────────────
    last_position = -1
    for section in rules["required_sections"]:
        try:
            position = sections.index(section)
        except ValueError:
            issues.append(f"Falta la seccion obligatoria: #{section}.")
            continue
        if position <= last_position:
            issues.append(f"La seccion #{section} esta fuera de orden.")
        last_position = position

    # ── 2. Secciones prohibidas (hard-fail) ────────────────────────────────
    if rules.get("qa_rules" if "qa_rules" in spec else "_", {}).get(
        "hard_fail_on_forbidden_section", True
    ) or spec.get("qa_rules", {}).get("hard_fail_on_forbidden_section", True):
        for section in rules.get("forbidden_sections", []):
            if section in sections:
                issues.append(f"Seccion prohibida encontrada: #{section}.")

    # ── 3. Bloques hablados ─────────────────────────────────────────────────
    blocks = parse_script_blocks(text, spec)
    if not blocks:
        issues.append("El guion no contiene bloques hablados.")
        return issues

    # ── 4. Speaker de apertura ──────────────────────────────────────────────
    expected_opening = opening_speaker(ep_code, spec)
    if blocks[0]["speaker"] != expected_opening:
        issues.append(
            f"El episodio {ep_code} debe abrirlo {expected_opening}, "
            f"pero abre {blocks[0]['speaker']}."
        )

    # ── 5. Anti-pingpong (máx consecutivos del mismo speaker) ──────────────
    max_consec = rules.get("max_consecutive_blocks_same_speaker", 2)
    consecutive = 1
    for current, nxt in zip(blocks, blocks[1:]):
        if current["speaker"] == nxt["speaker"]:
            consecutive += 1
            if consecutive > max_consec:
                issues.append(
                    "Demasiados bloques consecutivos del mismo speaker "
                    f"alrededor de la linea {nxt['line_number']}."
                )
                break
        else:
            consecutive = 1

    # ── 6. Etiquetas TTS ────────────────────────────────────────────────────
    for block in blocks:
        tag_count = count_tags(block["text"])
        if tag_count > 1:
            issues.append(f"El bloque {block['index']} tiene mas de una etiqueta TTS.")
        tag = extract_leading_tag(block["text"])
        if tag:
            allowed = allowed_tags_for_speaker(block["speaker"], spec)
            allowed_norm = {normalize_text_for_match(t) for t in allowed}
            if normalize_text_for_match(tag) not in allowed_norm:
                issues.append(
                    f"Etiqueta '{tag}' no permitida para {block['speaker']} "
                    f"en bloque {block['index']}."
                )

    # ── 7. Frases fijas ─────────────────────────────────────────────────────
    if rules.get("hook_closing_phrase") and rules["hook_closing_phrase"] not in text:
        issues.append("Falta la frase fija de cierre del hook.")
    if rules.get("final_closing_phrase") and rules["final_closing_phrase"] not in text:
        issues.append("Falta la frase fija de cierre final.")
    if rules.get("concepts_closing_phrase") and rules["concepts_closing_phrase"] not in text:
        issues.append("Falta la apertura fija del cierre de conceptos.")
    if rules.get("intro_comment") and rules["intro_comment"] not in text:
        issues.append("Falta la instruccion de intro de sonido.")

    # ── 8. Aviso de IA (keywords obligatorias) ──────────────────────────────
    spoken_text = " ".join(remove_leading_tag(b["text"]) for b in blocks)
    normalized_spoken = normalize_text_for_match(spoken_text)
    normalized_full = normalize_text_for_match(text)

    required_kws = rules.get("warning_phrase_keywords_required", [])
    for kw in required_kws:
        if normalize_text_for_match(kw) not in normalized_full:
            issues.append(f"Falta keyword obligatoria del aviso de IA: '{kw}'.")

    soft_kws = rules.get("warning_phrase_keywords_softcheck", [])
    soft_kw_found = any(
        normalize_text_for_match(kw) in normalized_full for kw in soft_kws
    )
    if soft_kws and not soft_kw_found:
        issues.append("[WARN] El aviso de IA no contiene ninguna frase de enganche recomendada.")

    # ── 9. "Iago" en lugar de "Yago" ────────────────────────────────────────
    if "iago" in normalized_spoken:
        issues.append("El texto hablado contiene 'Iago' (debe usarse 'Yago').")

    # ── 10. Palabras totales ─────────────────────────────────────────────────
    stats = build_script_stats(text, spec, concepts)
    min_words = rules.get("minimum_word_count", 0)
    max_words = rules.get("maximum_word_count", 99999)
    if min_words and stats["word_count_total"] < min_words:
        issues.append(
            f"El guion tiene {stats['word_count_total']} palabras "
            f"(minimo: {min_words})."
        )
    if max_words and stats["word_count_total"] > max_words:
        issues.append(
            f"[WARN] El guion tiene {stats['word_count_total']} palabras "
            f"(maximo recomendado: {max_words})."
        )

    # ── 11. Frases por intervención en bloques de desarrollo ─────────────────
    min_sents = rules.get("minimum_sentences_per_intervention", 2)
    max_sents = rules.get("maximum_sentences_per_intervention", 10)
    dev_sections = set(rules.get("required_sections", [])) - {
        "HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
        "CIERRE_CONCEPTOS", "CIERRE_FINAL", "VERIFICACIONES",
    }
    for count_val, block in zip(stats["sentence_counts"], blocks):
        if block.get("section") not in dev_sections:
            continue
        if count_val < min_sents:
            issues.append(
                f"[WARN] Bloque {block['index']} ({block['section']}) "
                f"tiene solo {count_val} frase(s) (minimo: {min_sents})."
            )
        elif count_val > max_sents:
            issues.append(
                f"[WARN] Bloque {block['index']} ({block['section']}) "
                f"tiene {count_val} frases (maximo: {max_sents})."
            )

    # ── 12. Media de palabras por intervención ───────────────────────────────
    avg_min = rules.get("target_avg_words_per_intervention_min", 0)
    if avg_min and stats["avg_words_per_intervention"] < avg_min:
        issues.append(
            f"[WARN] Media de palabras por intervencion demasiado baja: "
            f"{stats['avg_words_per_intervention']:.1f} (minimo: {avg_min})."
        )

    # ── 13. Blacklist de interjecciones (hard-fail) ──────────────────────────
    blacklisted = check_blacklist_interjections(text, spec)
    for phrase in blacklisted:
        issues.append(f"Interjeccion prohibida encontrada: '{phrase}'.")

    # ── 14. Cobertura de conceptos del PDF (soft-warn) ───────────────────────
    if concepts:
        min_coverage_pct = rules.get("minimum_pdf_coverage_percent", 0)
        coverage_hits = [
            c for c, mentions in stats["concept_mentions"].items() if mentions >= 1
        ]
        coverage_pct = int(round(len(coverage_hits) / max(len(concepts), 1) * 100))
        if min_coverage_pct and coverage_pct < min_coverage_pct:
            missing = [c for c in concepts if stats["concept_mentions"].get(c, 0) < 1]
            issues.append(
                f"[WARN] Cobertura de conceptos del PDF: {coverage_pct}% "
                f"(objetivo: {min_coverage_pct}%). "
                f"Sin mencionar: {', '.join(missing[:5])}."
            )

    return issues


# ---------------------------------------------------------------------------
# Nomenclatura de archivos
# ---------------------------------------------------------------------------

def guion_to_ep_code(guion_stem: str) -> str:
    """Convierte nombre de guion en código de episodio de audio.

    M0_TX_Nombre   →  M0_TX_E_Nombre   (T-type)
    M0_Nombre      →  M0_E_Nombre      (M-type)
    """
    m = re.match(r"^(M\d+)_TX_(.+)$", guion_stem, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_TX_E_{m.group(2)}"
    m = re.match(r"^(M\d+)_(.+)$", guion_stem, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_E_{m.group(2)}"
    return guion_stem


def ep_code_to_guion_stem(ep_code: str) -> str:
    """Inverso de guion_to_ep_code."""
    m = re.match(r"^(M\d+)_TX_E_(.+)$", ep_code, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_TX_{m.group(2)}"
    m = re.match(r"^(M\d+)_E_(.+)$", ep_code, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    return ep_code


def episode_type(guion_stem: str) -> str:
    """Devuelve 'T' para episodios TX, 'M' para episodios de módulo."""
    if re.match(r"^M\d+_TX_", guion_stem, re.IGNORECASE):
        return "T"
    return "M"

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
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas por defecto
# ---------------------------------------------------------------------------

DEFAULT_M_SPEC_PATH = Path("PODCAST_M_SPEC.md")
DEFAULT_T_SPEC_PATH = Path("PODCAST_T_SPEC.md")
DEFAULT_SPEC_PATH   = DEFAULT_M_SPEC_PATH   # alias de retrocompatibilidad

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


def tema_number(ep_code: str) -> int:
    """Extrae el número de tema de un ep_code T-type.

    M1_TX_E_T10_Nombre → 10
    M7_TX_E_T1_Titulos → 1
    """
    m = re.search(r"_T(\d+)(?:_|$)", ep_code, re.IGNORECASE)
    if not m:
        raise ValueError(f"No se pudo extraer número de tema de: {ep_code}")
    return int(m.group(1))


def opening_speaker(ep_code: str, spec: dict) -> str:
    """Devuelve MARIA o IAGO según paridad y tipo de episodio.

    T-type: paridad del número de TEMA.
      T impares → IAGO (Yago); T pares → MARIA.
    M-type: tabla explícita del spec (M0→MARIA, M1→IAGO, …).
      Fallback a paridad de módulo si no hay tabla.
    """
    spec_type = spec.get("spec_type", "M")

    if spec_type == "T":
        t_num = tema_number(ep_code)
        for speaker, cfg in spec["speakers"].items():
            if t_num % 2 == 1 and cfg.get("opens_odd_temas"):
                return speaker
            if t_num % 2 == 0 and cfg.get("opens_even_temas"):
                return speaker
        # fallback: impares=IAGO, pares=MARIA
        return "IAGO" if t_num % 2 == 1 else "MARIA"

    else:
        # M-type: explicit_table primero
        parity = spec.get("parity_rules", {})
        explicit_table = parity.get("explicit_table", {})
        mod_num = episode_number(ep_code)
        key = f"M{mod_num}"
        if key in explicit_table:
            val = explicit_table[key].lower()
            if val in ("yago", "iago"):
                return "IAGO"
            if val == "maria":
                return "MARIA"
        # fallback: flags en speakers
        for speaker, cfg in spec["speakers"].items():
            if mod_num % 2 == 0 and cfg.get("opens_even_modules"):
                return speaker
            if mod_num % 2 == 1 and cfg.get("opens_odd_modules"):
                return speaker
        return "MARIA" if mod_num % 2 == 0 else "IAGO"


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
    # Solo reconoce "# PALABRA" (un hash + espacio), NO "## ..." (comentarios de verificacion)
    if stripped.startswith("# ") and not stripped.startswith("## "):
        candidate = stripped[2:].strip().upper()
        if candidate:
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
    # Exclude short reaction blocks from average so the metric reflects development blocks only
    dev_word_counts = [w for w in word_counts if w > short_threshold]
    avg_dev = (sum(dev_word_counts) / len(dev_word_counts)) if dev_word_counts else 0.0
    return {
        "blocks": blocks,
        "sections": sections,
        "word_count_total": sum(word_counts),
        "avg_words_per_intervention": avg_dev,
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
# Validaciones v3: líder, compartido, aviso, conceptos, glosario, tokens
# ---------------------------------------------------------------------------

def validate_leader_share(blocks: list[dict], spec: dict) -> list[str]:
    """Valida que el líder de cada bloque líder tenga >= leader_share_min_percent%.

    Hard-fail si qa_rules.hard_fail_on_leader_share_below_min=true.
    BLOQUE_REALIDAD tiene threshold especial de 60% (leader_share_min_percent_realidad).
    """
    issues: list[str] = []
    rules = spec["script_rules"]
    qa = spec.get("qa_rules", {})
    hard = qa.get("hard_fail_on_leader_share_below_min", False)
    prefix = "" if hard else "[WARN] "
    default_min_pct = rules.get("leader_share_min_percent", 65)
    # Threshold especial para BLOQUE_REALIDAD (T-type, MARIA voz experta empresa)
    realidad_min_pct = qa.get("leader_share_min_percent_realidad", rules.get("leader_share_min_percent_realidad", 60))

    # Construir mapa {sección: speaker_líder}
    leader_for_section: dict[str, str] = {}
    for speaker, cfg in spec["speakers"].items():
        for section in cfg.get("leads_blocks", []):
            leader_for_section[section] = speaker

    # Agrupar bloques por sección
    section_blocks: dict[str, list[dict]] = defaultdict(list)
    for block in blocks:
        if block.get("section"):
            section_blocks[block["section"]].append(block)

    for section, leader_speaker in leader_for_section.items():
        sec_blocks = section_blocks.get(section, [])
        if not sec_blocks:
            continue
        total_words = 0
        leader_words = 0
        for b in sec_blocks:
            wc = count_words(remove_leading_tag(b["text"]))
            total_words += wc
            if b["speaker"] == leader_speaker:
                leader_words += wc
        if total_words == 0:
            continue
        pct = (leader_words * 100.0) / total_words
        # Usar threshold específico para BLOQUE_REALIDAD
        min_pct = realidad_min_pct if section == "BLOQUE_REALIDAD" else default_min_pct
        if pct < min_pct:
            issues.append(
                f"{prefix}{section}: {leader_speaker} lidera pero solo tiene {pct:.0f}% "
                f"de palabras (minimo {min_pct}%)."
            )
    return issues


def validate_shared_block_balance(blocks: list[dict], spec: dict) -> list[str]:
    """Valida que en bloques compartidos cada speaker tenga 40-60% de palabras.

    Hard-fail si qa_rules.hard_fail_on_shared_block_balance=true.
    """
    issues: list[str] = []
    rules = spec["script_rules"]
    qa = spec.get("qa_rules", {})
    hard = qa.get("hard_fail_on_shared_block_balance", False)
    prefix = "" if hard else "[WARN] "
    bal_range = rules.get("shared_block_balance_range_percent", [40, 60])
    min_bal, max_bal = bal_range[0], bal_range[1]

    # Recoger secciones compartidas (deben aparecer en ambos speakers)
    shared_sections: set[str] = set()
    for cfg in spec["speakers"].values():
        for section in cfg.get("shares_blocks", []):
            shared_sections.add(section)

    # Agrupar bloques por sección
    section_blocks: dict[str, list[dict]] = defaultdict(list)
    for block in blocks:
        if block.get("section"):
            section_blocks[block["section"]].append(block)

    for section in shared_sections:
        sec_blocks = section_blocks.get(section, [])
        if not sec_blocks:
            continue
        speaker_words: dict[str, int] = defaultdict(int)
        for b in sec_blocks:
            wc = count_words(remove_leading_tag(b["text"]))
            speaker_words[b["speaker"]] += wc
        total = sum(speaker_words.values()) or 1
        for speaker, words in speaker_words.items():
            pct = (words * 100.0) / total
            pct_rounded = round(pct)
            if pct_rounded < min_bal or pct_rounded > max_bal:
                issues.append(
                    f"{prefix}{section} (compartido): {speaker} tiene {pct_rounded}% de palabras "
                    f"(rango permitido: {min_bal}%-{max_bal}%)."
                )
    return issues


def validate_aviso_speaker(text: str, ep_code: str, spec: dict) -> list[str]:
    """Valida que las keywords del aviso de IA las diga el opener del episodio.

    Hard-fail si warning_must_be_said_by_opener=true y lo dice el otro speaker.
    Busca en la sección SALUDO_Y_PRESENTACION.
    """
    issues: list[str] = []
    rules = spec["script_rules"]
    if not rules.get("warning_must_be_said_by_opener", False):
        return issues

    required_kws = rules.get("warning_phrase_keywords_required", [])
    if not required_kws:
        return issues

    opener = opening_speaker(ep_code, spec)
    blocks = parse_script_blocks(text, spec)

    # Solo comprobamos bloques dentro de SALUDO_Y_PRESENTACION
    saludo_blocks = [b for b in blocks if b.get("section") == "SALUDO_Y_PRESENTACION"]

    for block in saludo_blocks:
        block_norm = normalize_text_for_match(block["text"])
        kw_found = any(normalize_text_for_match(kw) in block_norm for kw in required_kws)
        if kw_found and block["speaker"] != opener:
            issues.append(
                f"El aviso de IA lo dice {block['speaker']} (bloque {block['index']}) "
                f"pero debe decirlo {opener}."
            )
    return issues


def validate_saludo_format(text: str, ep_code: str, spec: dict) -> list[str]:
    """Hard-fail si SALUDO_Y_PRESENTACION colapsa los dos nombres en una sola
    intervencion (ej: "Soy Maria. Y yo soy Yago.") o si falta el bloque
    separado del segundo speaker presentandose.
    """
    issues: list[str] = []
    qa = spec.get("qa_rules", {})
    if not qa.get("hard_fail_on_saludo_collapsed_single_block", False):
        return issues

    blocks = parse_script_blocks(text, spec)
    saludo_blocks = [b for b in blocks if b.get("section") == "SALUDO_Y_PRESENTACION"]
    if not saludo_blocks:
        return issues

    # Patron prohibido dentro de un mismo bloque (normalizando acentos)
    bad_patterns = [
        re.compile(r"\bsoy\s+maria\b.*\by\s+yo\s+soy\s+yago\b", re.IGNORECASE | re.DOTALL),
        re.compile(r"\bsoy\s+yago\b.*\by\s+yo\s+soy\s+maria\b", re.IGNORECASE | re.DOTALL),
        re.compile(r"\bsoy\s+iago\b.*\by\s+yo\s+soy\s+maria\b", re.IGNORECASE | re.DOTALL),
    ]
    for b in saludo_blocks:
        body_norm = normalize_text_for_match(b["text"])
        for pat in bad_patterns:
            if pat.search(body_norm):
                issues.append(
                    f"SALUDO colapsado en bloque {b['index']}: un mismo speaker "
                    f"contiene 'Soy X. Y yo soy Y.'. Debe ir en bloques separados."
                )
                break

    # Verifica que haya al menos 1 bloque por cada speaker en SALUDO
    speakers_in_saludo = {b["speaker"] for b in saludo_blocks}
    if len(saludo_blocks) >= 2 and len(speakers_in_saludo) < 2:
        issues.append(
            "SALUDO_Y_PRESENTACION solo tiene intervenciones de un speaker; "
            "se requiere al menos una de cada (IAGO y MARIA)."
        )
    return issues


def validate_no_surnames(text: str, spec: dict) -> list[str]:
    """Hard-fail si aparece "Maria Apellido" o "Yago Apellido" / "Iago Apellido"
    en texto hablado (los presentadores no tienen apellidos).
    """
    issues: list[str] = []
    qa = spec.get("qa_rules", {})
    if not qa.get("hard_fail_on_presenter_surname_invented", False):
        return issues
    blocks = parse_script_blocks(text, spec)
    spoken = " ".join(remove_leading_tag(b["text"]) for b in blocks)
    # Apellidos: nombre seguido por palabra con mayuscula inicial que no este en una lista corta
    # de palabras inofensivas (ej: "Maria que..." no, porque "que" es minuscula)
    pat = re.compile(
        r"\b(Maria|Yago|Iago)\s+([A-ZÁÉÍÓÚÑ][a-zñáéíóú]{2,})\b"
    )
    # Lista de palabras-stop que pueden seguir legitimamente (raras pero posibles)
    stopwords = {"En", "Y", "O", "Pero", "Si", "No", "Pues", "Que", "Cuando", "Donde", "Como", "Esto", "Eso"}
    for m in pat.finditer(spoken):
        name, follow = m.group(1), m.group(2)
        if follow in stopwords:
            continue
        issues.append(
            f"Apellido inventado detectado: '{name} {follow}'. Los presentadores "
            f"se llaman solo Maria y Yago, sin apellido."
        )
    return issues


def validate_concepts_count(blocks: list[dict], spec: dict) -> list[str]:
    """Valida el número de bloques hablados en CIERRE_CONCEPTOS.

    T-type: exactamente key_concepts_block_count_exact (= 3).
    M-type: entre key_concepts_block_count_min y key_concepts_block_count_max (3-5).
    """
    issues: list[str] = []
    rules = spec["script_rules"]

    cierre_blocks = [b for b in blocks if b.get("section") == "CIERRE_CONCEPTOS"]
    count = len(cierre_blocks)

    if "key_concepts_block_count_exact" in rules:
        exact = rules["key_concepts_block_count_exact"]
        if count != exact:
            issues.append(
                f"CIERRE_CONCEPTOS tiene {count} bloque(s) hablados; "
                f"se requieren exactamente {exact}."
            )
    else:
        min_c = rules.get("key_concepts_block_count_min", 3)
        max_c = rules.get("key_concepts_block_count_max", 5)
        if not (min_c <= count <= max_c):
            issues.append(
                f"CIERRE_CONCEPTOS tiene {count} bloque(s) hablados; "
                f"rango permitido: {min_c}-{max_c}."
            )
    return issues


def validate_glossary_present(spec: dict, base_dir: Path | None = None) -> list[str]:
    """Valida que exista el archivo de glosario unificado. Hard-fail si no existe."""
    issues: list[str] = []
    glossary_path_str = (
        spec.get("script_rules", {})
        .get("sources", {})
        .get("secondary", {})
        .get("glossary", {})
        .get("path", "PDFs/auxiliares/glosario_unificado.md")
    )
    base = base_dir or Path(".")
    glossary_path = base / glossary_path_str
    if not glossary_path.exists():
        issues.append(
            f"Glosario no encontrado: {glossary_path_str}. "
            "Hard-fail: el glosario es obligatorio (PDFs/auxiliares/glosario_unificado.md)."
        )
    return issues


def validate_input_tokens(text: str, spec: dict) -> list[str]:
    """Valida que VERIFICACIONES reporte input_tokens > 0.

    Hard-fail si qa_rules.hard_fail_on_zero_input_tokens = true.
    """
    issues: list[str] = []
    qa = spec.get("qa_rules", {})
    if not qa.get("hard_fail_on_zero_input_tokens", False):
        return issues

    m = re.search(r"input_tokens[:\s=]+(\d+)", text, re.IGNORECASE)
    if not m:
        issues.append("VERIFICACIONES no reporta input_tokens (debe ser > 0).")
    elif int(m.group(1)) == 0:
        issues.append(
            "VERIFICACIONES reporta input_tokens=0. "
            "Hard-fail: el generador debe leer el PDF fuente."
        )
    return issues


def validate_pdf_coverage(text: str, spec: dict, concepts: list[str]) -> list[str]:
    """Valida cobertura minima de conceptos del PDF. Hard-fail si < 75%."""
    issues: list[str] = []
    if not concepts:
        return issues
    rules = spec["script_rules"]
    min_coverage_pct = rules.get("minimum_pdf_coverage_percent", 0)
    if not min_coverage_pct:
        return issues
    qa = spec.get("qa_rules", {})
    hard_fail = qa.get("hard_fail_on_pdf_coverage_below_75", False)

    concept_mentions = {
        c: count_concept_mentions(text, c) for c in concepts
    }
    coverage_hits = [c for c, n in concept_mentions.items() if n >= 1]
    coverage_pct = int(round(len(coverage_hits) / max(len(concepts), 1) * 100))
    if coverage_pct < min_coverage_pct:
        missing = [c for c in concepts if concept_mentions.get(c, 0) < 1]
        prefix = "" if hard_fail else "[WARN] "
        issues.append(
            f"{prefix}Cobertura de conceptos del PDF: {coverage_pct}% "
            f"(minimo: {min_coverage_pct}%). "
            f"Sin mencionar: {', '.join(missing[:5])}."
        )
    return issues


# ---------------------------------------------------------------------------
# Validación principal del guion
# ---------------------------------------------------------------------------

def validate_script_text(
    text: str,
    ep_code: str,
    spec: dict,
    concepts: list[str] | None = None,
    base_dir: Path | None = None,
) -> list[str]:
    """Valida el guion contra el spec.

    Devuelve lista de issues. Lista vacía = válido.
    Issues hard-fail van directamente; soft-warn llevan prefijo [WARN].

    base_dir: directorio raíz del proyecto, para resolver rutas (glosario, etc.)
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
    if spec.get("qa_rules", {}).get("hard_fail_on_forbidden_section", True):
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
    for current, nxt in zip(blocks, blocks[1:], strict=False):
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

    # ── 7. Frases fijas (comparacion normalizada: sin acentos, lowercase) ──────
    norm_text = normalize_text_for_match(text)
    if rules.get("hook_closing_phrase") and normalize_text_for_match(rules["hook_closing_phrase"]) not in norm_text:
        issues.append("Falta la frase fija de cierre del hook.")
    if rules.get("final_closing_phrase") and normalize_text_for_match(rules["final_closing_phrase"]) not in norm_text:
        issues.append("Falta la frase fija de cierre final.")
    if rules.get("concepts_closing_phrase") and normalize_text_for_match(rules["concepts_closing_phrase"]) not in norm_text:
        issues.append("Falta la apertura fija del cierre de conceptos.")
    if rules.get("intro_comment") and normalize_text_for_match(rules["intro_comment"]) not in norm_text:
        issues.append("Falta la instruccion de intro de sonido.")

    # ── 8. Aviso de IA (keywords obligatorias presentes en el texto) ──────────
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

    # ── 9. Aviso dicho por el opener correcto ────────────────────────────────
    issues.extend(validate_aviso_speaker(text, ep_code, spec))

    # ── 9b. SALUDO con formato de 3 bloques separados ────────────────────────
    issues.extend(validate_saludo_format(text, ep_code, spec))

    # ── 9c. Sin apellidos inventados para los presentadores ──────────────────
    issues.extend(validate_no_surnames(text, spec))

    # ── 10. "Iago" en lugar de "Yago" ────────────────────────────────────────
    spoken_text = " ".join(remove_leading_tag(b["text"]) for b in blocks)
    normalized_spoken = normalize_text_for_match(spoken_text)
    if re.search(r"\biago\b", normalized_spoken):
        issues.append("El texto hablado contiene 'Iago' (debe usarse 'Yago').")

    # ── 11. Palabras totales ─────────────────────────────────────────────────
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

    # ── 12. Frases por intervención en bloques de desarrollo ─────────────────
    min_sents = rules.get("minimum_sentences_per_intervention", 2)
    max_sents = rules.get("maximum_sentences_per_intervention", 10)
    reaction_limit = rules.get("reaction_word_limit", 12)
    dev_sections = set(rules.get("required_sections", [])) - {
        "HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
        "CIERRE_CONCEPTOS", "CIERRE_FINAL", "VERIFICACIONES",
    }
    for count_val, block in zip(stats["sentence_counts"], blocks, strict=False):
        if block.get("section") not in dev_sections:
            continue
        # Bloques de reacción (≤ reaction_word_limit palabras) son transiciones
        # cortas intencionales; exentos del mínimo de frases.
        block_words = count_words(remove_leading_tag(block["text"]))
        if block_words <= reaction_limit:
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

    # ── 13. Media de palabras por intervención ───────────────────────────────
    avg_min = rules.get("target_avg_words_per_intervention_min", 0)
    if avg_min and stats["avg_words_per_intervention"] < avg_min:
        issues.append(
            f"[WARN] Media de palabras por intervencion demasiado baja: "
            f"{stats['avg_words_per_intervention']:.1f} (minimo: {avg_min})."
        )

    # ── 14. Blacklist de interjecciones (hard-fail) ──────────────────────────
    blacklisted = check_blacklist_interjections(text, spec)
    for phrase in blacklisted:
        issues.append(f"Interjeccion prohibida encontrada: '{phrase}'.")

    # ── 15. Cobertura de conceptos del PDF ───────────────────────────────────
    if concepts:
        issues.extend(validate_pdf_coverage(text, spec, concepts))

    # ── 16. Líder por bloque (hard-fail) ────────────────────────────────────
    if spec.get("qa_rules", {}).get("hard_fail_on_leader_share_below_min", False):
        issues.extend(validate_leader_share(blocks, spec))

    # ── 17. Balance de bloque compartido (hard-fail) ─────────────────────────
    issues.extend(validate_shared_block_balance(blocks, spec))

    # ── 18. Número de conceptos en CIERRE_CONCEPTOS (hard-fail) ──────────────
    if spec.get("qa_rules", {}).get(
        "hard_fail_on_concepts_count_not_exact_3",
        spec.get("qa_rules", {}).get("hard_fail_on_concepts_count_out_of_range", False),
    ):
        issues.extend(validate_concepts_count(blocks, spec))

    # ── 19. Glosario presente (hard-fail) ────────────────────────────────────
    if spec.get("qa_rules", {}).get("hard_fail_on_missing_glossary", False):
        issues.extend(validate_glossary_present(spec, base_dir))

    # ── 20. Input tokens > 0 (hard-fail) ─────────────────────────────────────
    issues.extend(validate_input_tokens(text, spec))

    # ── 21. Intervenciones demasiado largas (WARN — Audio-Regla 2) ────────────
    max_single = rules.get("target_max_words_per_single_intervention", 0)
    if max_single and spec.get("qa_rules", {}).get("soft_warn_on_intervention_over_200_words", False):
        for block in blocks:
            wc = count_words(remove_leading_tag(block["text"]))
            if wc > max_single:
                issues.append(
                    f"[WARN] Bloque {block['index']} ({block['section']}) tiene {wc} palabras "
                    f"(max recomendado por intervencion: {max_single}). "
                    "Riesgo de artefactos TTS a 1.32x velocidad."
                )

    # ── 22. Numeros en formato digito en dialogo (WARN — Audio-Regla 1) ───────
    if spec.get("qa_rules", {}).get("soft_warn_on_digit_numbers_in_dialogue", False):
        digit_patterns = [
            (re.compile(r"\b\d+[.,]\d+\s*%"), "porcentaje en digitos"),
            (re.compile(r"\$\s*\d+"), "cifra monetaria en digitos"),
            (re.compile(r"\b\d+[.,]?\d*\s*[MB](?:illones?)?\b"), "cifra grande en digitos"),
        ]
        spoken_lines = [remove_leading_tag(b["text"]) for b in blocks]
        for line, block in zip(spoken_lines, blocks, strict=False):
            for pattern, desc in digit_patterns:
                if pattern.search(line):
                    issues.append(
                        f"[WARN] Bloque {block['index']} ({block['section']}): {desc} en el dialogo. "
                        "A 1.32x velocidad el TTS puede pronunciarlo mal — escribir en palabras."
                    )
                    break  # solo un warn por bloque

    # ── 23. CTA en CIERRE_FINAL (solo M-type, WARN) ───────────────────────────
    spec_type = spec.get("spec_type", "M")
    if spec_type == "M" and spec.get("qa_rules", {}).get("soft_warn_on_missing_cta_in_cierre_final", False):
        cierre_final_blocks = [b for b in blocks if b.get("section") == "CIERRE_FINAL"]
        if cierre_final_blocks:
            cierre_text = " ".join(remove_leading_tag(b["text"]) for b in cierre_final_blocks)
            cta_pattern = re.compile(
                r"episodio[s]?.{0,30}(m[oó]dulo|disponible|plataforma|escucha)",
                re.IGNORECASE,
            )
            if not cta_pattern.search(cierre_text):
                issues.append(
                    "[WARN] CIERRE_FINAL (M-type) no contiene CTA a episodios T del modulo. "
                    "Agregar mencion natural: 'los episodios del modulo ya estan disponibles'."
                )

    # ── 24. WARN: media de palabras por intervencion demasiado alta ───────────
    avg_max = rules.get("target_avg_words_per_intervention_max", 0)
    if avg_max and stats["avg_words_per_intervention"] > avg_max:
        issues.append(
            f"[WARN] Media de palabras por intervencion demasiado alta: "
            f"{stats['avg_words_per_intervention']:.1f} (maximo recomendado: {avg_max})."
        )

    # ── 25. HARD: frases placeholder genéricas (contenido de relleno) ──────────
    placeholder_phrases = rules.get("blacklist_placeholder_phrases", [])
    for phrase in placeholder_phrases:
        if phrase.lower() in text.lower():
            issues.append(
                f"Frase placeholder detectada (contenido de relleno sin valor): '{phrase[:60]}...'"
            )

    # ── 26. WARN: lista enumerada en voz alta (Primero/Segundo/Tercero/Cuarto) ─
    enum_pattern = re.compile(
        r"(Primero|Primera)[,:].*?(Segundo|Segunda)[,:].*?(Tercero|Tercera)[,:]",
        re.IGNORECASE | re.DOTALL,
    )
    for blk in stats["blocks"]:
        blk_text = blk["text"]
        if enum_pattern.search(blk_text):
            issues.append(
                f"[WARN] Bloque {blk['index']} ({blk.get('section','?')}) usa lista enumerada "
                f"(Primero/Segundo/Tercero): distribuye los puntos entre ambos speakers."
            )

    return issues


# ---------------------------------------------------------------------------
# Nomenclatura de archivos
# ---------------------------------------------------------------------------

def guion_to_ep_code(guion_stem: str) -> str:
    """Convierte nombre de guion en código de episodio de audio.

    M0_T1_Nombre   →  M0_TX_E_T1_Nombre   (T-type, naming actual)
    M0_TX_Nombre   →  M0_TX_E_Nombre      (T-type, naming legacy)
    M0_Nombre      →  M0_E_Nombre         (M-type)
    """
    m = re.match(r"^(M\d+)_T(\d+)_(.+)$", guion_stem, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_TX_E_T{m.group(2)}_{m.group(3)}"
    m = re.match(r"^(M\d+)_TX_(.+)$", guion_stem, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_TX_E_{m.group(2)}"
    m = re.match(r"^(M\d+)_(.+)$", guion_stem, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_E_{m.group(2)}"
    return guion_stem


def ep_code_to_guion_stem(ep_code: str) -> str:
    """Inverso de guion_to_ep_code (devuelve siempre el naming actual M{n}_T{k}_)."""
    m = re.match(r"^(M\d+)_TX_E_T(\d+)_(.+)$", ep_code, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_T{m.group(2)}_{m.group(3)}"
    m = re.match(r"^(M\d+)_TX_E_(.+)$", ep_code, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_TX_{m.group(2)}"
    m = re.match(r"^(M\d+)_E_(.+)$", ep_code, re.IGNORECASE)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    return ep_code


def episode_type(guion_stem: str) -> str:
    """Devuelve 'T' para episodios de tema, 'M' para episodios de módulo.

    Reconoce el naming actual (M{n}_T{k}_slug) y el legacy (M{n}_TX_...).
    """
    if re.match(r"^M\d+_T\d+_", guion_stem, re.IGNORECASE):
        return "T"
    if re.match(r"^M\d+_TX_", guion_stem, re.IGNORECASE):
        return "T"
    return "M"

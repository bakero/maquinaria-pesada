from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


DEFAULT_SPEC_PATH = Path("PODCAST_MASTER_SPEC.md")
JSON_START_MARKER = "<!-- PODCAST_SPEC_JSON_START -->"
JSON_END_MARKER = "<!-- PODCAST_SPEC_JSON_END -->"

WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:[-'][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)?")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_master_spec(path: str | Path = DEFAULT_SPEC_PATH) -> dict:
    path = Path(path)
    text = read_text(path)
    pattern = (
        re.escape(JSON_START_MARKER)
        + r"\s*```json\s*(.*?)\s*```"
        + r"\s*"
        + re.escape(JSON_END_MARKER)
    )
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No se encontro el bloque JSON maestro en {path}")
    return json.loads(match.group(1))


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_text_for_match(value: str) -> str:
    return strip_accents(value).lower()


def normalize_speaker(value: str, spec: dict) -> str:
    clean = normalize_text_for_match(value.strip().upper())
    aliases = spec["script_rules"]["speaker_aliases"]
    for canonical, items in aliases.items():
        normalized_items = {normalize_text_for_match(item.upper()) for item in items}
        if clean in normalized_items:
            return canonical
    if value.strip().upper() in spec["speakers"]:
        return value.strip().upper()
    raise ValueError(f"Speaker no reconocido: {value}")


def episode_number(ep_code: str) -> int:
    match = re.search(r"(\d+)", ep_code)
    if not match:
        raise ValueError(f"No se pudo extraer numero de episodio de {ep_code}")
    return int(match.group(1))


def opening_speaker(ep_code: str, spec: dict) -> str:
    number = episode_number(ep_code)
    return "MARIA" if number % 2 == 0 else "IAGO"


def allowed_tags_for_speaker(speaker: str, spec: dict) -> set[str]:
    return set(spec["speakers"][speaker]["allowed_tags"])


def extract_leading_tag(text: str) -> str | None:
    match = re.match(r"^\[(.+?)\]\s*", text.strip())
    if not match:
        return None
    return match.group(1).strip()


def remove_leading_tag(text: str) -> str:
    return re.sub(r"^\[(.+?)\]\s*", "", text.strip(), count=1)


def count_tags(text: str) -> int:
    return len(re.findall(r"\[[^\]]+\]", text))


def section_title(line: str) -> str | None:
    stripped = line.strip()
    if stripped.startswith("# "):
        return stripped[2:].strip().upper()
    return None


_SENT_PLACEHOLDER = "\x01"


def sentence_count(text: str) -> int:
    plain = remove_leading_tag(text)
    # Sustituir temporalmente puntos que no son finales de frase para no romper el conteo:
    # 1. Numeros decimales: 4.6, 360.000, GPT-5.4
    plain = re.sub(
        r"(\d)\.(\d)",
        lambda m: m.group(1) + _SENT_PLACEHOLDER + m.group(2),
        plain,
    )
    # 2. Abreviaturas de letras sueltas: I.A., EE.UU., etc.
    plain = re.sub(
        r"\b([A-ZÁÉÍÓÚÜ])\.\s*([A-ZÁÉÍÓÚÜ]\.?)",
        lambda m: m.group().replace(".", _SENT_PLACEHOLDER),
        plain,
    )
    parts = [part.strip() for part in re.split(r"[.!?]+", plain) if part.strip()]
    return len(parts)


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def count_words_without_speakers(script_text: str) -> int:
    total = 0
    for block in parse_script_blocks(script_text, load_master_spec()):
        total += count_words(remove_leading_tag(block["text"]))
    return total


def parse_script_blocks(text: str, spec: dict) -> list[dict]:
    blocks: list[dict] = []
    current_section = None
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
        blocks.append(
            {
                "speaker": speaker,
                "text": content.strip(),
                "line_number": line_number,
                "section": current_section,
            }
        )
    for index, block in enumerate(blocks, start=1):
        block["index"] = index
    return blocks


def extract_sections(text: str) -> list[str]:
    sections: list[str] = []
    for line in text.splitlines():
        title = section_title(line)
        if title:
            sections.append(title)
    return sections


def extract_theme_concepts(pdf_text: str, limit: int = 10) -> list[str]:
    lines = [line.strip() for line in pdf_text.splitlines() if line.strip()]
    candidates: list[str] = []

    for line in lines:
        normalized = normalize_text_for_match(line)
        if line.startswith("BLOQUE "):
            title = line.split("·", 1)[-1].strip() if "·" in line else line
            candidates.append(title)
        if " vs " in normalized:
            for part in re.split(r"\bvs\b", line, flags=re.IGNORECASE):
                part = part.strip(" .,:;()-")
                if 3 <= len(part.split()) <= 6:
                    candidates.append(part)
        for match in re.finditer(r"\b[A-Z]{2,10}\b", line):
            candidates.append(match.group(0))
        for match in re.finditer(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]+(?:\s+[a-zA-ZáéíóúÁÉÍÓÚñÑ]+){0,2}\b", line):
            phrase = match.group(0).strip()
            if 1 <= len(phrase.split()) <= 3 and len(phrase) > 5:
                candidates.append(phrase)

    stop_phrases = {
        "modulo",
        "master",
        "introduccion",
        "bloque",
        "contexto",
        "relevancia",
        "tema",
        "objetivo",
        "profesional",
        "empresa"
    }

    scored: dict[str, int] = {}
    for candidate in candidates:
        normalized = normalize_text_for_match(candidate)
        normalized = re.sub(r"[^a-z0-9áéíóúüñ\s-]", "", normalized).strip()
        if not normalized or normalized in stop_phrases:
            continue
        if len(normalized.split()) > 4:
            continue
        if count_words(normalized) == 0:
            continue
        scored[normalized] = scored.get(normalized, 0) + 1

    ranked = sorted(scored.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [concept for concept, _ in ranked[:limit]]


def concept_aliases(concept: str) -> list[str]:
    normalized = normalize_text_for_match(concept)
    aliases = {normalized}
    if ":" in normalized:
        left, right = [part.strip() for part in normalized.split(":", 1)]
        if left:
            aliases.add(left)
        if right:
            aliases.add(right)
    replacements = {
        "adopcion de ia en organizaciones": ["adopcion de ia", "88% de las organizaciones"],
        "crecimiento del mercado global de": ["mercado global de ia", "200 000 millones", "35%"],
        "ia como motor de transformacion": ["motor de transformacion", "transformacion empresarial", "transformacion de la economia"],
        "historia de la ia": ["historia de la ia", "inviernos", "renacimientos"],
        "deep learning y redes neuronales": ["deep learning", "redes neuronales"],
        "transformers y large language models": ["transformers", "large language models", "llms"],
        "convergencia de poder computacional datos": ["poder computacional", "datos", "arquitectura"],
        "poder computacional disponibilidad de datos": ["poder computacional", "disponibilidad de datos", "potencia de calculo", "datos utiles"],
        "limitaciones actuales de llms": ["alucinan", "sesgos", "memoria persistente", "llms"],
        "capacidades actuales de llms": ["capacidades actuales de los llms", "los llms pueden", "modelos de lenguaje de gran tamaño", "generar contenido", "analizar documentos"],
        "distincion entre ia estrecha e": ["ia estrecha", "ia general", "artificial narrow intelligence", "artificial general intelligence"],
        "diferencia entre ia discriminativa e": ["ia discriminativa", "ia generativa", "clasifica y predice", "crea contenido"],
        "transformers y llms desde 2017-2020": ["transformers", "llms", "desde 2017", "desde 2020", "large language models"]
    }
    for key, extra_aliases in replacements.items():
        if key in normalized:
            aliases.update(extra_aliases)
    filtered = []
    for alias in aliases:
        alias = re.sub(r"[^a-z0-9áéíóúüñ\s-]", " ", alias)
        alias = re.sub(r"\s+", " ", alias).strip()
        if alias and len(alias.split()) <= 5:
            filtered.append(alias)
    return list(dict.fromkeys(filtered))


def count_concept_mentions(script_text: str, concept: str) -> int:
    normalized_script = normalize_text_for_match(script_text)
    counts = []
    for alias in concept_aliases(concept):
        pattern = r"\b" + re.escape(alias) + r"\b"
        counts.append(len(re.findall(pattern, normalized_script)))
    return max(counts, default=0)


def build_script_stats(text: str, spec: dict, concepts: list[str] | None = None) -> dict:
    blocks = parse_script_blocks(text, spec)
    sections = extract_sections(text)
    content_blocks = [section for section in sections if section.startswith(spec["script_rules"]["content_block_prefix"])]
    insertions = [section for section in sections if section.startswith(spec["script_rules"]["insertion_prefix"])]
    word_counts = [count_words(remove_leading_tag(block["text"])) for block in blocks]
    sentence_counts = [sentence_count(block["text"]) for block in blocks]
    short_count = sum(1 for value in word_counts if value <= spec["script_rules"]["short_intervention_threshold"])
    long_count = sum(1 for value in word_counts if value > spec["script_rules"]["long_intervention_threshold"])
    total_blocks = len(blocks) or 1
    concept_mentions = {
        concept: count_concept_mentions(text, concept)
        for concept in (concepts or [])
    }
    return {
        "blocks": blocks,
        "sections": sections,
        "content_blocks": content_blocks,
        "insertions": insertions,
        "word_count_total": sum(word_counts),
        "avg_words_per_intervention": (sum(word_counts) / len(word_counts)) if word_counts else 0.0,
        "max_words_per_intervention": max(word_counts) if word_counts else 0,
        "min_words_per_intervention": min(word_counts) if word_counts else 0,
        "long_percentage": (long_count * 100.0) / total_blocks,
        "short_percentage": (short_count * 100.0) / total_blocks,
        "sentence_counts": sentence_counts,
        "concept_mentions": concept_mentions,
    }


def validate_script_text(text: str, ep_code: str, spec: dict, concepts: list[str] | None = None) -> list[str]:
    issues: list[str] = []
    rules = spec["script_rules"]
    sections = extract_sections(text)

    last_position = -1
    for section in rules["required_sections"]:
        try:
            position = sections.index(section)
        except ValueError:
            issues.append(f"Falta la seccion obligatoria #{section}.")
            continue
        if position <= last_position:
            issues.append(f"La seccion #{section} esta fuera de orden.")
        last_position = position

    blocks = parse_script_blocks(text, spec)
    if not blocks:
        issues.append("El guion no contiene bloques hablados.")
        return issues

    expected_opening = opening_speaker(ep_code, spec)
    if blocks[0]["speaker"] != expected_opening:
        issues.append(
            f"El episodio {ep_code} debe abrirlo {expected_opening}, pero abre {blocks[0]['speaker']}."
        )

    content_sections = [section for section in sections if section.startswith(rules["content_block_prefix"])]
    if len(content_sections) < rules["minimum_content_blocks"]:
        issues.append("El guion tiene menos de 4 bloques de contenido.")
    if len(content_sections) > rules["maximum_content_blocks"]:
        issues.append("El guion tiene mas de 6 bloques de contenido.")

    insertion_sections = [section for section in sections if section.startswith(rules["insertion_prefix"])]
    min_insertions = max(1, len(content_sections) // 2)
    if len(insertion_sections) < min_insertions:
        issues.append(
            f"Faltan inserciones de noticia o ejemplo: {len(insertion_sections)}/{min_insertions}."
        )

    consecutive = 1
    for current, nxt in zip(blocks, blocks[1:]):
        if current["speaker"] == nxt["speaker"]:
            consecutive += 1
            if consecutive > rules["max_consecutive_blocks_same_speaker"]:
                issues.append(
                    "Hay demasiados bloques consecutivos del mismo speaker "
                    f"alrededor de la linea {nxt['line_number']}."
                )
                break
        else:
            consecutive = 1

    for block in blocks:
        tag_count = count_tags(block["text"])
        if tag_count > 1:
            issues.append(f"El bloque {block['index']} tiene mas de una etiqueta.")
        tag = extract_leading_tag(block["text"])
        if tag is None and tag_count > 0:
            issues.append(f"El bloque {block['index']} tiene etiqueta fuera del inicio.")
        if tag:
            allowed = allowed_tags_for_speaker(block["speaker"], spec)
            allowed_norm = {normalize_text_for_match(t) for t in allowed}
            if normalize_text_for_match(tag) not in allowed_norm:
                issues.append(
                    f"La etiqueta '{tag}' no esta permitida para {block['speaker']} en el bloque {block['index']}."
                )

    if rules["hook_closing_phrase"] not in text:
        issues.append("Falta la frase fija de cierre del hook.")
    if rules["final_closing_phrase"] not in text:
        issues.append("Falta la frase fija de cierre final.")
    if rules["concepts_closing_phrase"] not in text:
        issues.append("Falta la apertura fija del cierre de conceptos.")
    if rules["intro_comment"] not in text:
        issues.append("Falta la instruccion de intro de sonido.")

    spoken_text = " ".join(remove_leading_tag(block["text"]) for block in blocks)
    normalized_spoken_text = normalize_text_for_match(spoken_text)
    if "iago" in normalized_spoken_text:
        issues.append("El texto hablado contiene 'Iago' y debe usar 'Yago'.")

    stats = build_script_stats(text, spec, concepts)
    if stats["word_count_total"] < rules["minimum_word_count"]:
        issues.append(
            f"El guion tiene {stats['word_count_total']} palabras y debe superar {rules['minimum_word_count']}."
        )

    for index, (count_value, block) in enumerate(zip(stats["sentence_counts"], blocks), start=1):
        is_development = (block.get("section") or "").startswith(rules["content_block_prefix"]) or (block.get("section") or "").startswith(rules["insertion_prefix"])
        if not is_development:
            continue
        if count_value < rules["minimum_sentences_per_intervention"]:
            issues.append(f"El bloque {index} tiene menos de 2 frases.")
            break
        if count_value > rules["maximum_sentences_per_intervention"]:
            issues.append(f"El bloque {index} tiene mas de 6 frases.")
            break

    if stats["avg_words_per_intervention"] < rules["target_avg_words_per_intervention_min"]:
        issues.append("La media de palabras por intervencion es demasiado baja.")
    if stats["long_percentage"] > rules["maximum_long_intervention_percentage"]:
        issues.append("Hay demasiadas intervenciones largas.")

    if concepts:
        minimum_mentions = rules["minimum_concept_mentions"]
        missing = [
            concept
            for concept, mentions in stats["concept_mentions"].items()
            if mentions < minimum_mentions
        ]
        if missing:
            issues.append(
                "Algunos conceptos clave del PDF no aparecen al menos dos veces: "
                + ", ".join(missing[:8])
            )

    return issues


def next_episode_code(scripts_dir: str | Path) -> str:
    scripts_dir = Path(scripts_dir)
    used_numbers: list[int] = []
    for path in scripts_dir.glob("M*_T_*.txt"):
        match = re.search(r"M(\d+)_T_", path.name)
        if match:
            used_numbers.append(int(match.group(1)))
    next_number = max(used_numbers, default=0) + 1
    return f"M{next_number}_T_"

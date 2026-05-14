#!/usr/bin/env python3
"""
guion_common.py — Núcleo compartido de generación de guiones (M y T).

Los episodios se generan ÚNICAMENTE con dos entry points:
  - generar_guion.py    → episodios M (módulos)   — PODCAST_M_SPEC.md
  - generar_guion_t.py  → episodios T (temas)     — PODCAST_T_SPEC.md

Ambos importan de aquí toda la lógica común: cliente Anthropic, extracción de
PDF, normalización y post-procesado mecánico del guion (anti-pingpong, split de
bloques largos, rebalanceo, frases fijas, números a palabras…).

La validación vive en `podcast_spec.py`; las reglas (blacklist, frases fijas,
marcadores temporales) viven en los SPEC JSON. Ver `GENERACION.md`.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

from podcast_spec import extract_leading_tag, normalize_text_for_match, remove_leading_tag

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


def call_claude(
    client, model: str, system: str, user: str,
    max_tokens: int, temperature: float, source: str = "generar_guion.py",
) -> tuple[str, object]:
    """Llama a Claude y devuelve (content_text, response).

    `source` identifica el script llamante en el tracker de uso de tokens.
    """
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
            response, model=model, source=source, kind="generation",
            latency_ms=int((_t.monotonic() - _t0) * 1000),
        )
    except ImportError:
        pass
    return response.content[0].text, response


# ---------------------------------------------------------------------------
# Números en dígitos → palabras (audio-regla 1)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Anti-pingpong
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# CIERRE_CONCEPTOS — recorte al número de bloques permitido
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Rebalanceo del bloque compartido
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# CTA en CIERRE_FINAL (M-type)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Split de bloques demasiado largos
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Normalización de tags TTS y nombres de speaker
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Frases fijas del spec
# ---------------------------------------------------------------------------

def enforce_fixed_phrases(text: str, spec: dict) -> str:
    """Inyecta frases fijas del spec si el modelo no las incluyo exactamente.

    Opera sobre el cuerpo del guion (sin bloque de verificaciones).
    Preserva la etiqueta TTS del bloque si existe.
    """
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


__all__ = [
    "TokenUsage",
    "extract_pdf_text",
    "make_anthropic_client",
    "call_claude",
    "extract_leading_tag",
    "remove_leading_tag",
    "normalize_text_for_match",
    "_fix_digit_numbers_in_dialogue",
    "_fix_antipingpong",
    "_trim_cierre_conceptos_if_excess",
    "_rebalance_shared_block",
    "_inject_cta_if_missing",
    "_split_oversized_blocks",
    "_split_oversized_sentence_blocks",
    "_fix_tts_closing_tags",
    "_fix_gendered_tags",
    "_remove_blacklisted_opening",
    "normalize_generated_script",
    "strip_verification_block",
    "enforce_fixed_phrases",
]

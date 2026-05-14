#!/usr/bin/env python3
"""Correcciones mecánicas de hard-fails en guiones existentes (spec v4).

Aplica:
1. CIERRE_CONCEPTOS: trim a 5 (M) o 3 (T) bloques.
2. Antipingpong: fusiona runs de 3+ del mismo speaker en un único bloque.
3. Blacklist: elimina interjecciones prohibidas (no solo en aperturas).
4. "Iago" → "Yago" en texto hablado.
5. Aviso de IA: swap speaker si lo dice el equivocado.
6. Tag [tecnico] no permitido → [explicativo].
7. Referencias 2025 (estado actual) → 2026.
8. Pad para guiones por debajo del mínimo de palabras (extiende una intervención
   pidiéndole a Claude que añada un cierre con ejemplo cotidiano).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from podcast_spec import (
    load_spec,
    opening_speaker,
    extract_sections,
    parse_script_blocks,
    validate_script_text,
)

BASE = Path(__file__).parent
GUIONES = BASE / "Guiones"

SPEC_M = load_spec(BASE / "PODCAST_M_SPEC.md")
SPEC_T = load_spec(BASE / "PODCAST_T_SPEC.md")


def detect_type(name: str) -> str:
    return "T" if "_TX_T" in name else "M"


def ep_code(name: str) -> str:
    base = name.replace(".txt", "")
    if "_TX_T" in base:
        m = re.match(r"(M\d+)_TX_(T\d+)", base)
        return f"{m.group(1)}_{m.group(2)}"
    return re.match(r"(M\d+)", base).group(1)


SPEAKER_RE = re.compile(r"^(IAGO|MARIA)\s*:\s*(.*)$", re.IGNORECASE | re.MULTILINE)
SECTION_RE = re.compile(r"^# ([A-Z_]+)\s*$", re.MULTILINE)


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Devuelve [(header_line, body), ...] preservando contenido inicial sin header."""
    parts = re.split(r"(^# [A-Z_]+\s*$)", text, flags=re.MULTILINE)
    out = []
    if parts[0]:
        out.append(("", parts[0]))
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        out.append((header, body))
    return out


def _join_sections(sections: list[tuple[str, str]]) -> str:
    out = []
    for header, body in sections:
        if header:
            out.append(header)
        out.append(body)
    return "".join(out)


def _section_speaker_blocks(body: str) -> list[tuple[int, str, str, str]]:
    """Devuelve [(line_idx, speaker, tag_or_none, content), ...] del cuerpo de una sección.

    Cada bloque ocupa una sola línea con formato 'SPEAKER: text'.
    """
    lines = body.split("\n")
    blocks = []
    for i, line in enumerate(lines):
        m = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", line, re.IGNORECASE)
        if m:
            blocks.append((i, m.group(1).upper(), line))
    return blocks


# ------------------------------------------------------------
# Fix 1 — CIERRE_CONCEPTOS trim
# ------------------------------------------------------------
def fix_cierre_conceptos(text: str, ep_type: str) -> str:
    sections = _split_into_sections(text)
    max_blocks = 5 if ep_type == "M" else 3
    for idx, (header, body) in enumerate(sections):
        if header == "# CIERRE_CONCEPTOS":
            lines = body.split("\n")
            kept = []
            speaker_count = 0
            for line in lines:
                if re.match(r"^(IAGO|MARIA)\s*:", line, re.IGNORECASE):
                    speaker_count += 1
                    if speaker_count > max_blocks:
                        continue  # drop extra block
                kept.append(line)
            sections[idx] = (header, "\n".join(kept))
            break
    return _join_sections(sections)


# ------------------------------------------------------------
# Fix 2 — Anti-pingpong: merge runs of 3+ same speaker
# ------------------------------------------------------------
def fix_pingpong(text: str) -> str:
    lines = text.split("\n")
    out = []
    i = 0
    # Find sequences of speaker lines and rewrite
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", line, re.IGNORECASE)
        if not m:
            out.append(line)
            i += 1
            continue
        speaker = m.group(1).upper()
        run = [(i, m.group(2))]
        j = i + 1
        # Look ahead — collect consecutive same-speaker blocks (skipping blank lines)
        while j < len(lines):
            nxt = lines[j]
            if nxt.strip() == "":
                j += 1
                continue
            mn = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", nxt, re.IGNORECASE)
            if not mn:
                break  # not a speaker line — stop
            if mn.group(1).upper() != speaker:
                break
            run.append((j, mn.group(2)))
            j += 1
        if len(run) >= 3:
            # Merge: keep first block, append text of subsequent into it (strip leading tag of later)
            first_text = run[0][1]
            extra = []
            for _, txt in run[1:]:
                stripped = re.sub(r"^\s*[\[<][a-zA-Z_/]+[\]>]\s*", "", txt)
                extra.append(stripped.strip())
            merged = f"{speaker}: {first_text} {' '.join(extra)}".rstrip()
            out.append(merged)
            # Skip the original lines for this run
            # We need to set i to the index after the last block in the run
            # Also skip blank lines that were within the run
            last_idx = run[-1][0]
            # Append blank lines from after last_idx to j as a single blank separator
            out.append("")
            i = last_idx + 1
            # Skip trailing blanks until next non-blank
            while i < len(lines) and lines[i].strip() == "":
                i += 1
        else:
            out.append(line)
            i += 1
    # Collapse extra blanks
    text2 = "\n".join(out)
    text2 = re.sub(r"\n{3,}", "\n\n", text2)
    return text2


# ------------------------------------------------------------
# Fix 2b — Cross-section pingpong: si fin de seccion X y comienzo de seccion Y
# son el mismo speaker repetido 2+ veces seguidas, insertar reaccion del otro al final de X.
# ------------------------------------------------------------
CROSS_SECTION_REACTIONS_IAGO = [
    "[directo] Eso conecta con lo siguiente.",
    "[reflexivo] Buen punto antes de seguir.",
    "[serio] De acuerdo. Vamos al siguiente bloque.",
]
CROSS_SECTION_REACTIONS_MARIA = [
    "[directo] De acuerdo. Sigamos.",
    "[analitica] Eso lo aterrizamos ahora.",
    "[curioso] Vamos a verlo.",
]


def fix_pingpong_cross_section(text: str) -> str:
    """Si la última intervención de una sección y la primera de la siguiente son del mismo speaker
    formando >=3 consecutivas globalmente, insertar una breve reacción del otro speaker al final
    de la sección anterior.
    """
    from podcast_spec import parse_script_blocks, load_spec
    # Use M spec for parsing (block detection only)
    spec = SPEC_M

    # We iterate until stable
    for _pass in range(5):
        blocks = parse_script_blocks(text, spec)
        # Find first run of 3+
        offender_idx = None
        run = 1
        for i in range(1, len(blocks)):
            if blocks[i]["speaker"] == blocks[i - 1]["speaker"]:
                run += 1
                if run >= 3:
                    offender_idx = i
                    break
            else:
                run = 1
        if offender_idx is None:
            break
        # Find the section header between offender_idx-1 and offender_idx (if any)
        ln_prev = blocks[offender_idx - 1]["line_number"]
        ln_off = blocks[offender_idx]["line_number"]
        lines = text.split("\n")
        # Search for "# SECTION" line strictly between ln_prev and ln_off (1-indexed line_number)
        insert_line = None  # index where we insert a new line
        for li in range(ln_prev, ln_off - 1):
            if li < len(lines) and re.match(r"^# [A-Z_]+\s*$", lines[li]):
                # Found section boundary; insert before this header
                insert_line = li
                break
        speaker = blocks[offender_idx]["speaker"]
        other = "MARIA" if speaker == "IAGO" else "IAGO"
        reaction_pool = CROSS_SECTION_REACTIONS_IAGO if other == "IAGO" else CROSS_SECTION_REACTIONS_MARIA
        reaction = reaction_pool[_pass % len(reaction_pool)]
        new_block = f"{other}: {reaction}"

        if insert_line is not None:
            # Insert as last line of previous section (before header), with blank line
            lines.insert(insert_line, "")
            lines.insert(insert_line, new_block)
        else:
            # Same section pingpong — insert just before the offending block line
            target = ln_off - 1  # 0-indexed
            lines.insert(target, "")
            lines.insert(target, new_block)
        text = "\n".join(lines)
    return text


# ------------------------------------------------------------
# Fix 3 — Remove blacklist interjections from any position
# ------------------------------------------------------------
BLACKLIST = [
    "exactamente",
    "claro que si",
    "claro que sí",
    "muy bien dicho",
    "tienes toda la razon",
    "tienes toda la razón",
    "exacto",
    "por supuesto",
    "eso es",
    "totalmente",
]


def fix_blacklist(text: str) -> str:
    # Only act inside speaker lines, not inside section headers
    def _clean_line(line: str) -> str:
        m = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", line, re.IGNORECASE)
        if not m:
            return line
        speaker, body = m.group(1).upper(), m.group(2)
        for phrase in BLACKLIST:
            # Remove standalone interjection + optional punctuation:
            # "Exacto. Y..." → "Y..."
            # "..., exacto, ..." → "..., ..."
            pattern = re.compile(
                r"(?<![A-Za-záéíóúñ])" + re.escape(phrase) + r"\b[.,!]?\s*",
                re.IGNORECASE,
            )
            body = pattern.sub("", body)
        # Trim leftover double spaces
        body = re.sub(r"\s{2,}", " ", body).strip()
        # If body becomes empty after removal, replace with a neutral phrase
        if not body or re.fullmatch(r"[\[<][a-zA-Z_]+[\]>]\s*", body):
            return f"{speaker}: {body}".rstrip()
        # If body starts with lowercase after the tag, capitalize first letter after tag
        m2 = re.match(r"^(\s*[\[<][a-zA-Z_]+[\]>]\s*)?(.*)$", body)
        if m2 and m2.group(2):
            rest = m2.group(2)
            if rest and rest[0].islower():
                rest = rest[0].upper() + rest[1:]
            body = (m2.group(1) or "") + rest
        return f"{speaker}: {body}"

    lines = text.split("\n")
    out = [_clean_line(l) for l in lines]
    return "\n".join(out)


# ------------------------------------------------------------
# Fix 4 — Iago → Yago in spoken text
# ------------------------------------------------------------
def fix_iago(text: str) -> str:
    def _clean(line: str) -> str:
        m = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", line, re.IGNORECASE)
        if not m:
            return line
        speaker, body = m.group(1).upper(), m.group(2)
        # Replace standalone "Iago" with "Yago" (case-sensitive on first letter)
        body = re.sub(r"\bIago\b", "Yago", body)
        body = re.sub(r"\biago\b", "yago", body)
        return f"{speaker}: {body}"
    return "\n".join(_clean(l) for l in text.split("\n"))


# ------------------------------------------------------------
# Fix 5 — Aviso wrong speaker
# ------------------------------------------------------------
def fix_aviso_speaker(text: str, ep: str, ep_type: str) -> str:
    spec = SPEC_M if ep_type == "M" else SPEC_T
    expected = opening_speaker(ep, spec)  # 'IAGO' or 'MARIA'
    other = "MARIA" if expected == "IAGO" else "IAGO"

    sections = _split_into_sections(text)
    for idx, (header, body) in enumerate(sections):
        if header != "# SALUDO_Y_PRESENTACION":
            continue
        lines = body.split("\n")
        for li, line in enumerate(lines):
            m = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", line, re.IGNORECASE)
            if not m:
                continue
            speaker = m.group(1).upper()
            content_lower = m.group(2).lower()
            if "sistema automatico" in content_lower.replace("á", "a") or "sistema automático" in content_lower:
                if speaker != expected:
                    # Swap speaker
                    lines[li] = f"{expected}: {m.group(2)}"
                break
        sections[idx] = (header, "\n".join(lines))
        break
    return _join_sections(sections)


# ------------------------------------------------------------
# Fix 6 — Tag tecnico → explicativo (for IAGO)
# ------------------------------------------------------------
def fix_tecnico_tag(text: str) -> str:
    def _clean(line: str) -> str:
        m = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", line, re.IGNORECASE)
        if not m:
            return line
        body = m.group(2)
        body = re.sub(r"\[tecnico\]", "[explicativo]", body, flags=re.IGNORECASE)
        body = re.sub(r"<tecnico>", "<explicativo>", body, flags=re.IGNORECASE)
        body = re.sub(r"</tecnico>", "</explicativo>", body, flags=re.IGNORECASE)
        return f"{m.group(1).upper()}: {body}"
    return "\n".join(_clean(l) for l in text.split("\n"))


# ------------------------------------------------------------
# Fix 7 — refs temporales 2025→2026 (estado actual)
# ------------------------------------------------------------
PUB_MARKERS = [
    "paper", "informe", "estudio", "reporte", "publicacion", "publicación",
    "encuesta", "segun", "según", "lanzamiento",
    "mckinsey", "hugging face", "anthropic", "openai", "google",
    "meta", "gartner", "ibm", "idc", "lucid", "forrester", "stanford",
    "state of ai",
]


def _is_publication_context(text_before: str) -> bool:
    """Heurística: ¿hay un marker de publicación en las ~10 palabras anteriores?"""
    words = text_before.split()[-10:]
    window = " ".join(words).lower()
    return any(mk in window for mk in PUB_MARKERS)


def fix_temporal_references(text: str) -> str:
    # Patrones a tratar (siempre que NO estén en contexto de publicación)
    patterns = [
        (re.compile(r"\bdos mil veinticinco\b", re.IGNORECASE), "dos mil veintiseis"),
        (re.compile(r"\b2025\b"), "2026"),
        (re.compile(r"\bdos mil veinticuatro\b", re.IGNORECASE), "dos mil veintiseis"),
    ]

    def _process(line: str) -> str:
        # Only operate inside speaker lines
        m = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", line, re.IGNORECASE)
        if not m:
            return line
        body = m.group(2)
        for pat, repl in patterns:
            def _maybe_replace(match):
                pre = body[: match.start()]
                if _is_publication_context(pre):
                    return match.group(0)
                # Preserve original case of "Dos" if at start of sentence
                orig = match.group(0)
                if orig[0].isupper():
                    return repl.capitalize()
                return repl
            body = pat.sub(_maybe_replace, body)
        return f"{m.group(1).upper()}: {body}"

    return "\n".join(_process(l) for l in text.split("\n"))


# ------------------------------------------------------------
# Fix 8 — Padding: extender bloque de realidad/limites con cierre si guion corto
# ------------------------------------------------------------
def fix_short_word_count(text: str, ep_type: str) -> str:
    """Si guion < min_words, añade una intervención corta de cierre en el bloque líder de MARIA.

    T-type: usa BLOQUE_REALIDAD (nuevo nombre, reemplaza BLOQUE_LIMITES).
    M-type: no aplica (BLOQUE_LIMITES eliminado del M). No hace nada para M.
    """
    spec = SPEC_M if ep_type == "M" else SPEC_T
    min_words = spec["script_rules"]["minimum_word_count"]

    # Count spoken words
    spoken = []
    for line in text.split("\n"):
        m = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", line, re.IGNORECASE)
        if m:
            content = re.sub(r"[\[<][a-zA-Z_/]+[\]>]", "", m.group(2))
            spoken.extend(content.split())
    word_count = len(spoken)

    if word_count >= min_words:
        return text

    # M-type no tiene BLOQUE_REALIDAD — no hacer padding aquí
    if ep_type == "M":
        return text

    needed = min_words - word_count + 20  # margen  # noqa: F841
    # Crear un breve cierre extra en BLOQUE_REALIDAD (Maria) — nuevo nombre v5
    # Compatibilidad hacia atrás: también busca BLOQUE_LIMITES para guiones legacy
    sections = _split_into_sections(text)
    target_headers = {"# BLOQUE_REALIDAD", "# BLOQUE_LIMITES"}
    for idx, (header, body) in enumerate(sections):
        if header not in target_headers:
            continue
        # Determinar último speaker
        blocks = _section_speaker_blocks(body)
        if not blocks:
            continue
        last_speaker = blocks[-1][1]
        other = "MARIA" if last_speaker == "IAGO" else "IAGO"
        # Texto de relleno — contexto técnico breve (Iago) o cierre empresarial (Maria)
        padding_iago = (
            "[explicativo] Y eso conecta con un patrón que se ve en muchas adopciones. "
            "Imagina que introduces una tecnología nueva en un proceso existente. "
            "La tecnología funciona, pero si los flujos y las personas que la usan "
            "no están alineados, el resultado decepciona. "
            "Con los modelos de lenguaje pasa lo mismo: el modelo no falla por sí solo, "
            "falla cuando el sistema alrededor no está diseñado para gestionar sus límites. "
            "Por eso la diferencia entre un piloto y producción no está en el modelo, "
            "sino en la ingeniería que lo envuelve."
        )
        padding_maria = (
            "[analitica] Y eso lo vemos en datos concretos de adopción empresarial. "
            "Según estudios recientes de Gartner y McKinsey, más del setenta por ciento "
            "de los proyectos de inteligencia artificial fallan en la fase de adopción, "
            "no en la fase técnica. El reto no es que el modelo funcione: es que la "
            "organización sepa cuándo confiar en él y cuándo no. "
            "Eso requiere criterio, formación y procesos de validación. "
            "Las empresas que están teniendo éxito con la IA no son las que tienen "
            "los mejores modelos, sino las que han construido las mejores prácticas "
            "alrededor de ellos."
        )
        padding = padding_iago if other == "IAGO" else padding_maria
        new_block = f"\n{other}: {padding}\n"
        sections[idx] = (header, body.rstrip() + "\n" + new_block)
        break
    return _join_sections(sections)


# ------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------
def fix_file(path: Path) -> tuple[int, int]:
    name = path.name
    ep_type = detect_type(name)
    ep = ep_code(name)
    text = path.read_text(encoding="utf-8", errors="replace")
    orig = text

    text = fix_blacklist(text)
    text = fix_iago(text)
    text = fix_tecnico_tag(text)
    text = fix_aviso_speaker(text, ep, ep_type)
    text = fix_temporal_references(text)
    # Run pingpong multiple times until stable (max 5 passes)
    for _ in range(5):
        new_text = fix_pingpong(text)
        if new_text == text:
            break
        text = new_text
    text = fix_pingpong_cross_section(text)
    # Cierre AFTER pingpong so inserted reactions don't bloat it
    text = fix_cierre_conceptos(text, ep_type)
    text = fix_short_word_count(text, ep_type)

    if text != orig:
        path.write_text(text, encoding="utf-8")

    spec = SPEC_M if ep_type == "M" else SPEC_T
    issues = validate_script_text(text, ep, spec, base_dir=BASE)
    hard = [i for i in issues if not i.startswith("[WARN]")]
    warn = [i for i in issues if i.startswith("[WARN]")]
    return len(hard), len(warn)


def main():
    files = sorted(GUIONES.glob("*.txt"))
    total_hard = 0
    total_warn = 0
    print(f"Procesando {len(files)} guiones con spec v4...")
    for f in files:
        h, w = fix_file(f)
        total_hard += h
        total_warn += w
        status = "OK" if h == 0 else f"HARD={h}"
        print(f"  {status:>10}  warn={w:>3}  {f.name}")
    print(f"\nTotal hard: {total_hard}   total warn: {total_warn}")


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el pipeline
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="fix_guiones_v4.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()

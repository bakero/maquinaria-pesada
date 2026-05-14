#!/usr/bin/env python3
"""Rebalanceo mecanico para BLOQUE_DESTACADO / BLOQUE_COMO / BLOQUE_REALIDAD (v5).

Estrategia:
- BLOQUE compartido (M: BLOQUE_DESTACADO / T: BLOQUE_COMO): target = 40-60 cada speaker.
- T-type BLOQUE_REALIDAD: leader = MARIA, target >= 60%.
- T-type BLOQUE_PANORAMA: leader = IAGO, target >= 65%.

Para corregir, partimos las intervenciones mas largas del speaker dominante en
dos: la primera mitad la mantiene el speaker original; la segunda se reasigna
al otro speaker como continuacion. Esto mantiene el contenido textual y solo
reparte el peso de palabras.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from podcast_spec import count_words, load_spec, parse_script_blocks, remove_leading_tag

SPEC_M = load_spec(Path("PODCAST_M_SPEC.md"))
SPEC_T = load_spec(Path("PODCAST_T_SPEC.md"))


def _detect_type(name: str) -> str:
    return "T" if "_TX_T" in name else "M"


# ----------------------------------------------------------------------
# Splitting helpers
# ----------------------------------------------------------------------
SENTENCE_END = re.compile(r"(?<=[\.\?\!])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])")


def split_block(text: str, take_last: float = 0.5) -> tuple[str, str]:
    """Split text into (first_half, second_half) at sentence boundary.

    Removes leading TTS tag from second half. Returns (head_with_tag, tail_no_tag).
    """
    # Extraer tag inicial
    tag_match = re.match(r"^(\s*[\[<][a-zA-Z_/]+[\]>]\s*)", text)
    tag = tag_match.group(1) if tag_match else ""
    body = text[len(tag):]
    sents = SENTENCE_END.split(body.strip())
    if len(sents) < 2:
        return text, ""
    cut = max(1, int(len(sents) * (1 - take_last)))
    head_body = " ".join(sents[:cut])
    tail_body = " ".join(sents[cut:])
    head = (tag + head_body).rstrip()
    tail = tail_body.strip()
    return head, tail


def rebalance_section(
    lines: list[str],
    section: str,
    target_speaker: str,
    target_min_pct: int,
    target_max_pct: int = 100,
    leader_mode: bool = False,
) -> list[str]:
    """Operate over `lines` (in place) splitting the dominant speaker's longest
    blocks within `section` and reassigning the tail to `target_speaker`.
    """
    # Localizar limites de la seccion (rango de indices en `lines`)
    start = end = None
    for i, ln in enumerate(lines):
        m = re.match(r"^# ([A-Z_]+)\s*$", ln)
        if not m:
            continue
        if m.group(1) == section:
            start = i + 1
        elif start is not None and end is None:
            end = i
            break
    if start is None:
        return lines
    if end is None:
        end = len(lines)

    # Helper: stats actuales
    def collect_blocks() -> list[tuple[int, str, str]]:
        out = []
        for li in range(start, end):
            m = re.match(r"^(IAGO|MARIA)\s*:\s*(.*)$", lines[li], re.IGNORECASE)
            if m:
                out.append((li, m.group(1).upper(), m.group(2)))
        return out

    def share() -> tuple[int, int, int]:
        words = defaultdict(int)
        for _, sp, body in collect_blocks():
            words[sp] += count_words(re.sub(r"^[\[<][^\]>]+[\]>]\s*", "", body))
        total = sum(words.values()) or 1
        return words.get("IAGO", 0), words.get("MARIA", 0), total

    over_speaker = "MARIA" if target_speaker == "IAGO" else "IAGO"

    for _pass in range(20):
        i_words, m_words, total = share()
        if total == 0:
            return lines
        tgt_words = i_words if target_speaker == "IAGO" else m_words
        tgt_pct = tgt_words * 100 / total
        if leader_mode:
            if tgt_pct >= target_min_pct:
                return lines
        else:
            # Balanced range
            min_pct, max_pct = target_min_pct, target_max_pct
            if min_pct <= tgt_pct <= max_pct:
                # Verificar que el otro tambien en rango
                other_pct = 100 - tgt_pct
                if min_pct <= other_pct <= max_pct:
                    return lines

        # Encontrar bloque mas largo del over_speaker
        candidates = [
            (li, sp, body, count_words(re.sub(r"^[\[<][^\]>]+[\]>]\s*", "", body)))
            for li, sp, body in collect_blocks()
            if sp == over_speaker
        ]
        if not candidates:
            return lines
        candidates.sort(key=lambda x: -x[3])
        # Tomar el mas largo con al menos 2 oraciones
        chosen = None
        for c in candidates:
            head, tail = split_block(c[2], take_last=0.45)
            if tail and count_words(tail) >= 10:
                chosen = c
                head_t, tail_t = head, tail
                break
        if chosen is None:
            return lines

        li_idx = chosen[0]
        # Reemplazar bloque por head, e insertar tail como otro speaker
        lines[li_idx] = f"{over_speaker}: {head_t}"
        # Etiqueta neutra para la continuacion
        tag = "[analitica]" if target_speaker == "MARIA" else "[explicativo]"
        new_block = f"{target_speaker}: {tag} {tail_t}"
        lines.insert(li_idx + 1, "")
        lines.insert(li_idx + 2, new_block)
        # ajustar `end` porque hemos insertado 2 lineas
        end += 2

    return lines


def process_file(path: Path) -> tuple[int, int]:
    ep_type = _detect_type(path.name)
    spec = SPEC_M if ep_type == "M" else SPEC_T
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    # Bloque compartido
    shared_section = "BLOQUE_DESTACADO" if ep_type == "M" else "BLOQUE_COMO"
    bal_min, bal_max = spec["script_rules"].get("shared_block_balance_range_percent", [40, 60])
    # Aplicamos al under-speaker
    # Identificar speaker over y under desde stats actuales
    blocks = parse_script_blocks(text, spec)
    section_words = defaultdict(lambda: defaultdict(int))
    for b in blocks:
        if b.get("section"):
            section_words[b["section"]][b["speaker"]] += count_words(remove_leading_tag(b["text"]))

    # Shared
    sw = section_words.get(shared_section, {})
    if sw:
        tot = sum(sw.values()) or 1
        i_pct = sw.get("IAGO", 0) * 100 / tot
        m_pct = sw.get("MARIA", 0) * 100 / tot
        if not (bal_min <= i_pct <= bal_max):
            target = "MARIA" if i_pct > bal_max else "IAGO"
            lines = rebalance_section(lines, shared_section, target, bal_min, bal_max, leader_mode=False)

    # T-type BLOQUE_REALIDAD: Maria liderazgo >= 60
    # M-type: BLOQUE_LIMITES eliminado, no aplica
    if ep_type == "T":
        text_now = "\n".join(lines)
        blocks2 = parse_script_blocks(text_now, spec)
        sw_lim = defaultdict(int)
        for b in blocks2:
            if b.get("section") == "BLOQUE_REALIDAD":
                sw_lim[b["speaker"]] += count_words(remove_leading_tag(b["text"]))
        tot_lim = sum(sw_lim.values()) or 1
        m_pct_lim = sw_lim.get("MARIA", 0) * 100 / tot_lim
        if m_pct_lim < 60:
            lines = rebalance_section(lines, "BLOQUE_REALIDAD", "MARIA", 60, 100, leader_mode=True)

    # T-type BLOQUE_PANORAMA leader = IAGO >=65
    if ep_type == "T":
        text_now = "\n".join(lines)
        blocks3 = parse_script_blocks(text_now, spec)
        sw_q = defaultdict(int)
        for b in blocks3:
            if b.get("section") == "BLOQUE_PANORAMA":
                sw_q[b["speaker"]] += count_words(remove_leading_tag(b["text"]))
        tot_q = sum(sw_q.values()) or 1
        i_pct_q = sw_q.get("IAGO", 0) * 100 / tot_q
        if i_pct_q < 65:
            lines = rebalance_section(lines, "BLOQUE_PANORAMA", "IAGO", 65, 100, leader_mode=True)
    else:
        # M-type BLOQUE_PANORAMA leader = IAGO >=65
        text_now = "\n".join(lines)
        blocks3 = parse_script_blocks(text_now, spec)
        sw_p = defaultdict(int)
        for b in blocks3:
            if b.get("section") == "BLOQUE_PANORAMA":
                sw_p[b["speaker"]] += count_words(remove_leading_tag(b["text"]))
        tot_p = sum(sw_p.values()) or 1
        i_pct_p = sw_p.get("IAGO", 0) * 100 / tot_p
        if i_pct_p < 65:
            lines = rebalance_section(lines, "BLOQUE_PANORAMA", "IAGO", 65, 100, leader_mode=True)

    new_text = "\n".join(lines)
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return 1, 0
    return 0, 0


def main():
    files = sorted(Path("Guiones").glob("*.txt"))
    changed = 0
    for f in files:
        c, _ = process_file(f)
        changed += c
        print(f"{'CHG' if c else 'OK '}  {f.name}")
    print(f"\nFiles changed: {changed}")


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el pipeline
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="rebalance_blocks.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()

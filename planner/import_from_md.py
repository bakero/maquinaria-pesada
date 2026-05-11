"""Parse a task-list markdown into structured `tareas.json`.

Usage:
    python planner/import_from_md.py [SOURCE.md]

Default SOURCE: latest `planner/source/*.md` (lexicographic). Output:
`planner/tareas.json`. Does NOT touch `planner/_state.json` (mutable status).

Expected line format per task:
  **TNNN** · description · `OWNER:` X · `LISTA:` date|recurring · `SALE:` date|— · `DEP:` T0xx, T0xx

Tolerances:
- Date: dd/mm/aaaa with optional hh:mm. Time omitted → date-only.
- `LISTA: diario SN` / `LISTA: continuo` → recurring flag.
- `SALE: —` → no public date.
- Emoji 🔴 anywhere in the title → critical = True.
- Title starting with "CHECK" or "CHECK:" → is_check = True.
- Multiple DEPs separated by commas. Also accepts T001-T012 ranges (expanded).

Block + subsection tracked via `## BLOQUE / ## SEMANA` and `### subsection` headers
encountered while scanning.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

# ----- Regex patterns ----------------------------------------------------

# A task line typically begins with **TNNN** · then fields separated by · .
TASK_LINE = re.compile(r"^\*\*(T\d{3,4})\*\*\s*·\s*(.+)$")

OWNER_RE = re.compile(r"`?OWNER:`?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-Za-z]+)?)")
LISTA_RE = re.compile(r"`?LISTA:`?\s*(.+?)(?=\s*·\s*`?SALE:|$)")
SALE_RE = re.compile(r"`?SALE:`?\s*(.+?)(?=\s*·\s*`?DEP:|$)")
DEP_RE = re.compile(r"`?DEP:`?\s*(.+?)$")

DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})(?:\s+(\d{2}):(\d{2}))?")
RECURRING_RE = re.compile(r"(?:diario|continuo)", re.IGNORECASE)

BLOQUE_HEADER = re.compile(r"^##\s+(BLOQUE\s+\d+\b.+|SEMANA\s+\d+\b.+)$", re.IGNORECASE)
SUBSECTION_HEADER = re.compile(r"^###\s+(.+)$")


def _parse_date(text: str) -> tuple[str | None, str | None]:
    """Return (iso_date_or_none, time_or_none) from a chunk of free text."""
    if not text or text.strip() in ("—", "-", ""):
        return None, None
    m = DATE_RE.search(text)
    if not m:
        return None, None
    dd, mm, yyyy, hh, mi = m.groups()
    try:
        iso = date(int(yyyy), int(mm), int(dd)).isoformat()
    except ValueError:
        return None, None
    time_str = f"{hh}:{mi}" if hh and mi else None
    return iso, time_str


def _is_recurring(text: str) -> bool:
    return bool(RECURRING_RE.search(text or ""))


def _parse_deps(text: str) -> list[str]:
    """Accepts "T001, T002" or "T001-T012" (range expanded) or mixed."""
    if not text:
        return []
    out: list[str] = []
    # split by comma
    for part in text.split(","):
        p = part.strip()
        if not p:
            continue
        rng = re.match(r"(T)(\d{3,4})-T?(\d{3,4})", p)
        if rng:
            prefix, lo, hi = rng.groups()
            for n in range(int(lo), int(hi) + 1):
                out.append(f"{prefix}{n:03d}")
        else:
            m = re.match(r"T\d{3,4}", p)
            if m:
                out.append(m.group(0))
    return out


def parse_md(source: Path) -> list[dict]:
    text = source.read_text(encoding="utf-8")
    bloque = ""
    subsection = ""
    tasks: list[dict] = []

    for raw in text.splitlines():
        line = raw.rstrip()

        m_bloque = BLOQUE_HEADER.match(line)
        if m_bloque:
            bloque = m_bloque.group(1).strip()
            subsection = ""  # reset on new block
            continue

        m_sub = SUBSECTION_HEADER.match(line)
        if m_sub:
            subsection = m_sub.group(1).strip()
            continue

        m_task = TASK_LINE.match(line)
        if not m_task:
            continue

        task_id = m_task.group(1)
        rest = m_task.group(2)

        # Split title from metadata fields. Title is the first segment before
        # the first `OWNER:` field.
        owner_split = rest.split("`OWNER:`", 1)
        if len(owner_split) == 2:
            title_part, meta_part = owner_split[0], "`OWNER:`" + owner_split[1]
        else:
            # Some lines may use OWNER without backticks
            alt = rest.split("OWNER:", 1)
            if len(alt) == 2:
                title_part, meta_part = alt[0], "OWNER:" + alt[1]
            else:
                title_part, meta_part = rest, ""

        title = title_part.rstrip(" ·\t").strip()
        critical = "🔴" in title
        title = title.replace("🔴", "").strip()
        is_check = bool(re.match(r"^CHECK[:\s]", title, re.IGNORECASE))

        # Parse fields
        owner_m = OWNER_RE.search(meta_part)
        owner = owner_m.group(1).strip() if owner_m else ""

        lista_m = LISTA_RE.search(meta_part)
        sale_m = SALE_RE.search(meta_part)
        dep_m = DEP_RE.search(meta_part)

        lista_raw = lista_m.group(1).strip() if lista_m else ""
        sale_raw = sale_m.group(1).strip() if sale_m else ""
        dep_raw = dep_m.group(1).strip() if dep_m else ""

        lista_date, lista_time = _parse_date(lista_raw)
        sale_date, sale_time = _parse_date(sale_raw)
        recurring = _is_recurring(lista_raw)

        tasks.append({
            "id": task_id,
            "title": title,
            "owner": owner,
            "block": bloque,
            "subsection": subsection,
            "lista_date": lista_date,
            "lista_time": lista_time,
            "lista_raw": lista_raw,        # preserved verbatim for debugging
            "sale_date": sale_date,
            "sale_time": sale_time,
            "sale_raw": sale_raw,
            "deps": _parse_deps(dep_raw),
            "critical": critical,
            "is_check": is_check,
            "recurring": recurring,
        })
    return tasks


def latest_source() -> Path:
    src_dir = Path(__file__).parent / "source"
    candidates = sorted(src_dir.glob("*.md"))
    if not candidates:
        raise SystemExit(f"No source .md found in {src_dir}")
    return candidates[-1]


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        source = Path(argv[1])
    else:
        source = latest_source()

    print(f"Reading: {source}")
    tasks = parse_md(source)
    print(f"Parsed: {len(tasks)} tasks")

    # Sanity: count critical / check / recurring
    critical = sum(1 for t in tasks if t["critical"])
    checks = sum(1 for t in tasks if t["is_check"])
    recurring = sum(1 for t in tasks if t["recurring"])
    with_dep = sum(1 for t in tasks if t["deps"])
    with_lista = sum(1 for t in tasks if t["lista_date"])
    with_sale = sum(1 for t in tasks if t["sale_date"])

    # ASCII-only prints (Windows cp1252 console doesn't grok emoji).
    print(f"  critical  : {critical}")
    print(f"  checks    : {checks}")
    print(f"  recurring : {recurring}")
    print(f"  with deps : {with_dep}")
    print(f"  with LISTA: {with_lista}")
    print(f"  with SALE : {with_sale}")

    out_path = Path(__file__).parent / "tareas.json"
    out_path.write_text(
        json.dumps({
            "source": str(source.relative_to(source.parent.parent.parent))
                      if source.is_relative_to(Path(__file__).parent.parent)
                      else str(source),
            "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
            "tasks": tasks,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote: {out_path}")

    # Initialize _state.json if missing
    state_path = Path(__file__).parent / "_state.json"
    if not state_path.exists():
        state_path.write_text(json.dumps({}, ensure_ascii=False, indent=2),
                              encoding="utf-8")
        print(f"Initialized empty: {state_path}")
    else:
        print(f"Preserved existing: {state_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

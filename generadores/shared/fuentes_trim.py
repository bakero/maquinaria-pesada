"""Post-process determinista para BLOQUE_FUENTES.

El modelo (Sonnet) tiene un fallo persistente con la regla de "exactamente N
fuentes con N años distintos": oscila entre 2, 3, 4 y 5 incluso con retries
con feedback. Este módulo aplica un trim mecánico DESPUÉS de la generación,
ANTES de la validación: si BLOQUE_FUENTES tiene más años distintos que el
máximo permitido, elimina interventions del FINAL del bloque hasta llegar
al máximo objetivo. Si tiene menos, no hace nada (no podemos inventar
fuentes con calidad).

Uso desde m_generator / t_generator (antes de validate_fn).
"""
from __future__ import annotations

import re

# Coincide con validators/m_validator._YEAR_PATTERN. Cubre:
#  - 19xx/20xx en dígitos
#  - "dos mil X" para 2000-2099 (con lookbehind `(?<!y\s)` para evitar
#    falsos positivos como "cuarenta y dos mil uno" = ISO 42001)
#  - "mil novecientos X" para 1900-1999
_YEAR_PATTERN = re.compile(
    r"\b(?:"
    r"19\d{2}|20\d{2}"
    r"|(?<!y\s)dos\s+mil(?:\s+\w+){0,3}"
    r"|mil\s+novecientos(?:\s+\w+){1,3}"
    r")\b",
    re.IGNORECASE,
)

_SECTION_RE = re.compile(r"^#\s+([A-Z_]+)\s*$", re.MULTILINE)
_LINE_RE = re.compile(
    r"^\s*(?P<speaker>IAGO|YAGO|MARIA|MARÍA)\s*:\s*",
    re.MULTILINE,
)


def _distinct_years(text: str) -> list[str]:
    return list({m.group(0).strip().lower() for m in _YEAR_PATTERN.finditer(text)})


def trim_bloque_fuentes(script: str, *, max_years: int) -> str:
    """Si BLOQUE_FUENTES tiene más años distintos que ``max_years``, elimina
    interventions del final hasta llegar al objetivo.

    Devuelve el guion modificado o el original si no hay nada que recortar.
    """
    sections = list(_SECTION_RE.finditer(script))
    if not sections:
        return script

    # Localizar inicio y fin de BLOQUE_FUENTES.
    fuentes_idx = None
    for i, m in enumerate(sections):
        if m.group(1) == "BLOQUE_FUENTES":
            fuentes_idx = i
            break
    if fuentes_idx is None:
        return script

    start = sections[fuentes_idx].end()
    end = (
        sections[fuentes_idx + 1].start()
        if fuentes_idx + 1 < len(sections)
        else len(script)
    )
    bloque = script[start:end]

    years = _distinct_years(bloque)
    if len(years) <= max_years:
        return script

    # Partir el bloque en interventions (por cabeceras SPEAKER:).
    spk_matches = list(_LINE_RE.finditer(bloque))
    if not spk_matches:
        return script

    # Calcular spans: [start_i, end_i) de cada intervention dentro del bloque.
    spans: list[tuple[int, int]] = []
    for j, sm in enumerate(spk_matches):
        s = sm.start()
        e = spk_matches[j + 1].start() if j + 1 < len(spk_matches) else len(bloque)
        spans.append((s, e))

    # Acumular interventions desde la primera hasta que los años distintos
    # alcancen max_years. Las siguientes se descartan.
    kept_text = bloque[:spans[0][0]]  # Texto previo a la primera intervención.
    seen_years: set[str] = set()
    for s, e in spans:
        chunk = bloque[s:e]
        chunk_years = _distinct_years(chunk)
        new_years = [y for y in chunk_years if y not in seen_years]
        # Si añadir este chunk mantiene los años <= max_years, lo conservamos.
        if len(seen_years) + len(new_years) <= max_years:
            kept_text += chunk
            seen_years.update(new_years)
        else:
            # Detenemos el corte aquí. Las interventions siguientes se eliminan.
            break

    if not kept_text.strip():
        # No deberíamos vaciar el bloque; abortar si se rompería.
        return script

    new_script = script[:start] + kept_text + script[end:]
    return new_script

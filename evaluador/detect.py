"""Detección de tipo de guion por filename + verificación por contenido.

Diverge del spec original (§3.1) en una cosa: los regex se ablandan para
aceptar sufijos descriptivos y extensión `.md`, porque el corpus real
mezcla ambas convenciones. Las reglas seguirán siendo las del spec v6.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Regex relajados (admiten .txt o .md y sufijo descriptivo opcional)
M_REGEX = re.compile(r"^M(\d{1,2})(_.+)?\.(txt|md)$")
T_REGEX = re.compile(r"^M(\d{1,2})_T(\d{1,2})(_.+)?\.(txt|md)$")
S_REGEX = re.compile(r"^S(\d{1,3})(_.+)?\.(txt|md)$")


@dataclass
class KindDetection:
    kind: str | None  # "M" | "T" | "S" | None
    module_n: int | None
    tema_n: int | None
    s_n: int | None
    reason: str  # explicación si kind=None o si hay mismatch


def detect_kind_from_filename(filename: str) -> KindDetection:
    """Detecta el tipo del guion sólo por filename.

    Prioridad: T > M (porque M_T... también matchea ^M(\\d+)).
    """
    name = Path(filename).name

    m_t = T_REGEX.match(name)
    if m_t:
        return KindDetection(
            kind="T",
            module_n=int(m_t.group(1)),
            tema_n=int(m_t.group(2)),
            s_n=None,
            reason="filename T match",
        )

    m_m = M_REGEX.match(name)
    if m_m:
        return KindDetection(
            kind="M",
            module_n=int(m_m.group(1)),
            tema_n=None,
            s_n=None,
            reason="filename M match",
        )

    m_s = S_REGEX.match(name)
    if m_s:
        return KindDetection(
            kind="S",
            module_n=None,
            tema_n=None,
            s_n=int(m_s.group(1)),
            reason="filename S match",
        )

    return KindDetection(
        kind=None,
        module_n=None,
        tema_n=None,
        s_n=None,
        reason=f"filename '{name}' no encaja en ningún patrón M/T/S",
    )


def verify_kind_with_content(kind: str, raw_text: str) -> tuple[bool, str]:
    """Verifica que el contenido es coherente con el tipo declarado.

    Devuelve (ok, mensaje). El mensaje describe el mismatch si ok=False.
    """
    text_upper = raw_text.upper()

    if kind == "M":
        # M exige APLICACION_PRACTICA como marker de v6.
        if "# APLICACION_PRACTICA" not in text_upper:
            return False, "M sin marcador '# APLICACION_PRACTICA' (estructura legacy o no-M)"
        return True, ""

    if kind == "T":
        # T exige BLOQUE_COMO y (BLOQUE_REALIDAD o BLOQUE_CASOS).
        has_como = "# BLOQUE_COMO" in text_upper
        has_realidad = "# BLOQUE_REALIDAD" in text_upper or "# BLOQUE_CASOS" in text_upper
        if not has_como or not has_realidad:
            return False, "T sin '# BLOQUE_COMO' y/o '# BLOQUE_REALIDAD|BLOQUE_CASOS'"
        if "# APLICACION_PRACTICA" in text_upper:
            return False, "T contiene '# APLICACION_PRACTICA' (exclusivo de M)"
        return True, ""

    if kind == "S":
        # S no debe tener cabeceras de bloque ni atribuciones IAGO/MARIA.
        if re.search(r"^#\s*BLOQUE_", raw_text, re.MULTILINE | re.IGNORECASE):
            return False, "S contiene cabecera '# BLOQUE_*' (debe ser estructura plana)"
        if re.search(r"^(IAGO|YAGO|MARIA|MAR[ÍI]A)\s*:", raw_text, re.MULTILINE | re.IGNORECASE):
            return False, "S contiene atribución de speaker (debe ser narración neutral)"
        return True, ""

    return False, f"tipo desconocido: {kind}"

"""Cálculo de paridad: qué presentador abre el episodio.

Regla A.3 del cuadro consolidado v6.

La regla es la misma para los tres formatos — **impar → Yago, par → Maria** —
pero el número que decide la paridad cambia:

- M: número de módulo (M0 → Maria, M1 → Yago, ...).
- T: número de tema (T1 → Yago, T2 → Maria, ...).
- S: número de orden de publicación (S1 → Yago, S2 → Maria, ...).

Quien abre el episodio abre el HOOK y dice el aviso de IA (en M y T; S no narra
aviso). El nombre hablado de IAGO es "Yago".
"""
from __future__ import annotations

import re

from validators.result import ValidationResult, fail, ok

IAGO = "IAGO"
MARIA = "MARIA"


def opener_for(number: int) -> str:
    """Devuelve el speaker que abre según la paridad del número.

    impar → IAGO, par → MARIA. Vale para M (módulo), T (tema) y S (orden).
    """
    return IAGO if number % 2 == 1 else MARIA


def number_from_episode_id(episode_id: str, kind: str) -> int | None:
    """Extrae el número que decide la paridad a partir del id del episodio.

    - kind="M": episode_id tipo "M3"          → 3
    - kind="T": episode_id tipo "M3_T2"       → 2 (número de tema)
    - kind="S": episode_id tipo "S7" o "S7_RAG" → 7
    """
    kind = kind.upper()
    if kind == "M":
        m = re.match(r"^M(\d+)$", episode_id)
        return int(m.group(1)) if m else None
    if kind == "T":
        m = re.match(r"^M\d+_T(\d+)", episode_id)
        return int(m.group(1)) if m else None
    if kind == "S":
        m = re.match(r"^S(\d+)", episode_id)
        return int(m.group(1)) if m else None
    return None


def check_opener(episode_id: str, kind: str,
                  actual_opener: str) -> ValidationResult:
    """Hard-fail si quien abre el episodio no coincide con la paridad."""
    number = number_from_episode_id(episode_id, kind)
    if number is None:
        return fail(
            "parity_opener", "HARD",
            f"No se pudo extraer el número de paridad de '{episode_id}' "
            f"(kind={kind})",
            episode_id=episode_id, kind=kind,
        )
    expected = opener_for(number)
    actual = (actual_opener or "").strip().upper()
    if actual == expected:
        return ok("parity_opener", "HARD",
                  f"{episode_id}: abre {expected} (correcto por paridad)")
    return fail(
        "parity_opener", "HARD",
        f"{episode_id}: abre {actual or '?'} pero por paridad debe abrir {expected}",
        episode_id=episode_id, kind=kind, expected=expected, actual=actual,
    )

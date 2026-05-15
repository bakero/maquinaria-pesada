"""Tests de generadores/shared/ssml_pauses.py."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared import ssml_pauses as sp  # noqa: E402

SAMPLE = """\
# HOOK
IAGO: [directo] Frase inicial del hook.
MARIA: [curioso] Y una pregunta.

# SALUDO_Y_PRESENTACION
IAGO: [calido] Hola.
MARIA: [calido] Hola.

# BLOQUE_PANORAMA
IAGO: [explicativo] Mapa del módulo.
"""


def test_insert_block_pauses_adds_break_after_hook():
    out = sp.insert_block_pauses(SAMPLE)
    # Después del HOOK debe haber un break con 600ms (after_hook).
    hook_section = out.split("# SALUDO_Y_PRESENTACION")[0]
    assert "600ms" in hook_section


def test_insert_block_pauses_adds_between_blocks():
    out = sp.insert_block_pauses(SAMPLE)
    # Entre SALUDO_Y_PRESENTACION y BLOQUE_PANORAMA, pausa default 1000ms.
    assert "1000ms" in out


def test_insert_block_pauses_does_not_add_after_last_section():
    text = "# HOOK\nIAGO: [directo] Solo.\n"
    out = sp.insert_block_pauses(text)
    # Última sección sin sección siguiente → sin pausa final.
    breaks = out.count("<break")
    assert breaks == 1  # solo el after_hook al ser HOOK


def test_speaker_change_pause_inserted():
    text = "# HOOK\nIAGO: [directo] Uno.\nMARIA: [curioso] Dos.\n"
    out = sp.insert_speaker_change_pauses(text, pause_ms=500)
    assert "500ms" in out


def test_speaker_change_no_pause_for_first_speaker():
    text = "# HOOK\nIAGO: [directo] Uno.\n"
    out = sp.insert_speaker_change_pauses(text, pause_ms=500)
    assert "<break" not in out


def test_speaker_change_resets_between_sections():
    text = (
        "# HOOK\nIAGO: [directo] Uno.\n"
        "# SALUDO_Y_PRESENTACION\nIAGO: [calido] Sigue siendo Iago.\n"
    )
    out = sp.insert_speaker_change_pauses(text, pause_ms=500)
    # No hay cambio dentro de la misma sección con un solo speaker → sin pausa.
    assert "<break" not in out


def test_insert_all_applies_both_pauses():
    out = sp.insert_all(SAMPLE)
    assert "600ms" in out
    assert "1000ms" in out
    assert "500ms" in out


def test_custom_pauses_config():
    custom = {"after_hook": 999, "between_blocks": 1234, "speaker_change": 321}
    out = sp.insert_all(SAMPLE, custom)
    assert "999ms" in out
    assert "1234ms" in out
    assert "321ms" in out

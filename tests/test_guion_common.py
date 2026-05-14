"""Tests del núcleo compartido de generación (guion_common.py).

Foco: `_soften_inline_enumerations`. Esta función reemplaza a un intento
previo (`_soften_inline_enumerations` en wip/master-postprocs) que corrompía
el texto — convertía "por segundo" en "por El segundo punto es que" y producía
"El El segundo punto es que". Estos tests fijan que eso NO puede volver a pasar.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guion_common import _soften_inline_enumerations  # noqa: E402


def test_suaviza_enumeracion_real():
    text = (
        "# BLOQUE_COMO\n"
        "IAGO: [didactico] El flujo tiene tres etapas. Primero, la ingesta de "
        "documentos. Segundo, la recuperacion por similitud. Tercero, la "
        "generacion de la respuesta."
    )
    out = _soften_inline_enumerations(text)
    # Los ordinales de lista desaparecen...
    assert "Primero," not in out
    assert "Segundo," not in out
    assert "Tercero," not in out
    # ...sustituidos por conectores naturales...
    assert "Para empezar," in out
    # ...y el contenido se conserva intacto.
    assert "la ingesta de documentos" in out
    assert "la recuperacion por similitud" in out
    assert "la generacion de la respuesta" in out


def test_no_toca_ordinales_en_minuscula():
    """La corrupcion del intento previo: 'por segundo', 'el segundo arbol'."""
    text = (
        "# BLOQUE_REALIDAD\n"
        "MARIA: [analitica] Procesan millones de transacciones por segundo. "
        "El segundo arbol corrige los errores del primero."
    )
    assert _soften_inline_enumerations(text) == text


def test_ignora_ordinal_suelto():
    """Un solo 'Primero,' no es una lista — no se toca (umbral >=2)."""
    text = (
        "# BLOQUE_PANORAMA\n"
        "IAGO: [directo] Primero, conviene aclarar algo importante del tema."
    )
    assert _soften_inline_enumerations(text) == text


def test_protege_cierre_conceptos():
    """CIERRE_CONCEPTOS usa Primero/Segundo/Tercero de forma obligatoria."""
    text = (
        "# CIERRE_CONCEPTOS\n"
        "IAGO: [firme] No te puedes ir sin esto. Primero, el concepto base. "
        "Segundo, la aplicacion. Tercero, el limite."
    )
    assert _soften_inline_enumerations(text) == text


def test_sin_palabras_comidas_ni_duplicadas():
    """Sin 'El El', sin 'punto es que', sin 'etapa es etapa'."""
    text = (
        "# BLOQUE_DESTACADO\n"
        "IAGO: [didactico] Hay dos mecanismos. Primero, el indexado offline. "
        "Segundo, la consulta online en tiempo real."
    )
    out = _soften_inline_enumerations(text)
    line = out.split("\n")[1]
    assert line.startswith("IAGO: [didactico] ")
    assert "El El" not in out
    assert "punto es que" not in out
    assert "etapa es etapa" not in out
    assert "  " not in line  # sin dobles espacios


def test_conserva_speaker_y_tag():
    text = (
        "# BLOQUE_COMO\n"
        "MARIA: [explicativo] Son dos fases. Primero, una. Segundo, otra."
    )
    out = _soften_inline_enumerations(text)
    assert out.split("\n")[1].startswith("MARIA: [explicativo] ")


def test_headers_y_no_speaker_intactos():
    text = "# BLOQUE_COMO\n\nlinea suelta sin speaker\n"
    assert _soften_inline_enumerations(text) == text

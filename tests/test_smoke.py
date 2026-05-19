"""Smoke tests baseline.

Objetivo: detectar rotura de imports y validar el contrato del prompt_builder
y del registry de connectors. No requiere claves API ni dependencias pesadas
(anthropic, pydub, whisper). El resto de pipelines se prueban en tests
dedicados a medida que se modularicen.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_prompt_builder_emite_comando_python():
    from cockpit.core import prompt_builder

    cmd = prompt_builder.build(
        script="lanzar_produccion.py",
        flags=[("--ep", "EP001"), ("--dry-run", True), ("--skip", False), ("--note", None)],
        cwd="/tmp",
        header="test",
    )
    assert "python lanzar_produccion.py" in cmd
    assert "--ep EP001" in cmd
    assert "--dry-run" in cmd  # bool True → flag sin valor
    assert "--skip" not in cmd  # bool False → omitido
    assert "--note" not in cmd  # None → omitido
    assert "cd /tmp" in cmd
    assert "# test" in cmd


def test_prompt_builder_escapa_espacios_en_paths():
    from cockpit.core import prompt_builder

    cmd = prompt_builder.build(
        script="x.py",
        flags=[("--path", "/home/user/with space/file.txt")],
        cwd=None,
    )
    assert "'/home/user/with space/file.txt'" in cmd


def test_connector_registry_se_carga_sin_errores():
    from cockpit import connectors

    assert len(connectors.REGISTRY) > 0, "El registry no debería estar vacío"
    # Categorías esperadas
    cats = {c.category for c in connectors.REGISTRY.values()}
    assert "pipeline" in cats
    assert "service" in cats


def test_pipelines_registrados_tienen_id_y_script():
    from cockpit import connectors
    from cockpit.connectors.base import PipelineConnector

    pipes = [c for c in connectors.REGISTRY.values() if isinstance(c, PipelineConnector)]
    assert pipes, "Debe haber al menos un PipelineConnector"
    for p in pipes:
        assert p.id, f"Pipeline sin id: {type(p).__name__}"
        assert p.script, f"Pipeline {p.id} sin script"
        assert p.script.endswith(".py"), f"Pipeline {p.id}: script debería ser .py"


def test_pipeline_build_command_omite_campos_vacios():
    from cockpit import connectors
    from cockpit.connectors.base import PipelineConnector

    pipe = next(
        (c for c in connectors.REGISTRY.values() if isinstance(c, PipelineConnector)),
        None,
    )
    assert pipe is not None
    # Sin ningún valor → comando solo con `python script.py`
    cmd = pipe.build_command({})
    assert f"python {pipe.script}" in cmd


@pytest.mark.parametrize(
    "value, expected_in_cmd",
    [
        (True, True),
        (False, False),
        ("", False),
        (None, False),
        ("valor", True),
    ],
)
def test_prompt_builder_filtra_valores_falsy(value, expected_in_cmd):
    from cockpit.core import prompt_builder

    cmd = prompt_builder.build(
        script="x.py",
        flags=[("--f", value)],
        cwd=None,
    )
    assert ("--f" in cmd) is expected_in_cmd

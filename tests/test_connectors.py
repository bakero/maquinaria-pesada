"""Tests del registro de connectors y de los connectors registrados."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit import connectors  # noqa: E402
from cockpit.connectors.base import (  # noqa: E402
    Connector,
    Field_,
    PipelineConnector,
    ServiceConnector,
    SourceConnector,
    Status,
    register,
)


def test_registry_no_vacio():
    assert len(connectors.REGISTRY) >= 4


def test_categorias_esperadas_presentes():
    by_cat = {
        cat: connectors.by_category(cat)  # type: ignore[arg-type]
        for cat in ("service", "pipeline", "source")
    }
    assert all(len(v) > 0 for v in by_cat.values())


def test_pipelines_principales_registrados():
    expected = {"generar_guion", "validar_episodio", "estado_proyecto"}
    actual = {c.id for c in connectors.by_category("pipeline")}
    assert expected.issubset(actual)


def test_services_principales_registrados():
    expected = {"openai", "elevenlabs"}
    actual = {c.id for c in connectors.by_category("service")}
    assert expected.issubset(actual)


def test_get_devuelve_el_correcto():
    c = connectors.get("generar_guion")
    assert c.id == "generar_guion"
    assert isinstance(c, PipelineConnector)


def test_get_keyerror_si_no_existe():
    with pytest.raises(KeyError):
        connectors.get("no-existe")


def test_register_rechaza_id_duplicado():
    class _Dup(PipelineConnector):
        id = "generar_guion"  # ya existe
        script = "x.py"

    with pytest.raises(ValueError, match="already registered"):
        register(_Dup)


def test_register_rechaza_sin_id():
    class _SinId(PipelineConnector):
        id = ""
        script = "x.py"

    with pytest.raises(ValueError, match="missing id"):
        register(_SinId)


def test_field_serializable_a_dict():
    f = Field_(flag="--ep", label="Episodio", kind="str", required=True)
    assert f.flag == "--ep"
    assert f.options == []  # default factory


def test_pipelineconnector_build_command_excluye_falsy():
    class _P(PipelineConnector):
        id = "_test_p"
        script = "x.py"
        fields = [
            Field_("--a", "A"),
            Field_("--b", "B", kind="bool"),
        ]

    p = _P()
    cmd = p.build_command({"--a": "val", "--b": False})
    assert "--a val" in cmd
    assert "--b" not in cmd


def test_pipelineconnector_status_marca_no_existente():
    class _P(PipelineConnector):
        id = "_t1"
        script = "no_existe_zzz_xyz.py"

    s = _P().status()
    assert s.ok is False


def test_serviceconnector_status_sin_env_keys_es_ok():
    class _S(ServiceConnector):
        id = "_t2"

    s = _S().status()
    assert s.ok is True


def test_serviceconnector_status_falta_env(monkeypatch, tmp_path):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    monkeypatch.delenv("UNLIKELY_VAR_XYZ", raising=False)

    class _S(ServiceConnector):
        id = "_t3"
        env_keys = ("UNLIKELY_VAR_XYZ",)

    s = _S().status()
    assert s.ok is False
    assert "UNLIKELY_VAR_XYZ" in s.detail


def test_sourceconnector_list_items_default_es_vacio():
    class _Src(SourceConnector):
        id = "_t4"

    assert _Src().list_items() == []


def test_status_dataclass_defaults():
    s = Status(ok=True)
    assert s.ok is True
    assert s.detail == ""


def test_base_connector_status_es_ok():
    class _C(Connector):
        id = "_t5"

    assert _C().status().ok is True

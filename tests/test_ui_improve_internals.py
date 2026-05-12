"""Tests de los helpers privados de ui_improve y del extractor JSON del Mapa.

No instancia Streamlit. Solo testea funciones puras.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit import ui_improve  # noqa: E402


def test_build_user_message_sin_extra():
    msg = ui_improve._build_user_message("CTX", "", "PROMPT")  # noqa: SLF001
    assert "## Contexto del componente" in msg
    assert "CTX" in msg
    assert "PROMPT" in msg
    assert "## Estado actual" not in msg


def test_build_user_message_con_extra():
    msg = ui_improve._build_user_message("CTX", "EXTRA", "PROMPT")  # noqa: SLF001
    assert "## Estado actual" in msg
    assert "EXTRA" in msg


def test_default_slow_warning_es_120s():
    assert ui_improve.DEFAULT_SLOW_WARNING_S == 120


def test_forbidden_hints_contiene_zonas_protegidas():
    must = {"cockpit/", ".github/", "generar_guion.py", "pyproject.toml"}
    assert must.issubset(set(ui_improve._FORBIDDEN_HINTS))  # noqa: SLF001


def test_warn_no_se_invoca_streamlit_si_no_hay_hits(monkeypatch):
    # Sustituir streamlit por un objeto que falle si se llama a warning.
    import types

    fake_st = types.SimpleNamespace(warning=lambda *_: pytest_fail("no debió llamarse"))
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    # No hay hits → no llama a st.warning.
    ui_improve._warn_if_mentions_forbidden_paths("Texto inocuo sin paths sensibles")  # noqa: SLF001


def test_warn_se_invoca_si_hay_hits(monkeypatch):
    import types

    captured = []
    fake_st = types.SimpleNamespace(warning=lambda msg: captured.append(msg))
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    ui_improve._warn_if_mentions_forbidden_paths(  # noqa: SLF001
        "Voy a modificar cockpit/app.py y .github/workflows/ci.yml"
    )
    assert len(captured) == 1
    assert "cockpit/" in captured[0]
    assert ".github/" in captured[0]


def pytest_fail(msg):
    import pytest

    pytest.fail(msg)


# --- _extract_json_map vive en la página Mapa, lo cargamos por path ---

def _load_mapa_module():
    # No queremos ejecutar el cuerpo Streamlit del módulo: con AST extraemos
    # solo la función _extract_json_map y la ejecutamos en un namespace aislado.
    page_path = ROOT / "cockpit" / "pages" / "12_🗺️_Mapa.py"
    src = page_path.read_text(encoding="utf-8")
    fn_src = _extract_function_source(src, "_extract_json_map")
    ns: dict = {}
    exec(  # noqa: S102
        "import json\n" + fn_src, ns,
    )
    return ns["_extract_json_map"]


def _extract_function_source(src: str, fn_name: str) -> str:
    import ast

    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            return ast.get_source_segment(src, node)
    raise AssertionError(f"No se encontró función {fn_name}")


def test_extract_json_map_devuelve_dict_valido():
    fn = _load_mapa_module()
    text = (
        "Aquí va el mapa:\n"
        "```json\n"
        '{"nodes": [{"id": "x", "label": "X", "kind": "system"}], '
        '"edges": []}\n'
        "```\n"
        "Fin."
    )
    result = fn(text)
    assert isinstance(result, dict)
    assert result["nodes"][0]["id"] == "x"
    assert result["edges"] == []


def test_extract_json_map_devuelve_none_sin_bloque():
    fn = _load_mapa_module()
    assert fn("Respuesta sin código") is None


def test_extract_json_map_devuelve_none_si_json_invalido():
    fn = _load_mapa_module()
    text = "```json\n{esto no es json válido}\n```"
    assert fn(text) is None


def test_extract_json_map_devuelve_none_si_faltan_campos():
    fn = _load_mapa_module()
    text = '```json\n{"otro": 1}\n```'
    assert fn(text) is None

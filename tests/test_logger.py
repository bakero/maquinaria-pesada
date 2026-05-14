"""Tests del logger estructurado JSON."""
from __future__ import annotations

import io
import json
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import logger as L  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_logger():
    """Cada test arranca con bindings limpios y el handler re-instalable."""
    L.clear()
    # Forzar reinstalación del handler en cada test para que capture el stream.
    L._HANDLER_INSTALLED = False
    yield
    L.clear()


def _capture():
    """Sustituye el handler por uno que escribe a un buffer y lo devuelve."""
    L._ensure_handler()
    root = logging.getLogger("maquinaria")
    buf = io.StringIO()
    for h in root.handlers:
        h.stream = buf  # type: ignore[attr-defined]
    return buf


def _read_lines(buf: io.StringIO) -> list[dict]:
    buf.seek(0)
    return [json.loads(line) for line in buf.read().splitlines() if line.strip()]


def test_info_emite_json_con_ts_y_level():
    buf = _capture()
    L.info("arranque")
    lines = _read_lines(buf)
    assert len(lines) == 1
    assert lines[0]["msg"] == "arranque"
    assert lines[0]["level"] == "info"
    assert "ts" in lines[0]


def test_extras_aparecen_en_payload():
    buf = _capture()
    L.warn("retry", attempt=2, reason="429")
    lines = _read_lines(buf)
    assert lines[0]["level"] == "warning"
    assert lines[0]["attempt"] == 2
    assert lines[0]["reason"] == "429"


def test_bind_anade_correlation_id_a_siguientes_logs():
    buf = _capture()
    L.bind(correlation_id="M3_001", pipeline="audio")
    L.info("start")
    L.info("end")
    lines = _read_lines(buf)
    assert len(lines) == 2
    for ln in lines:
        assert ln["correlation_id"] == "M3_001"
        assert ln["pipeline"] == "audio"


def test_unbind_quita_la_clave():
    buf = _capture()
    L.bind(correlation_id="X", extra="Y")
    L.info("a")
    L.unbind("extra")
    L.info("b")
    lines = _read_lines(buf)
    assert lines[0]["extra"] == "Y"
    assert "extra" not in lines[1]
    assert lines[1]["correlation_id"] == "X"


def test_clear_limpia_todos_los_bindings():
    buf = _capture()
    L.bind(correlation_id="X")
    L.clear()
    L.info("limpio")
    lines = _read_lines(buf)
    assert "correlation_id" not in lines[0]


def test_with_correlation_es_scoped():
    buf = _capture()
    L.info("antes")
    with L.with_correlation("X-1", pipeline="p"):
        L.info("durante")
    L.info("despues")
    lines = _read_lines(buf)
    assert "correlation_id" not in lines[0]
    assert lines[1]["correlation_id"] == "X-1"
    assert lines[1]["pipeline"] == "p"
    assert "correlation_id" not in lines[2]


def test_error_emite_level_error():
    buf = _capture()
    L.error("fail", exc="ConnError")
    lines = _read_lines(buf)
    assert lines[0]["level"] == "error"
    assert lines[0]["exc"] == "ConnError"


def test_payload_es_json_serializable():
    """Objetos no JSON-serializables (Path) se serializan a str via default."""
    buf = _capture()
    L.info("path", file=ROOT / "x.txt")
    lines = _read_lines(buf)
    assert "x.txt" in lines[0]["file"]

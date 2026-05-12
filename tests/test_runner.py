"""Tests del runner de pipelines."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import runner  # noqa: E402


def test_build_argv_filtra_falsy():
    argv = runner.build_argv(
        "x.py",
        [("--a", "1"), ("--b", True), ("--c", False), ("--d", None), ("--e", "")],
    )
    assert argv[1] == "x.py"
    assert "--a" in argv and "1" in argv
    assert "--b" in argv
    assert "--c" not in argv
    assert "--d" not in argv
    assert "--e" not in argv


def test_preview_command_es_shell_safe():
    cmd = runner.preview_command("x.py", [("--p", "/with space/file.txt")])
    assert "'/with space/file.txt'" in cmd


def test_stream_pipeline_yields_runresult_al_final(tmp_path):
    script = tmp_path / "echo.py"
    script.write_text("print('hola'); print('mundo')\n", encoding="utf-8")

    outputs = []
    result = None
    for item in runner.stream_pipeline(str(script), [], cwd=str(tmp_path)):
        if isinstance(item, runner.RunResult):
            result = item
        else:
            outputs.append(item)

    assert outputs == ["hola", "mundo"]
    assert result is not None
    assert result.returncode == 0
    assert result.duration_s >= 0


def test_stream_pipeline_reporta_exit_code_no_cero(tmp_path):
    script = tmp_path / "fail.py"
    script.write_text("import sys; print('antes'); sys.exit(7)\n", encoding="utf-8")

    result = None
    for item in runner.stream_pipeline(str(script), [], cwd=str(tmp_path)):
        if isinstance(item, runner.RunResult):
            result = item

    assert result is not None
    assert result.returncode == 7

"""Test de integración del sistema de logging.

Simula una corrida de un generador (con AI mockeado) y verifica que la
bitácora central queda correctamente trazada: START/END, pasos, llamadas
IA con tokens, retries, y la auto-validación final.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import daylog
from cockpit.core import log_validator
from cockpit.core.log_helpers import get_run_logger


@pytest.fixture
def tmp_daylog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("DAYLOG_DIR", str(tmp_path))
    return tmp_path


def _today_log_path(daylog_dir: Path) -> Path:
    return daylog_dir / f"maquinaria_{daylog.log_day():%Y-%m-%d}.log"


def _fake_response(in_tok: int, out_tok: int, text: str = "ok"):
    """Construye un objeto similar a una respuesta de Anthropic."""
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(
            input_tokens=in_tok,
            output_tokens=out_tok,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=0,
        ),
    )


def test_generator_run_writes_full_trace(tmp_daylog: Path):
    """Smoke test: una corrida simulada produce todas las líneas esperadas."""

    fake_client = SimpleNamespace(
        messages=SimpleNamespace(
            create=lambda **kw: _fake_response(in_tok=1500, out_tok=800, text="guion fake")
        )
    )

    with daylog.RunLog(script="fake_generador.py", params=["--ep", "M3"]):
        log = get_run_logger("fake_generador")

        log.step("load_spec", spec="PODCAST_M_SPEC.md")
        log.step("extract_concepts", pdf="PDFs/RESUMEN_M3.pdf")

        # Llamada IA simulada (centralizada vía call_claude)
        from guion_common import call_claude

        text, resp = call_claude(
            fake_client,
            model="claude-sonnet-4-5",
            system="...",
            user="...",
            max_tokens=8000,
            temperature=0.7,
            source="fake_generador.py",
            purpose="extract_concepts",
        )
        assert text == "guion fake"
        assert resp.usage.input_tokens == 1500

        log.step("generate", attempts=2)
        log.retry(attempt=2, reason="hard_fails", count=3)

        # Segunda llamada IA con tokens diferentes
        call_claude(
            fake_client,
            model="claude-sonnet-4-5",
            system="...",
            user="...",
            max_tokens=8000,
            temperature=0.7,
            source="fake_generador.py",
            purpose="generate_block",
        )

        log.step("save", path="Guiones/M3_test.txt")
        log.ok("guion guardado", path="Guiones/M3_test.txt", tokens_total=2300)

    text = _today_log_path(tmp_daylog).read_text(encoding="utf-8")

    # --- START / END ---
    assert "[START]" in text
    assert "[END  ]" in text
    assert "status=ok" in text

    # --- pasos esperados ---
    for step in ["load_spec", "extract_concepts", "generate", "save"]:
        assert f"paso → {step}" in text
        assert f"step={step}" in text

    # --- AI calls con tokens ---
    assert text.count("AI call → extract_concepts") == 1
    assert text.count("AI call ok → extract_concepts") == 1
    assert text.count("AI call → generate_block") == 1
    assert "tokens_in=1500" in text
    assert "tokens_out=800" in text
    assert "model=claude-sonnet-4-5" in text

    # --- retry ---
    assert "retry" in text
    assert "attempt=2" in text
    assert "reason=hard_fails" in text

    # --- OK final ---
    assert "guion guardado" in text


def test_generator_run_passes_validator(tmp_daylog: Path):
    """La corrida simulada debe pasar el validador sin issues."""
    fake_client = SimpleNamespace(
        messages=SimpleNamespace(
            create=lambda **kw: _fake_response(in_tok=100, out_tok=50)
        )
    )

    run = daylog.RunLog(script="generar_guion.py", capture_output=False)
    with run:
        log = get_run_logger("generar_guion")
        log.step("load_spec")
        log.step("extract_concepts")
        from guion_common import call_claude
        call_claude(
            fake_client, model="m", system="", user="",
            max_tokens=10, temperature=0.5,
            source="generar_guion.py", purpose="extract_concepts",
        )
        log.step("generate")
        log.step("validate")
        log.step("save")

    report = log_validator.validate_after_run(run.run_id)
    assert report is not None
    assert report.ok, f"issues inesperados: {report.issues}"
    # Sin warnings porque cubrimos todos los pasos esperados
    assert not report.warnings, f"warnings inesperados: {report.warnings}"


def test_generator_with_ai_error_logs_correctly(tmp_daylog: Path):
    """Si una llamada IA falla, el log debe registrarlo y el validador detectarlo."""

    def fail_create(**kw):
        raise RuntimeError("API down")

    fake_client = SimpleNamespace(
        messages=SimpleNamespace(create=fail_create)
    )

    with daylog.RunLog(script="fake_gen.py", capture_output=False):
        log = get_run_logger("fake_gen")
        log.step("extract_concepts")
        from guion_common import call_claude
        with pytest.raises(RuntimeError, match="API down"):
            call_claude(
                fake_client, model="m", system="", user="",
                max_tokens=10, temperature=0.5,
                source="fake_gen.py", purpose="extract_concepts",
            )

    text = _today_log_path(tmp_daylog).read_text(encoding="utf-8")
    assert "AI call → extract_concepts" in text
    assert "AI call error → extract_concepts" in text
    assert "exc_type=RuntimeError" in text


def test_auto_validate_runs_on_close(tmp_daylog: Path):
    """daylog.RunLog.__exit__ invoca al validador y deja warnings si faltan pasos."""
    # Ejecución de generar_guion.py SIN ningún log.step() — el validador
    # debería avisar de que faltan pasos esperados.
    with daylog.RunLog(script="generar_guion.py", capture_output=False):
        pass

    text = _today_log_path(tmp_daylog).read_text(encoding="utf-8")
    # El END ya ocurrió antes de la auto-validación; el INFO de warnings va después.
    assert "auto-validate: warnings" in text
    assert "pasos esperados ausentes" in text


def test_check_run_log_flag_in_evaluador(tmp_daylog: Path, capsys):
    """El CLI del evaluador valida runs cuando se pasa --check-run-log."""
    # Genera una ejecución que pasará la validación.
    with daylog.RunLog(script="generar_guion.py", capture_output=False):
        log = get_run_logger("generar_guion")
        for step in ["load_spec", "extract_concepts", "generate", "validate", "save"]:
            log.step(step)

    from evaluador.cli import main as evaluador_main

    rc = evaluador_main(["--check-run-log", "today"])
    captured = capsys.readouterr()
    assert "Validación de día-log" in captured.out
    # 1 run, sin issues
    assert "[OK]" in captured.out
    assert rc == 0


def test_check_run_log_detects_issues(tmp_daylog: Path, capsys):
    """--check-run-log devuelve 1 cuando algún run tiene issues."""
    try:
        with daylog.RunLog(script="x.py", capture_output=False):
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    from evaluador.cli import main as evaluador_main

    rc = evaluador_main(["--check-run-log", "today"])
    captured = capsys.readouterr()
    assert "[ISSUE]" in captured.out
    assert rc == 1

"""Tests del módulo de verificaciones por episodio."""
from __future__ import annotations

from pathlib import Path

import pytest

from cockpit.core import verifications
from cockpit.core.episodes import Episode


def _make_episode(tmp_path: Path, *,
                  pdf: bool = False, guion_text: str | None = None,
                  escaleta: bool = False, audio_size: int = 0,
                  logs_text: list[str] | None = None) -> Episode:
    pdf_p = None
    if pdf:
        pdf_p = tmp_path / "x.pdf"
        pdf_p.write_bytes(b"%PDF" + b"x" * 20_000)
    guion_p = None
    if guion_text is not None:
        guion_p = tmp_path / "g.txt"
        guion_p.write_text(guion_text, encoding="utf-8")
    esc_p = None
    if escaleta:
        esc_p = tmp_path / "e.md"
        esc_p.write_text("# Escaleta\n" + "bloque " * 50, encoding="utf-8")
    audio_p = None
    if audio_size > 0:
        audio_p = tmp_path / "a.mp3"
        audio_p.write_bytes(b"x" * audio_size)
    logs: list[Path] = []
    if logs_text:
        for i, t in enumerate(logs_text):
            lp = tmp_path / f"l{i}.log"
            lp.write_text(t, encoding="utf-8")
            logs.append(lp)
    return Episode(
        id="M1", module="M1", kind="M", slug="test",
        pdf=pdf_p, guion=guion_p, escaleta=esc_p, audio=audio_p, logs=logs,
    )


def test_ok_episode(tmp_path: Path):
    text = "Iago: hola.\nMaría: qué tal.\n" + "palabra " * 600
    ep = _make_episode(
        tmp_path, pdf=True, guion_text=text,
        escaleta=True, audio_size=400_000,
        logs_text=["INFO ok\n"],
    )
    res = verifications.run_all(ep)
    assert set(res) == {"pdf", "guion", "escaleta", "audio", "logs"}
    assert not verifications.episode_has_errors(ep)


def test_missing_pdf_is_fail(tmp_path: Path):
    ep = _make_episode(tmp_path, pdf=False, guion_text="Iago María x", escaleta=True, audio_size=400_000)
    res = verifications.run_all(ep)
    assert any(c.status == "fail" for c in res["pdf"])
    assert verifications.episode_has_errors(ep)


def test_guion_missing_speaker_is_fail(tmp_path: Path):
    ep = _make_episode(tmp_path, pdf=True, guion_text="solo iago habla " * 200, escaleta=True, audio_size=400_000)
    res = verifications.run_all(ep)
    speaker_check = next(c for c in res["guion"] if c.id == "guion_speakers")
    assert speaker_check.status == "fail"


def test_guion_few_words_is_warn(tmp_path: Path):
    ep = _make_episode(tmp_path, pdf=True, guion_text="Iago hola María corto", escaleta=True, audio_size=400_000)
    res = verifications.run_all(ep)
    words_check = next(c for c in res["guion"] if c.id == "guion_min_words")
    assert words_check.status == "warn"


def test_audio_stub_is_warn(tmp_path: Path):
    text = "Iago María " * 600
    ep = _make_episode(tmp_path, pdf=True, guion_text=text, escaleta=True, audio_size=1000)
    res = verifications.run_all(ep)
    # File present pero pequeño → warn en _file_check
    assert any(c.status == "warn" for c in res["audio"])


def test_logs_detect_errors(tmp_path: Path):
    text = "Iago María " * 600
    ep = _make_episode(
        tmp_path, pdf=True, guion_text=text, escaleta=True, audio_size=400_000,
        logs_text=["INFO ok\nERROR algo falló\nTraceback (most recent call last)\n"],
    )
    res = verifications.run_all(ep)
    log_err = next(c for c in res["logs"] if c.id == "log_errors")
    assert log_err.status == "fail"
    assert verifications.episode_has_errors(ep)


def test_check_result_icons():
    cr_ok = verifications.CheckResult("x", "x", "ok")
    cr_fail = verifications.CheckResult("x", "x", "fail")
    cr_warn = verifications.CheckResult("x", "x", "warn")
    cr_na = verifications.CheckResult("x", "x", "na")
    assert cr_ok.icon == "✅"
    assert cr_fail.icon == "❌"
    assert cr_warn.icon == "⚠️"
    assert cr_na.icon == "⚪"


def test_invalid_status_raises_keyerror():
    cr = verifications.CheckResult("x", "x", "weird")
    with pytest.raises(KeyError):
        _ = cr.icon

"""Tests de generadores/base_generator.py.

Mockea anthropic_client.generate / generate_with_retry para verificar la
pipeline sin red.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores import base_generator as bg  # noqa: E402
from generadores.shared import anthropic_client as ac  # noqa: E402
from validators.result import fail, ok  # noqa: E402


def _ok_result(text: str = "hola mundo"):
    return ac.GenerationResult(
        text=text, model="m", input_tokens=10, output_tokens=5, cost_usd=0.001)


def test_post_process_applies_num2words():
    out = bg.post_process_text("El 80% adopta IA",
                                apply_pronunciation_overrides=False,
                                apply_ssml_pauses=False)
    assert "ochenta" in out.lower()
    assert "80%" not in out


def test_post_process_applies_pronunciation_overrides():
    out = bg.post_process_text("Hablamos de LLM",
                                apply_num2words=False,
                                apply_ssml_pauses=False)
    # Siglas inglesas se deletrean con nombres castellanos: LLM -> "ele ele eme".
    assert "ele ele eme" in out.lower()


def test_post_process_applies_ssml_pauses():
    text = "# HOOK\nIAGO: [directo] Una frase.\n# BLOQUE_PANORAMA\nMARIA: [calido] Sigue.\n"
    out = bg.post_process_text(text,
                                apply_num2words=False,
                                apply_pronunciation_overrides=False)
    assert "<break" in out


def test_run_pipeline_no_validation_no_retry(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "generate",
                         lambda **kw: _ok_result("texto generado"))
    req = bg.PipelineRequest(
        episode_id="M0", kind="M",
        system_prompt="sys", user_prompt="user",
        model="claude-haiku-4-5", repo_root=tmp_path,
        apply_num2words=False, apply_pronunciation_overrides=False,
        apply_ssml_pauses=False,
    )
    result = bg.run_pipeline(req)
    assert result.used_retry is False
    assert result.retry_generation is None
    assert result.final_text == "texto generado"


def test_run_pipeline_does_not_retry_when_validation_passes(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "generate",
                         lambda **kw: _ok_result("guion valido"))

    def validate_fn(text, ep):
        return [ok("dummy", "HARD")]

    req = bg.PipelineRequest(
        episode_id="M0", kind="M",
        system_prompt="s", user_prompt="u",
        model="m", repo_root=tmp_path,
        apply_num2words=False, apply_pronunciation_overrides=False,
        apply_ssml_pauses=False,
        validate_fn=validate_fn,
    )
    result = bg.run_pipeline(req)
    assert result.used_retry is False
    assert not result.is_blocked_by_validation


def test_run_pipeline_retries_once_on_hard_fail(monkeypatch, tmp_path):
    calls = []

    def fake_generate(**kw):
        calls.append(kw["user"])
        return _ok_result(f"intento {len(calls)}")

    monkeypatch.setattr(ac, "generate", fake_generate)

    def validate_fn(text, ep):
        if "intento 1" in text:
            return [fail("rule_x", "HARD", "boom")]
        return [ok("rule_x", "HARD")]

    # Forzamos retry_strategy="full" para que el test compruebe el camino de
    # regeneración completa (sin patch retry intermedio).
    req = bg.PipelineRequest(
        episode_id="M0", kind="M",
        system_prompt="s", user_prompt="u",
        model="m", repo_root=tmp_path,
        apply_num2words=False, apply_pronunciation_overrides=False,
        apply_ssml_pauses=False,
        validate_fn=validate_fn,
        retry_strategy="full",
    )
    result = bg.run_pipeline(req)
    assert result.used_retry is True
    assert result.retry_generation is not None
    assert "intento 2" in result.final_text
    # El 2º prompt llevaba el feedback explicito.
    assert any("FEEDBACK" in c for c in calls)


def test_run_pipeline_uses_patch_retry_when_localized(monkeypatch, tmp_path):
    """Con retry_strategy='auto' y 1 hard localizado, debe intentar patch retry."""
    calls: list[dict] = []
    patch_response = (
        '{"patches": [{"section": "HOOK", "operation": "replace_intervention",'
        ' "intervention_idx": 0, "new_content": "IAGO: nuevo"}]}'
    )
    script_with_section = "# HOOK\nIAGO: hook viejo\n"

    def fake_generate(**kw):
        calls.append(kw)
        # Primera llamada = generación normal del guion.
        if len(calls) == 1:
            return _ok_result(script_with_section)
        # Siguientes = patch retry response (formato JSON).
        return _ok_result(patch_response)

    monkeypatch.setattr(ac, "generate", fake_generate)

    seen_texts: list[str] = []

    def validate_fn(text, ep):
        seen_texts.append(text)
        if "nuevo" not in text:
            return [fail("m_fuentes_count", "HARD", "boom")]
        return [ok("m_fuentes_count", "HARD")]

    req = bg.PipelineRequest(
        episode_id="M0", kind="M",
        system_prompt="s", user_prompt="u",
        model="claude-sonnet-4-5", repo_root=tmp_path,
        apply_num2words=False, apply_pronunciation_overrides=False,
        apply_ssml_pauses=False,
        validate_fn=validate_fn,
    )
    result = bg.run_pipeline(req)
    assert result.patch_retries >= 1
    assert "nuevo" in result.final_text


def test_run_pipeline_tracks_cost(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "generate", lambda **kw: _ok_result())
    req = bg.PipelineRequest(
        episode_id="T1", kind="T",
        system_prompt="s", user_prompt="u",
        model="claude-haiku-4-5", repo_root=tmp_path,
        apply_num2words=False, apply_pronunciation_overrides=False,
        apply_ssml_pauses=False,
    )
    bg.run_pipeline(req)
    log = tmp_path / "costes_generacion.log"
    assert log.exists()
    assert "T1" in log.read_text(encoding="utf-8")


def test_format_hard_failures_feedback_lists_rules():
    results = [
        ok("rule_a", "HARD"),
        fail("rule_b", "HARD", "msg_b"),
        fail("rule_c_soft", "SOFT", "msg_c"),
        fail("rule_d", "HARD", "msg_d"),
    ]
    fb = bg._format_hard_failures_feedback(results)
    assert "- rule_b:" in fb
    assert "- rule_d:" in fb
    # La regla SOFT no aparece como ítem listado.
    assert "- rule_c_soft:" not in fb


def test_run_pipeline_no_retry_when_first_generation_failed(monkeypatch, tmp_path):
    # Si la 1ª generación falla con error (no es hard-fail de validación),
    # no hay texto que validar → no retry.
    monkeypatch.setattr(
        ac, "generate",
        lambda **kw: ac.GenerationResult("", "m", 0, 0, 0.0, error="ratelimited"),
    )

    def validate_fn(text, ep):
        return [fail("x", "HARD", "no se llega aquí")]

    req = bg.PipelineRequest(
        episode_id="S1", kind="S", system_prompt="s", user_prompt="u",
        model="m", repo_root=tmp_path, validate_fn=validate_fn,
        apply_num2words=False, apply_pronunciation_overrides=False,
        apply_ssml_pauses=False,
    )
    result = bg.run_pipeline(req)
    # No hay texto final → no se ejecutó validate → no retry.
    assert result.final_text == ""
    assert result.used_retry is False

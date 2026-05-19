"""Tests del módulo `generadores/patch_retry.py`.

Sin red: mockeamos anthropic_client.generate para verificar el parser de
patches y la lógica de aplicación.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores import patch_retry as pr  # noqa: E402
from generadores.shared import anthropic_client as ac  # noqa: E402
from validators.result import fail, ok  # noqa: E402

SCRIPT_DEMO = """\
# HOOK
IAGO: [contundente] Hook actual.
IAGO: [grave] Esto es MaquinarIA Pesada. Arrancamos.

# BLOQUE_FUENTES
IAGO: [didactico] Vaswani, dos mil diecisiete.
MARIA: [analitica] Lewis, dos mil veinte.

# CIERRE_FINAL
IAGO: [calido] Hasta luego.
"""


def test_split_sections_preserves_order():
    sections = pr._split_sections(SCRIPT_DEMO)
    names = [n for n, _ in sections if n]
    assert names == ["HOOK", "BLOQUE_FUENTES", "CIERRE_FINAL"]


def test_split_interventions_strips_blank_lines():
    body = "\nIAGO: hola\n\nMARIA: hey\n"
    assert pr._split_interventions(body) == ["IAGO: hola", "MARIA: hey"]


def test_apply_patches_replace_section():
    patches = [pr.Patch(
        section="BLOQUE_FUENTES",
        operation="replace_section",
        new_content="IAGO: nueva fuente uno.\nMARIA: nueva fuente dos.\nIAGO: nueva fuente tres.",
    )]
    out = pr.apply_patches(SCRIPT_DEMO, patches)
    assert "nueva fuente uno" in out
    assert "Vaswani" not in out
    # Las otras secciones se preservan.
    assert "Hook actual" in out
    assert "Hasta luego" in out


def test_apply_patches_replace_intervention():
    patches = [pr.Patch(
        section="HOOK", operation="replace_intervention",
        intervention_idx=0,
        new_content="IAGO: [grave] Hook reescrito.",
    )]
    out = pr.apply_patches(SCRIPT_DEMO, patches)
    assert "Hook reescrito" in out
    assert "Hook actual" not in out
    # La 2ª intervención del HOOK sigue.
    assert "Esto es MaquinarIA Pesada" in out


def test_apply_patches_insert_after_intervention():
    patches = [pr.Patch(
        section="BLOQUE_FUENTES", operation="insert_after_intervention",
        intervention_idx=1,
        new_content="IAGO: nueva tercera fuente, dos mil veintitres.",
    )]
    out = pr.apply_patches(SCRIPT_DEMO, patches)
    assert "nueva tercera fuente" in out
    # Las dos originales siguen.
    assert "Vaswani" in out
    assert "Lewis" in out


def test_apply_patches_delete_intervention():
    patches = [pr.Patch(
        section="BLOQUE_FUENTES", operation="delete_intervention",
        intervention_idx=0,
    )]
    out = pr.apply_patches(SCRIPT_DEMO, patches)
    assert "Vaswani" not in out
    assert "Lewis" in out


def test_apply_patches_ignores_unknown_section():
    patches = [pr.Patch(
        section="SECCION_INEXISTENTE", operation="replace_section",
        new_content="x",
    )]
    out = pr.apply_patches(SCRIPT_DEMO, patches)
    # Nada cambia.
    assert "Vaswani" in out
    assert "Hook actual" in out


def test_parse_patches_strips_code_fences():
    raw = """```json
{"patches": [
  {"section": "HOOK", "operation": "replace_intervention",
   "intervention_idx": 0, "new_content": "IAGO: nuevo"}
]}
```"""
    patches = pr._parse_patches(raw)
    assert len(patches) == 1
    assert patches[0].section == "HOOK"
    assert patches[0].intervention_idx == 0


def test_parse_patches_skips_invalid_operations():
    raw = '{"patches": [{"section": "HOOK", "operation": "frobnicate"}]}'
    assert pr._parse_patches(raw) == []


def test_parse_patches_handles_garbage_returns_empty():
    assert pr._parse_patches("no soy json") == []


def test_should_use_patch_retry_rejects_structural_fails():
    results = [fail("required_sections", "HARD", "msg")]
    assert pr.should_use_patch_retry(results) is False


def test_should_use_patch_retry_rejects_too_many_hards():
    results = [fail(f"r{i}", "HARD", "m") for i in range(4)]
    assert pr.should_use_patch_retry(results) is False


def test_should_use_patch_retry_accepts_localized():
    results = [
        fail("m_fuentes_count", "HARD", "msg"),
        ok("otra_regla", "HARD"),
    ]
    assert pr.should_use_patch_retry(results) is True


def test_request_patches_uses_haiku_first(monkeypatch):
    calls: list[str] = []

    def fake_generate(**kwargs):
        calls.append(kwargs["model"])
        return ac.GenerationResult(
            text='{"patches": [{"section": "HOOK", "operation": "replace_intervention", "intervention_idx": 0, "new_content": "IAGO: nuevo"}]}',
            model=kwargs["model"], input_tokens=10, output_tokens=5, cost_usd=0.0001,
        )

    monkeypatch.setattr(ac, "generate", fake_generate)
    patches, gen = pr.request_patches(
        script=SCRIPT_DEMO,
        validation_results=[fail("m_fuentes_count", "HARD", "msg")],
        primary_model="claude-sonnet-4-6",
    )
    assert calls == ["claude-haiku-4-5-20251001"]
    assert len(patches) == 1
    assert gen is not None


def test_request_patches_falls_back_to_sonnet_when_haiku_fails(monkeypatch):
    calls: list[str] = []

    def fake_generate(**kwargs):
        calls.append(kwargs["model"])
        if "haiku" in kwargs["model"]:
            return ac.GenerationResult(
                text="basura no parseable",
                model=kwargs["model"], input_tokens=10, output_tokens=5, cost_usd=0.0,
            )
        return ac.GenerationResult(
            text='{"patches": [{"section": "HOOK", "operation": "delete_intervention", "intervention_idx": 0}]}',
            model=kwargs["model"], input_tokens=10, output_tokens=5, cost_usd=0.0001,
        )

    monkeypatch.setattr(ac, "generate", fake_generate)
    patches, _ = pr.request_patches(
        script=SCRIPT_DEMO,
        validation_results=[fail("m_fuentes_count", "HARD", "msg")],
        primary_model="claude-sonnet-4-6",
    )
    assert calls == ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"]
    assert len(patches) == 1


def test_request_patches_skips_sonnet_fallback_when_primary_is_haiku(monkeypatch):
    calls: list[str] = []

    def fake_generate(**kwargs):
        calls.append(kwargs["model"])
        return ac.GenerationResult(
            text="basura", model=kwargs["model"],
            input_tokens=0, output_tokens=0, cost_usd=0.0,
        )

    monkeypatch.setattr(ac, "generate", fake_generate)
    patches, _ = pr.request_patches(
        script=SCRIPT_DEMO,
        validation_results=[fail("m_fuentes_count", "HARD", "msg")],
        primary_model="claude-haiku-4-5-20251001",
    )
    # No escalamos a Sonnet si el primario ya era Haiku.
    assert calls == ["claude-haiku-4-5-20251001"]
    assert patches == []

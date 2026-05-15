"""Tests del validador S (formato Short)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators import s_validator as sv  # noqa: E402

VALID_S = (
    "¿Cómo sabe un modelo de lenguaje que rey y reina tienen algo en común? "
    "Por esto. Un embedding consiste en convertir cualquier cosa, una palabra, "
    "una imagen o un sonido, en un punto dentro de un espacio matemático "
    "grande y compartido. Las cosas parecidas quedan cerca y las distintas "
    "quedan muy lejos. La geometría del espacio refleja la semántica del "
    "lenguaje, sin que nadie le haya explicado las reglas previas a un "
    "modelo. Imagina un mapa enorme donde rey y reina aparecen al lado, "
    "mesa queda en otro continente y restaurante aparece cerca de comida. "
    "Eso es un embedding, y es la base operativa de la inteligencia "
    "artificial moderna en producción. Cuando le preguntas algo a un "
    "modelo, lo primero que hace es convertir tu frase en un embedding "
    "para buscar respuestas parecidas en su mapa interno construido "
    "durante el entrenamiento del modelo. Sin embeddings no existirían "
    "los buscadores semánticos ni los sistemas de recuperación que usamos "
    "cada día. "
    "Más sobre embeddings en el episodio T de MaquinarIA Pesada."
)


def test_word_count_in_range_passes():
    r = sv.check_word_count(VALID_S)
    assert r.passed is True


def test_word_count_below_min_fails():
    r = sv.check_word_count("Texto muy corto.")
    assert r.passed is False


def test_word_count_above_max_fails():
    text = " ".join(["palabra"] * 250)
    r = sv.check_word_count(text)
    assert r.passed is False


def test_hook_template_pregunta_detected():
    text = "¿Cómo entiende un modelo lo que dices? Por esto. " + VALID_S
    r = sv.check_hook_template(text)
    assert r.passed is True


def test_hook_template_numero_detected():
    text = "El 80 por ciento de los proyectos fallan por esto. " + VALID_S
    r = sv.check_hook_template(text)
    assert r.passed is True


def test_hook_template_contradiccion_detected():
    text = "Los modelos no entienden lo que dicen, pero entender este concepto cambia eso. " + VALID_S
    r = sv.check_hook_template(text)
    assert r.passed is True


def test_hook_template_none_fails():
    # Inicio plano sin contradicción, número ni pregunta.
    text = "Hoy hablamos de un concepto interesante de inteligencia artificial. " + VALID_S
    r = sv.check_hook_template(text)
    assert r.passed is False


def test_closing_canonical_present():
    assert sv.check_closing(VALID_S).passed is True


def test_closing_missing_fails():
    text = VALID_S.replace("Más sobre embeddings en el episodio T de MaquinarIA Pesada.",
                            "Y eso es todo.")
    assert sv.check_closing(text).passed is False


def test_no_dialogue_clean_passes():
    assert sv.check_no_dialogue(VALID_S).passed is True


def test_no_dialogue_detects_speakers():
    text = "IAGO: Hola.\nMARIA: Y yo soy Maria."
    assert sv.check_no_dialogue(text).passed is False


def test_no_tts_tags_clean_passes():
    assert sv.check_no_tts_tags(VALID_S).passed is True


def test_no_tts_tags_detects_tag():
    text = "[didactico] " + VALID_S
    assert sv.check_no_tts_tags(text).passed is False


def test_no_urls_clean_passes():
    assert sv.check_no_urls(VALID_S).passed is True


def test_no_urls_detects_url():
    text = VALID_S + " https://maquinariapesada.com"
    assert sv.check_no_urls(text).passed is False


def test_no_paper_citations_clean_passes():
    assert sv.check_no_paper_citations(VALID_S).passed is True


def test_no_paper_citations_detects_citation():
    text = VALID_S + " Como dijo Vaswani et al. 2017 en su paper."
    assert sv.check_no_paper_citations(text).passed is False


def test_block_count_no_sections_passes():
    assert sv.check_block_count(VALID_S).passed is True


def test_block_count_five_sections_fails():
    text = "\n".join(f"# {n}\nTexto." for n in ["A", "B", "C", "D", "E"])
    assert sv.check_block_count(text).passed is False


def test_filename_correct_format_passes():
    assert sv.check_filename("S7_RAG.mp3").passed is True


def test_filename_wrong_format_fails():
    assert sv.check_filename("RAG.mp3").passed is False
    assert sv.check_filename("S_RAG.mp3").passed is False


def test_filename_none_passes():
    assert sv.check_filename(None).passed is True


def test_voice_parity_odd_iago_passes():
    assert sv.check_voice_parity(1, "IAGO").passed is True


def test_voice_parity_even_maria_passes():
    assert sv.check_voice_parity(2, "MARIA").passed is True


def test_voice_parity_wrong_fails():
    assert sv.check_voice_parity(1, "MARIA").passed is False


def test_brand_mention_only_in_closing_passes():
    assert sv.check_brand_mention_only_in_closing(VALID_S).passed is True


def test_brand_mention_outside_closing_soft_warn():
    text = "Hola, bienvenidos a MaquinarIA Pesada. " + VALID_S
    r = sv.check_brand_mention_only_in_closing(text)
    assert r.passed is False
    assert r.severity == "SOFT"


def test_validate_returns_results_with_no_blocking_for_valid_s():
    results = sv.validate(VALID_S, "S1_Embeddings",
                          s_number=1, voice="IAGO",
                          filename="S1_Embeddings.mp3")
    blocking = [r for r in results if r.is_blocking]
    assert blocking == [], (
        f"Reglas duras fallando para Short válido: "
        f"{[(r.rule_name, r.message) for r in blocking]}"
    )


def test_validate_fails_on_dialogue_format():
    bad = "IAGO: Hola.\nMARIA: Y yo." + VALID_S
    results = sv.validate(bad, "S1_Test", s_number=1, voice="IAGO",
                           filename="S1_Test.mp3")
    blocking_names = {r.rule_name for r in results if r.is_blocking}
    assert "s_no_dialogue" in blocking_names

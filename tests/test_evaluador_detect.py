"""Tests de detección de tipo del evaluador."""

from __future__ import annotations

from evaluador.detect import detect_kind_from_filename, verify_kind_with_content


def test_detect_m_canonical():
    det = detect_kind_from_filename("M3.txt")
    assert det.kind == "M" and det.module_n == 3


def test_detect_m_with_descriptive_suffix():
    det = detect_kind_from_filename("M0_Introduccion_Estrategica.txt")
    assert det.kind == "M" and det.module_n == 0


def test_detect_m_md():
    det = detect_kind_from_filename("M0_v6.md")
    assert det.kind == "M" and det.module_n == 0


def test_detect_t():
    det = detect_kind_from_filename("M3_T2.txt")
    assert det.kind == "T" and det.module_n == 3 and det.tema_n == 2


def test_detect_t_with_suffix():
    det = detect_kind_from_filename("M7_T1_que_es_rag.txt")
    assert det.kind == "T" and det.module_n == 7 and det.tema_n == 1


def test_detect_s():
    det = detect_kind_from_filename("S11_RLHF.txt")
    assert det.kind == "S" and det.s_n == 11


def test_detect_s_md():
    det = detect_kind_from_filename("S1_RAG_v6.md")
    assert det.kind == "S" and det.s_n == 1


def test_detect_unknown():
    det = detect_kind_from_filename("random_file.txt")
    assert det.kind is None


def test_verify_m_content():
    text = "# APLICACION_PRACTICA\nIAGO: [didactico] Bla bla."
    ok, _ = verify_kind_with_content("M", text)
    assert ok


def test_verify_t_content_rejects_aplicacion():
    text = "# BLOQUE_COMO\nIAGO: foo\n# BLOQUE_REALIDAD\nMARIA: bar\n# APLICACION_PRACTICA\n"
    ok, msg = verify_kind_with_content("T", text)
    assert not ok
    assert "APLICACION_PRACTICA" in msg


def test_verify_s_content_rejects_speaker():
    text = "MARIA: hola\nMás sobre rag en el episodio T."
    ok, _ = verify_kind_with_content("S", text)
    assert not ok

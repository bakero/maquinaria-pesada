"""Tests de validators/shared/parity.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators.shared import parity  # noqa: E402


@pytest.mark.parametrize("number,expected", [
    (0, "MARIA"), (1, "IAGO"), (2, "MARIA"), (3, "IAGO"), (14, "MARIA"),
])
def test_opener_for_parity(number, expected):
    assert parity.opener_for(number) == expected


@pytest.mark.parametrize("episode_id,kind,expected", [
    ("M0", "M", 0),
    ("M3", "M", 3),
    ("M3_T2", "T", 2),
    ("M10_T5", "T", 5),
    ("S1", "S", 1),
    ("S7_RAG", "S", 7),
])
def test_number_from_episode_id(episode_id, kind, expected):
    assert parity.number_from_episode_id(episode_id, kind) == expected


def test_number_from_episode_id_invalid_returns_none():
    assert parity.number_from_episode_id("basura", "M") is None
    assert parity.number_from_episode_id("M3", "T") is None


def test_check_opener_m0_maria_ok():
    r = parity.check_opener("M0", "M", "MARIA")
    assert r.passed is True


def test_check_opener_m1_yago_ok():
    r = parity.check_opener("M1", "M", "IAGO")
    assert r.passed is True


def test_check_opener_wrong_speaker_fails():
    r = parity.check_opener("M0", "M", "IAGO")
    assert r.passed is False
    assert r.severity == "HARD"
    assert r.context["expected"] == "MARIA"


def test_check_opener_t_parity_by_tema_number():
    # M8_T1 → tema 1 impar → IAGO
    assert parity.check_opener("M8_T1", "T", "IAGO").passed is True
    # M8_T2 → tema 2 par → MARIA
    assert parity.check_opener("M8_T2", "T", "MARIA").passed is True


def test_check_opener_s_parity_by_s_number():
    assert parity.check_opener("S1_RAG", "S", "IAGO").passed is True
    assert parity.check_opener("S2_Embeddings", "S", "MARIA").passed is True


def test_check_opener_unparseable_id_fails():
    r = parity.check_opener("XXX", "M", "MARIA")
    assert r.passed is False

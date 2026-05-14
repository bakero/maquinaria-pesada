"""Tests de validators/result.py — ValidationResult y summarize."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators.result import ValidationResult, fail, ok, summarize  # noqa: E402


def test_ok_helper_builds_passing_result():
    r = ok("regla_x", "HARD", "todo bien")
    assert r.passed is True
    assert r.severity == "HARD"
    assert r.is_blocking is False


def test_fail_helper_builds_failing_result():
    r = fail("regla_y", "HARD", "algo falla", index=3)
    assert r.passed is False
    assert r.is_blocking is True
    assert r.context["index"] == 3


def test_soft_failure_is_not_blocking():
    r = fail("regla_z", "SOFT", "advertencia")
    assert r.passed is False
    assert r.is_blocking is False


def test_to_dict_roundtrip():
    r = ValidationResult("r", "SOFT", True, "msg", {"k": 1})
    d = r.to_dict()
    assert d == {"rule_name": "r", "severity": "SOFT", "passed": True,
                 "message": "msg", "context": {"k": 1}}


def test_summarize_counts_and_blocking():
    results = [
        ok("a", "HARD"),
        fail("b", "HARD", "x"),
        fail("c", "SOFT", "y"),
        ok("d", "SOFT"),
    ]
    s = summarize(results)
    assert s["total"] == 4
    assert s["passed"] == 2
    assert s["hard_failed"] == 1
    assert s["soft_failed"] == 1
    assert s["blocking"] is True
    assert s["hard_failures"] == ["b"]
    assert s["soft_warnings"] == ["c"]


def test_summarize_no_blocking_when_only_soft_fails():
    s = summarize([ok("a", "HARD"), fail("b", "SOFT", "x")])
    assert s["blocking"] is False

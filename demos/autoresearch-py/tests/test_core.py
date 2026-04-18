"""Tests for AutoResearch core logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import STAGES, NUM_STAGES, run_stage, build_report, run_full  # noqa: E402


def test_stages_constant():
    assert NUM_STAGES == 23
    assert len(STAGES) == 23
    # exactly 4 search-enabled stages
    assert sum(1 for s in STAGES if s["uses_search"]) == 4


def test_run_stage_zero_returns_done():
    res = run_stage("AI in 2026", 0)
    assert res["status"] == "done"
    assert res["stage_idx"] == 0
    assert res["uses_search"] is False
    assert res["search_results"] == []
    assert isinstance(res["log"], list) and res["log"]


def test_run_stage_out_of_range():
    import pytest
    with pytest.raises(IndexError):
        run_stage("x", 99)


def test_non_search_stage_no_results():
    res = run_stage("test", 1)
    assert res["uses_search"] is False
    assert res["search_results"] == []


def test_build_report_contains_topic():
    topic = "Quantum computing outlook"
    results = [run_stage(topic, i) for i in range(3)]
    md = build_report(topic, results, lang="en")
    assert topic in md
    assert "Research Report" in md


def test_build_report_zh():
    topic = "AI 趋势"
    results = [run_stage(topic, 0)]
    md = build_report(topic, results, lang="zh")
    assert topic in md
    assert "研究报告" in md

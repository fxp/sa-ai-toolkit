"""Tests for Org-Uplift engine."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import (  # noqa: E402
    execute_task, compute_stats, classify_bottlenecks,
    get_success_rate, SCENARIOS, BOTTLENECK_LABELS,
)


def test_execute_task_shape():
    res = execute_task("调研AI客服竞品", player="Alice", scenario="newco")
    assert res["task"] == "调研AI客服竞品"
    assert res["player"] == "Alice"
    assert "dice" in res
    assert set(res["dice"].keys()) >= {"roll", "threshold", "success"}
    assert 0 <= res["dice"]["roll"] <= 100
    assert 0 <= res["dice"]["threshold"] <= 100
    assert isinstance(res["dice"]["success"], bool)
    assert res["estimatedHours"] > 0
    assert isinstance(res["bottlenecks"], list) and res["bottlenecks"]


def test_success_curve():
    assert get_success_rate(5) == 0.95
    assert get_success_rate(40) == 0.80
    assert get_success_rate(100) == 0.65
    assert get_success_rate(200) == 0.50
    assert get_success_rate(500) == 0.10
    assert get_success_rate(1000) == 0.05


def test_classify_bottlenecks():
    assert "human-data" in classify_bottlenecks("need to interview customers")
    assert "coordination" in classify_bottlenecks("weekly standup meeting")
    assert classify_bottlenecks("pure dev work") == ["none"]


def test_compute_stats_empty():
    s = compute_stats([])
    assert s["totalTasks"] == 0
    assert s["successRate"] == 0


def test_compute_stats_aggregates():
    tasks = [
        {"dice": {"success": True},  "estimatedHours": 10, "bottlenecks": ["none"]},
        {"dice": {"success": False}, "estimatedHours": 30, "bottlenecks": ["peer-review"]},
        {"dice": {"success": True},  "estimatedHours": 20, "bottlenecks": ["peer-review", "decision"]},
    ]
    s = compute_stats(tasks)
    assert s["totalTasks"] == 3
    assert s["successCount"] == 2
    assert s["successRate"] == 67
    assert s["totalAgentHours"] == 60
    assert s["bottleneckCounts"]["peer-review"] == 2
    assert s["bottleneckCounts"]["decision"] == 1


def test_scenarios_preset():
    assert "newco" in SCENARIOS
    assert "metr" in SCENARIOS
    assert len(SCENARIOS["newco"]["players"]) >= 3


def test_bottleneck_labels_complete():
    for k in ["human-data", "ml-experiment", "peer-review", "external",
              "decision", "coordination", "none"]:
        assert k in BOTTLENECK_LABELS

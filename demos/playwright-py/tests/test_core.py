"""Tests for Playwright demo core."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import simulate_run, SCENARIOS  # noqa: E402


def test_scenarios_four_keys():
    assert set(SCENARIOS.keys()) == {"bing", "github", "form", "responsive"}


def test_simulate_returns_non_empty_trace():
    for name in SCENARIOS:
        trace = simulate_run(name)
        assert isinstance(trace, list) and len(trace) > 0
        for step in trace:
            assert "step" in step
            assert "code_line" in step
            assert "action" in step
            assert "result" in step
            assert "duration_ms" in step


def test_simulate_unknown_scenario_raises():
    import pytest
    with pytest.raises(ValueError):
        simulate_run("nope")


def test_bing_first_action_is_goto():
    trace = simulate_run("bing")
    assert trace[0]["action"] == "goto"
    assert trace[0]["target_url"] and "bing.com" in trace[0]["target_url"]


def test_responsive_contains_viewport_actions():
    trace = simulate_run("responsive")
    viewport_steps = [s for s in trace if s["action"] == "viewport"]
    assert len(viewport_steps) >= 2

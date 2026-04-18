import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import CEOAgent  # noqa: E402


def test_metrics_deterministic_with_seed():
    a = CEOAgent(company="Acme", seed=42)
    b = CEOAgent(company="Acme", seed=42)
    assert a.metrics() == b.metrics()


def test_metrics_same_company_same_result():
    a = CEOAgent(company="FooBar")
    b = CEOAgent(company="FooBar")
    assert a.metrics()["arr"] == b.metrics()["arr"]
    assert a.metrics()["headcount"] == b.metrics()["headcount"]


def test_brief_returns_three():
    a = CEOAgent(company="X")
    for i in range(3):
        brief = a.morning_brief(brief_idx=i)
        assert len(brief) == 3
        assert all("title" in b and "priority" in b for b in brief)


def test_brief_cycles_and_localizes():
    a = CEOAgent(company="X")
    en0 = a.morning_brief(0, "en")
    zh0 = a.morning_brief(0, "zh")
    assert en0 != zh0
    assert a.morning_brief(3, "en") == a.morning_brief(0, "en")  # cycles


def test_mood_shape():
    a = CEOAgent(company="X")
    m = a.mood_heatmap()
    assert len(m["rows"]) == 8
    for row in m["rows"]:
        assert len(row["mood"]) == 5
        assert all(1 <= v <= 5 for v in row["mood"])
    assert len(m["labels"]) == 5


def test_all_has_keys():
    out = CEOAgent(company="X").all()
    for k in ("brief", "metrics", "decisions", "mood", "competitors", "actions"):
        assert k in out

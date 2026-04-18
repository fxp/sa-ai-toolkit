import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import extract_concepts, lint_kb  # noqa: E402


SAMPLE = (
    "Sierra and Decagon are winning customer service by focusing narrowly. "
    "Sierra raised 175M at a 4.5B valuation. "
    "Customer service is the largest AI vertical by spend. "
    "Decagon also competes in support automation. "
    "Knowledge base quality is the real bottleneck for agents. "
    "Companies must invest in cleaning their knowledge base before deploying agents."
)


def test_extract_returns_n_concepts():
    concepts = extract_concepts(SAMPLE, n=4)
    assert isinstance(concepts, list)
    assert len(concepts) == 4
    for c in concepts:
        assert "name" in c and isinstance(c["name"], str) and c["name"]
        assert "summary" in c and isinstance(c["summary"], str)
        assert "cross_links" in c and isinstance(c["cross_links"], list)


def test_extract_empty_text():
    assert extract_concepts("", n=3) == []


def test_lint_detects_orphan_and_short():
    concepts = [
        {"name": "Alpha", "summary": "short", "cross_links": []},
        {"name": "Beta", "summary": "A reasonably long summary about beta concept.", "cross_links": ["Alpha"]},
    ]
    report = lint_kb(concepts)
    assert "Alpha" in report["orphaned"]
    assert "Alpha" in report["short_summaries"]
    assert report["total_issues"] >= 2


def test_lint_detects_duplicates():
    concepts = [
        {"name": "Agent", "summary": "x" * 40, "cross_links": ["B"]},
        {"name": "Agents", "summary": "x" * 40, "cross_links": ["A"]},
    ]
    report = lint_kb(concepts)
    assert report["duplicates"], "expected duplicate pair"


def test_lint_clean_kb():
    concepts = [
        {"name": "Alpha", "summary": "x" * 40, "cross_links": ["Beta"]},
        {"name": "Beta", "summary": "y" * 40, "cross_links": ["Alpha"]},
    ]
    report = lint_kb(concepts)
    assert report["total_issues"] == 0

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import DEMOS, build_runbook_markdown, generate_package, score_demos  # noqa: E402


def _profile(**kw):
    base = {"company": "Test", "industry": "tech", "pain_points": ["km"], "audience": "executives", "minutes": 60, "size": "500-5000"}
    base.update(kw)
    return base


def test_score_returns_14():
    scored = score_demos(_profile())
    assert len(scored) == len(DEMOS) == 14
    assert all("score" in d for d in scored)


def test_matching_industry_raises_score():
    banking_hit = score_demos(_profile(industry="banking", pain_points=["comp"]))
    tech_hit = score_demos(_profile(industry="tech", pain_points=["comp"]))
    compliance_banking = next(d for d in banking_hit if d["id"] == "compliance")
    compliance_tech = next(d for d in tech_hit if d["id"] == "compliance")
    assert compliance_banking["score"] > compliance_tech["score"]


def test_runbook_non_empty_markdown():
    pkg = generate_package(_profile())
    assert "# RUNBOOK" in pkg["runbook"]
    assert len(pkg["selected"]) > 0


def test_sorted_descending():
    scored = score_demos(_profile(pain_points=["km", "collab", "docburden"]))
    scores = [d["score"] for d in scored]
    assert scores == sorted(scores, reverse=True)

"""Enterprise Demo Package Generator.

Scores 14 demo templates against a company profile, picks a schedule that
fits the minute budget, and renders a markdown runbook.
"""
from __future__ import annotations

from typing import Any

try:
    from jinja2 import Template  # type: ignore
    _HAS_JINJA = True
except Exception:  # pragma: no cover
    _HAS_JINJA = False


PAIN_POINTS: dict[str, dict[str, str]] = {
    "doc":       {"en": "Document processing",   "zh": "文档处理"},
    "collab":    {"en": "Collaboration speed",   "zh": "协作效率"},
    "decision":  {"en": "Decision quality",      "zh": "决策质量"},
    "km":        {"en": "Knowledge management",  "zh": "知识管理"},
    "market":    {"en": "Market insights",       "zh": "市场洞察"},
    "talent":    {"en": "Talent shortage",       "zh": "人才短缺"},
    "risk":      {"en": "Risk detection",        "zh": "风险识别"},
    "innov":     {"en": "Innovation cycles",     "zh": "创新周期"},
    "docburden": {"en": "Documentation burden",  "zh": "文档负担"},
    "legacy":    {"en": "Legacy systems",        "zh": "遗留系统"},
    "qc":        {"en": "Quality control",       "zh": "质量管控"},
    "comp":      {"en": "Compliance",            "zh": "合规"},
    "test":      {"en": "Testing automation",    "zh": "测试自动化"},
}


# 14 demos: id, name, target pain points, industry fit (0-10), impact score (0-10), default minutes.
DEMOS: list[dict[str, Any]] = [
    {"id": "autoresearch", "name": "Auto-Research",      "pain": ["market", "decision", "km"],
     "fit": {"banking": 9, "manufacturing": 6, "aerospace": 7, "healthcare": 8, "retail": 8, "consulting": 10, "logistics": 6, "realestate": 7, "energy": 7, "tech": 9},
     "impact": 9, "minutes": 8},
    {"id": "orguplift",    "name": "Org Uplift",         "pain": ["talent", "collab", "innov"],
     "fit": {"banking": 7, "manufacturing": 7, "aerospace": 7, "healthcare": 6, "retail": 6, "consulting": 9, "logistics": 6, "realestate": 6, "energy": 6, "tech": 10},
     "impact": 8, "minutes": 7},
    {"id": "ceodash",      "name": "CEO Dashboard",      "pain": ["decision", "market", "risk"],
     "fit": {"banking": 9, "manufacturing": 8, "aerospace": 8, "healthcare": 7, "retail": 9, "consulting": 8, "logistics": 8, "realestate": 8, "energy": 8, "tech": 9},
     "impact": 9, "minutes": 8},
    {"id": "gstack",       "name": "GStack (DevEx)",     "pain": ["talent", "innov", "test"],
     "fit": {"banking": 5, "manufacturing": 5, "aerospace": 6, "healthcare": 5, "retail": 5, "consulting": 6, "logistics": 5, "realestate": 4, "energy": 5, "tech": 10},
     "impact": 8, "minutes": 8},
    {"id": "hypothesis",   "name": "Hypothesis Testing", "pain": ["innov", "decision", "km"],
     "fit": {"banking": 8, "manufacturing": 7, "aerospace": 7, "healthcare": 8, "retail": 7, "consulting": 10, "logistics": 6, "realestate": 7, "energy": 7, "tech": 9},
     "impact": 7, "minutes": 6},
    {"id": "industrial",   "name": "Industrial AI",      "pain": ["qc", "risk", "legacy"],
     "fit": {"banking": 4, "manufacturing": 10, "aerospace": 10, "healthcare": 6, "retail": 5, "consulting": 5, "logistics": 8, "realestate": 4, "energy": 9, "tech": 7},
     "impact": 10, "minutes": 10},
    {"id": "karpathy",     "name": "Karpathy KB",        "pain": ["km", "docburden", "collab"],
     "fit": {"banking": 8, "manufacturing": 7, "aerospace": 8, "healthcare": 8, "retail": 7, "consulting": 9, "logistics": 7, "realestate": 7, "energy": 7, "tech": 10},
     "impact": 8, "minutes": 7},
    {"id": "maestro",      "name": "Maestro (Mobile)",   "pain": ["test", "qc", "docburden"],
     "fit": {"banking": 8, "manufacturing": 5, "aerospace": 5, "healthcare": 7, "retail": 10, "consulting": 5, "logistics": 7, "realestate": 8, "energy": 5, "tech": 10},
     "impact": 7, "minutes": 6},
    {"id": "playwright",   "name": "Playwright",         "pain": ["test", "qc", "docburden"],
     "fit": {"banking": 8, "manufacturing": 5, "aerospace": 5, "healthcare": 6, "retail": 9, "consulting": 5, "logistics": 7, "realestate": 7, "energy": 5, "tech": 10},
     "impact": 7, "minutes": 6},
    {"id": "pptgen",       "name": "PPT Generator",      "pain": ["docburden", "collab", "km"],
     "fit": {"banking": 8, "manufacturing": 7, "aerospace": 7, "healthcare": 7, "retail": 7, "consulting": 10, "logistics": 7, "realestate": 8, "energy": 7, "tech": 9},
     "impact": 7, "minutes": 5},
    {"id": "entgen",       "name": "Enterprise Gen",     "pain": ["collab", "docburden", "km"],
     "fit": {"banking": 8, "manufacturing": 7, "aerospace": 7, "healthcare": 7, "retail": 7, "consulting": 10, "logistics": 7, "realestate": 7, "energy": 7, "tech": 9},
     "impact": 8, "minutes": 6},
    {"id": "satoolkit",    "name": "SA Toolkit",         "pain": ["collab", "docburden"],
     "fit": {"banking": 7, "manufacturing": 6, "aerospace": 6, "healthcare": 6, "retail": 7, "consulting": 9, "logistics": 6, "realestate": 7, "energy": 6, "tech": 9},
     "impact": 7, "minutes": 5},
    {"id": "compliance",   "name": "Compliance Agent",   "pain": ["comp", "risk", "doc"],
     "fit": {"banking": 10, "manufacturing": 7, "aerospace": 9, "healthcare": 10, "retail": 7, "consulting": 8, "logistics": 7, "realestate": 8, "energy": 9, "tech": 7},
     "impact": 9, "minutes": 8},
    {"id": "onboard",      "name": "Onboarding Agent",   "pain": ["talent", "docburden", "km"],
     "fit": {"banking": 8, "manufacturing": 7, "aerospace": 7, "healthcare": 8, "retail": 8, "consulting": 8, "logistics": 7, "realestate": 7, "energy": 7, "tech": 9},
     "impact": 7, "minutes": 6},
]


def score_demos(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Returns all 14 demos scored and sorted desc by score.

    profile keys: company, industry, pain_points (list of ids), audience, minutes, size
    formula: 0.4 * pain_match + 0.4 * industry_fit + 0.2 * impact
    """
    industry = profile.get("industry", "tech")
    pains: list[str] = list(profile.get("pain_points", []))
    out: list[dict[str, Any]] = []
    for d in DEMOS:
        pain_hits = sum(1 for p in d["pain"] if p in pains)
        pain_match = min(10, pain_hits * (10 / max(1, len(d["pain"]))))
        fit = d["fit"].get(industry, 5)
        impact = d["impact"]
        score = round(0.4 * pain_match + 0.4 * fit + 0.2 * impact, 2)
        out.append({
            "id": d["id"], "name": d["name"], "pain": d["pain"],
            "pain_match": round(pain_match, 2), "industry_fit": fit,
            "impact": impact, "score": score, "minutes": d["minutes"],
        })
    out.sort(key=lambda x: (-x["score"], x["id"]))
    return out


def generate_schedule(scored_demos: list[dict[str, Any]], minutes: int) -> list[dict[str, Any]]:
    """Pick demos in score order until minute budget is full."""
    budget = max(15, int(minutes))
    intro, qa = 5, 10
    remaining = budget - intro - qa
    picked: list[dict[str, Any]] = []
    t = intro
    for d in scored_demos:
        if d["minutes"] > remaining:
            continue
        picked.append({**d, "start": t, "end": t + d["minutes"]})
        t += d["minutes"]
        remaining -= d["minutes"]
        if remaining < 3:
            break
    return picked


_RUNBOOK_TMPL = """# RUNBOOK — {{ profile.company }}

**Industry:** {{ profile.industry }}
**Audience:** {{ profile.audience }}
**Size:** {{ profile.size }}
**Budget:** {{ profile.minutes }} min
**Pain points:** {{ pains_text }}

## Pre-Flight Checklist
- [ ] Verify each demo URL loads ({{ selected|length }} demos)
- [ ] Confirm audience headcount and connection details
- [ ] Load opening slides; test screen share
- [ ] Prepare audience-specific Q&A cards ({{ profile.audience }})

## Demo Walkthrough
{% for d in selected %}
### {{ loop.index }}. {{ d.name }} ({{ d.minutes }} min, {{ d.start }}–{{ d.end }})
- Target pain: {{ d.pain|join(', ') }}
- Score: {{ d.score }} (pain {{ d.pain_match }} / fit {{ d.industry_fit }} / impact {{ d.impact }})
- Hook: "For {{ profile.industry }} teams struggling with {{ d.pain[0] }}, this demo shows how AI cuts cycle time."
- Backup: screenshot fallback in `/screenshots/{{ d.id }}.png`
{% endfor %}

## Post-Demo
- Capture Q&A in shared doc
- Send follow-up within 24h
- Schedule pilot kickoff within 2 weeks
"""


def build_runbook_markdown(profile: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    pains_text = ", ".join(
        PAIN_POINTS.get(p, {"en": p})["en"] for p in profile.get("pain_points", [])
    ) or "(none selected)"
    if _HAS_JINJA:
        return Template(_RUNBOOK_TMPL).render(profile=profile, selected=selected, pains_text=pains_text)
    # Fallback plain-format
    lines = [
        f"# RUNBOOK — {profile.get('company', '')}",
        "",
        f"**Industry:** {profile.get('industry', '')}",
        f"**Audience:** {profile.get('audience', '')}",
        f"**Budget:** {profile.get('minutes', 0)} min",
        f"**Pain points:** {pains_text}",
        "",
        "## Demo Walkthrough",
    ]
    for i, d in enumerate(selected, 1):
        lines.append(f"### {i}. {d['name']} ({d['minutes']} min)")
        lines.append(f"- Score: {d['score']}")
        lines.append(f"- Pains: {', '.join(d['pain'])}")
    return "\n".join(lines)


def build_profile_markdown(profile: dict[str, Any]) -> str:
    pains_text = ", ".join(
        PAIN_POINTS.get(p, {"en": p})["en"] for p in profile.get("pain_points", [])
    ) or "(none)"
    return (
        f"# {profile.get('company', 'Company')} — Profile\n\n"
        f"**Industry:** {profile.get('industry', 'tech')}\n"
        f"**Size:** {profile.get('size', 'n/a')}\n"
        f"**Audience:** {profile.get('audience', 'executives')}\n"
        f"**Length:** {profile.get('minutes', 90)} minutes\n"
        f"**Pain points:** {pains_text}\n\n"
        f"## Snapshot\n{profile.get('company', '')} is a player in the "
        f"{profile.get('industry', 'tech')} industry. This profile is user-supplied.\n"
    )


def build_matrix_markdown(scored: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| {i+1} | {d['name']} | {d['pain_match']}/10 | {d['industry_fit']}/10 | {d['impact']}/10 | **{d['score']}** |"
        for i, d in enumerate(scored)
    )
    return (
        f"# Scoring Matrix ({len(scored)} demos)\n\n"
        "| # | Demo | Pain Match | Industry Fit | Impact | **Score** |\n"
        "|---|------|-----------:|-------------:|-------:|----------:|\n"
        f"{rows}\n\n"
        "**Formula:** `score = 0.4 × pain_match + 0.4 × industry_fit + 0.2 × impact`"
    )


def build_schedule_markdown(profile: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| {i+1} | {d['start']}–{d['end']} min | **{d['name']}** | {', '.join(d['pain'])} | {d['score']} |"
        for i, d in enumerate(selected)
    )
    return (
        f"# Presentation Schedule — {profile.get('minutes', 90)} min\n\n"
        f"**Audience:** {profile.get('audience', 'executives')} · "
        f"**Demos:** {len(selected)}\n\n"
        "| Slot | Time | Demo | Focus | Score |\n"
        "|------|------|------|-------|------:|\n"
        f"{rows}\n\n"
        f"## Opening Remarks\nWelcome {profile.get('company', 'team')}. "
        f"Today we'll walk through {len(selected)} concrete AI applications tailored to "
        f"{profile.get('industry', 'your industry')}."
    )


def generate_package(profile: dict[str, Any]) -> dict[str, Any]:
    scored = score_demos(profile)
    selected = generate_schedule(scored, int(profile.get("minutes", 90)))
    return {
        "profile": build_profile_markdown(profile),
        "matrix": build_matrix_markdown(scored),
        "schedule": build_schedule_markdown(profile, selected),
        "runbook": build_runbook_markdown(profile, selected),
        "company": profile.get("company", ""),
        "scored": scored,
        "selected": selected,
    }

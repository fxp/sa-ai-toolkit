"""SA Toolkit — Gen / Customize / Present modules."""
from __future__ import annotations

import copy
import html
import re
from typing import Any

try:
    from jinja2 import Template  # type: ignore
    _HAS_JINJA = True
except Exception:  # pragma: no cover
    _HAS_JINJA = False

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


# ------------------------- Gen -------------------------

_INDUSTRY_HINTS = [
    ("banking",       ["bank", "金融", "pay", "fund", "capital"]),
    ("tech",          ["tech", "tencent", "alibaba", "baidu", "lab", "bytedance", "openai"]),
    ("healthcare",    ["health", "medical", "药", "医", "pharma", "bio"]),
    ("retail",        ["retail", "mart", "shop", "mall", "小米"]),
    ("manufacturing", ["factory", "steel", "manuf", "制造", "motor"]),
    ("aerospace",     ["aero", "航空", "空客", "boeing"]),
    ("logistics",     ["logistics", "express", "运输", "快递"]),
    ("energy",        ["energy", "oil", "电力", "power"]),
    ("consulting",    ["consult", "mckinsey", "deloitte"]),
]


def _guess_industry(name: str) -> str:
    low = name.lower()
    for ind, keys in _INDUSTRY_HINTS:
        if any(k in low for k in keys):
            return ind
    return "tech"


_PRESETS: dict[str, dict[str, Any]] = {
    "default": {
        "products": ["flagship platform", "cloud services", "consumer apps"],
        "competitors": ["major peers in the industry"],
    },
    "tencent": {
        "industry": "tech",
        "products": ["WeChat", "QQ", "Tencent Cloud", "Tencent Games"],
        "competitors": ["Alibaba", "ByteDance", "Baidu"],
        "size": ">50000",
    },
    "alibaba": {
        "industry": "tech",
        "products": ["Taobao", "Tmall", "Alibaba Cloud", "Alipay (Ant)"],
        "competitors": ["JD.com", "Pinduoduo", "Tencent"],
        "size": ">50000",
    },
}


def search_company(name: str) -> dict[str, Any]:
    """Best-effort company snapshot.

    Tries DuckDuckGo instant answer; falls back to built-in presets / generic.
    Always returns {name, industry, products, competitors, size, summary}.
    """
    key = name.strip().lower()
    preset = _PRESETS.get(key) or _PRESETS["default"]
    industry = preset.get("industry") or _guess_industry(name)
    summary = f"{name} is a recognized player in the {industry} industry."
    if requests is not None:
        try:
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": name, "format": "json", "no_html": "1"},
                timeout=3,
            )
            if r.ok:
                j = r.json()
                abstract = (j.get("AbstractText") or "").strip()
                if abstract:
                    summary = abstract[:600]
        except Exception:
            pass
    return {
        "name": name,
        "industry": industry,
        "products": list(preset.get("products", _PRESETS["default"]["products"])),
        "competitors": list(preset.get("competitors", _PRESETS["default"]["competitors"])),
        "size": preset.get("size", "5000-50000"),
        "summary": summary,
    }


def _load_entgen():
    """Load enterprise-gen core.py by path (avoids `core` module name clash)."""
    import importlib.util
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "enterprise-gen-py", "core.py")
    path = os.path.normpath(path)
    spec = importlib.util.spec_from_file_location("entgen_core", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


def generate_package(company_info: dict[str, Any]) -> dict[str, Any]:
    """Build a demo package from a company info dict."""
    entgen = _load_entgen()
    if entgen is not None:
        score_demos = entgen.score_demos
        generate_schedule = entgen.generate_schedule
        _profile_md = entgen.build_profile_markdown
        _matrix = entgen.build_matrix_markdown
        _sched = entgen.build_schedule_markdown
        _runbook = entgen.build_runbook_markdown
    else:
        score_demos = generate_schedule = _profile_md = _matrix = _sched = _runbook = None  # type: ignore

    profile = {
        "company": company_info.get("name", "Acme"),
        "industry": company_info.get("industry", "tech"),
        "pain_points": company_info.get("pain_points") or ["km", "collab", "docburden"],
        "audience": company_info.get("audience", "executives"),
        "minutes": int(company_info.get("minutes", 90)),
        "size": company_info.get("size", "500-5000"),
    }
    if score_demos and generate_schedule and _profile_md and _matrix and _sched and _runbook:
        scored = score_demos(profile)
        selected = generate_schedule(scored, profile["minutes"])
        scoring = _matrix(scored)
        schedule = _sched(profile, selected)
        profile_md = _profile_md(profile)
        runbook = _runbook(profile, selected)
    else:
        scored = []
        selected = []
        scoring = "# Scoring\n(scoring engine unavailable)"
        schedule = "# Schedule\n(unavailable)"
        profile_md = f"# {profile['company']}\nIndustry: {profile['industry']}"
        runbook = "# Runbook\n(unavailable)"

    opening = (
        f"# Opening Remarks\n\nWelcome to the {profile['company']} AI-adoption walkthrough.\n\n"
        f"Today we'll show you {len(selected)} concrete demos tailored to {profile['industry']} — "
        "each one ties directly to a business pain we've seen teams like yours struggle with. "
        "You'll leave with a ranked list of what to pilot first and a rough 90-day rollout plan.\n\n"
    )
    if selected:
        opening += f"Let's begin with **{selected[0]['name']}**."

    return {
        "company": profile["company"],
        "industry": profile["industry"],
        "audience": profile["audience"],
        "snapshot": {
            "name": profile["company"],
            "industry": profile["industry"],
            "products": company_info.get("products", []),
            "competitors": company_info.get("competitors", []),
            "summary": company_info.get("summary", ""),
        },
        "profile": profile_md,
        "scoring": scoring,
        "schedule": schedule,
        "opening_remarks": opening,
        "scored": scored,
        "selected": selected,
    }


# ------------------------- Customize -------------------------

_TEXT_KEYS = ("profile", "scoring", "schedule", "opening_remarks")


def replace_terms(package: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    out = copy.deepcopy(package)
    for k in _TEXT_KEYS:
        if isinstance(out.get(k), str):
            for frm, to in mapping.items():
                if frm:
                    out[k] = out[k].replace(frm, to)
    return out


def deepen_demo(package: dict[str, Any], demo_id: str) -> dict[str, Any]:
    """Regenerate/extend a single demo section (marked [DEEP] + extra notes)."""
    out = copy.deepcopy(package)
    for d in out.get("selected", []):
        if d.get("id") == demo_id or d.get("name") == demo_id:
            d["deep"] = True
            d["notes"] = (
                f"Extended for {out.get('industry', 'your industry')}: "
                "integration patterns, ROI benchmarks, customer reference scenarios, "
                "risk/compliance talk-track, 90-day pilot outline."
            )
            out["opening_remarks"] += (
                f"\n\n> Deep-dive prepared for **{d.get('name', demo_id)}** — "
                "extended scenarios available on request."
            )
            break
    return out


def switch_audience(package: dict[str, Any], audience: str) -> dict[str, Any]:
    tone = {
        "executives":  "ROI, strategic timeline, and risk framing",
        "engineering": "architecture deep-dives and integration patterns",
        "business":    "workflow impact and user-journey framing",
        "allhands":    "vision-first narrative with light technical coverage",
    }.get(audience, "balanced framing")
    out = copy.deepcopy(package)
    out["audience"] = audience
    out["opening_remarks"] = (
        f"# Opening Remarks ({audience})\n\n"
        f"Tailored for **{audience}** — emphasizing {tone}.\n\n"
        f"Welcome to the {out.get('company', 'session')} walkthrough."
    )
    # Re-render schedule note
    out["schedule"] = re.sub(
        r"\*\*Audience:\*\* [^·\n]+", f"**Audience:** {audience} ", out.get("schedule", ""),
    ) or out.get("schedule", "")
    return out


# ------------------------- Present -------------------------

def rehearse(package: dict[str, Any]) -> list[dict[str, Any]]:
    selected = package.get("selected", [])
    plays: list[dict[str, Any]] = []
    plays.append({
        "step": "opening",
        "title": "Opening Remarks",
        "seconds": 60,
        "script": package.get("opening_remarks", ""),
    })
    for i, d in enumerate(selected, 1):
        plays.append({
            "step": f"demo-{i}",
            "title": d.get("name", f"Demo {i}"),
            "seconds": int(d.get("minutes", 5)) * 60,
            "script": (
                f"Frame pain ({', '.join(d.get('pain', []))}). "
                f"Run end-to-end. Call out ROI moment. "
                + ("[DEEP mode] " + d.get("notes", "") if d.get("deep") else "")
            ).strip(),
        })
    plays.append({
        "step": "qa",
        "title": "Q&A + Next steps",
        "seconds": 600,
        "script": "Capture questions, schedule pilot kickoff, send follow-up email within 24h.",
    })
    return plays


_EMAIL_TMPL = """Subject: Thank you — {{ company }} AI walkthrough follow-up

Hi team,

Thanks for the time today. As promised, here is a crisp recap.

Three takeaways:
{% for d in top3 %}{{ loop.index }}. {{ d.name }} — {{ d.pain|join(', ') }}
{% endfor %}
{% if top3 %}Three action items:
- [ ] Identify a pilot owner for {{ top3[0].name }} by end of week
{% if top3|length > 1 %}- [ ] Share technical requirements doc for {{ top3[1].name }}
{% endif %}{% if top3|length > 2 %}- [ ] Schedule a working session with {{ top3[2].name }} team
{% endif %}{% endif %}
Happy to jump on a 30-min follow-up anytime.

Best,
Your SA
"""


def export_email(package: dict[str, Any]) -> str:
    top3 = (package.get("selected") or [])[:3]
    if _HAS_JINJA:
        return Template(_EMAIL_TMPL).render(company=package.get("company", "team"), top3=top3)
    # Plain fallback
    lines = [
        f"Subject: Thank you — {package.get('company', 'team')} AI walkthrough follow-up",
        "",
        "Hi team,",
        "",
        "Three takeaways:",
    ]
    for i, d in enumerate(top3, 1):
        lines.append(f"{i}. {d.get('name', '')} — {', '.join(d.get('pain', []))}")
    lines.append("")
    lines.append("Best,")
    lines.append("Your SA")
    return "\n".join(lines)


# Convenience: safely escape for HTML preview if needed by callers
def _escape(s: str) -> str:
    return html.escape(s or "")

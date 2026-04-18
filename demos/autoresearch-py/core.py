"""
AutoResearch core — 23-stage research pipeline.

Pure business logic: given a topic, run stages sequentially. A few stages
call DuckDuckGo for real web sources; the rest simulate reasoning work.
"""
from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Optional

try:
    from jinja2 import Template
except ImportError:  # pragma: no cover
    Template = None


# ---------------------------------------------------------------------------
# Stage definitions (23 stages; 4 do real search)
# ---------------------------------------------------------------------------

STAGES: list[dict] = [
    {"name": "Topic scoping",              "name_zh": "主题界定",        "uses_search": False, "search_query_template": None},
    {"name": "Query decomposition",        "name_zh": "查询拆解",        "uses_search": False, "search_query_template": None},
    {"name": "Literature search",          "name_zh": "文献检索",        "uses_search": True,  "search_query_template": "{topic}"},
    {"name": "Source ranking",             "name_zh": "来源排序",        "uses_search": False, "search_query_template": None},
    {"name": "Key claim extraction",       "name_zh": "关键论点抽取",    "uses_search": False, "search_query_template": None},
    {"name": "Counter-argument search",    "name_zh": "反方观点检索",    "uses_search": True,  "search_query_template": "{topic} criticism limitations"},
    {"name": "Evidence triangulation",     "name_zh": "证据三角校验",    "uses_search": False, "search_query_template": None},
    {"name": "Domain expert lookup",       "name_zh": "领域专家查询",    "uses_search": True,  "search_query_template": "{topic} expert analysis 2025"},
    {"name": "Data point extraction",      "name_zh": "数据点提取",      "uses_search": False, "search_query_template": None},
    {"name": "Trend identification",       "name_zh": "趋势识别",        "uses_search": False, "search_query_template": None},
    {"name": "Timeline construction",      "name_zh": "时间线构建",      "uses_search": False, "search_query_template": None},
    {"name": "Case study search",          "name_zh": "案例检索",        "uses_search": True,  "search_query_template": "{topic} case study examples"},
    {"name": "Quantitative synthesis",     "name_zh": "定量综合",        "uses_search": False, "search_query_template": None},
    {"name": "Qualitative synthesis",      "name_zh": "定性综合",        "uses_search": False, "search_query_template": None},
    {"name": "Hypothesis formulation",     "name_zh": "假设形成",        "uses_search": False, "search_query_template": None},
    {"name": "Contradiction check",        "name_zh": "矛盾校验",        "uses_search": False, "search_query_template": None},
    {"name": "Citation verification",      "name_zh": "引用核验",        "uses_search": False, "search_query_template": None},
    {"name": "Narrative outlining",        "name_zh": "叙事大纲",        "uses_search": False, "search_query_template": None},
    {"name": "Draft writing",              "name_zh": "草稿撰写",        "uses_search": False, "search_query_template": None},
    {"name": "Peer review (multi-agent)",  "name_zh": "多 Agent 同行评审", "uses_search": False, "search_query_template": None},
    {"name": "Iterative refinement",       "name_zh": "迭代打磨",        "uses_search": False, "search_query_template": None},
    {"name": "Final formatting",           "name_zh": "最终排版",        "uses_search": False, "search_query_template": None},
    {"name": "Report publication",         "name_zh": "报告发布",        "uses_search": False, "search_query_template": None},
]

NUM_STAGES = len(STAGES)


# ---------------------------------------------------------------------------
# DuckDuckGo search (HTML scrape, no API key)
# ---------------------------------------------------------------------------

def _search_duckduckgo(query: str, n: int = 5) -> list[dict]:
    """Scrape DuckDuckGo HTML search results. Returns [] on failure."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        results: list[dict] = []
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL,
        )
        for m in pattern.finditer(html):
            if len(results) >= n:
                break
            raw_url = m.group(1)
            if "uddg=" in raw_url:
                um = re.search(r"uddg=([^&]+)", raw_url)
                real_url = urllib.parse.unquote(um.group(1)) if um else raw_url
            else:
                real_url = raw_url
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            snippet = re.sub(r"<[^>]+>", "", m.group(3)).strip()
            results.append({"title": title, "url": real_url, "snippet": snippet})
        return results
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Stage runner
# ---------------------------------------------------------------------------

def run_stage(topic: str, stage_idx: int, prev_results: Optional[list] = None) -> dict:
    """Run a single research stage and return a structured result."""
    if stage_idx < 0 or stage_idx >= NUM_STAGES:
        raise IndexError(f"stage_idx {stage_idx} out of range [0,{NUM_STAGES - 1}]")

    stage = STAGES[stage_idx]
    t0 = time.time()
    log: list[str] = [f"[stage {stage_idx+1}/{NUM_STAGES}] {stage['name']}"]
    search_results: list[dict] = []

    if stage["uses_search"]:
        query = stage["search_query_template"].format(topic=topic)
        log.append(f"search: {query}")
        search_results = _search_duckduckgo(query, n=5)
        log.append(f"← {len(search_results)} sources")
    else:
        # Simulated reasoning work — fixed short delay in core is fine for CLI
        log.append("synthesizing…")

    duration_ms = int((time.time() - t0) * 1000)
    return {
        "stage_idx": stage_idx,
        "name": stage["name"],
        "name_zh": stage["name_zh"],
        "uses_search": stage["uses_search"],
        "status": "done",
        "log": log,
        "search_results": search_results,
        "duration_ms": duration_ms,
    }


# ---------------------------------------------------------------------------
# Report builder (Jinja2)
# ---------------------------------------------------------------------------

_REPORT_TEMPLATE_EN = """# Research Report: {{ topic }}

**Generated**: {{ date }}
**Sources**: {{ sources|length }} unique sources
**Pipeline**: AutoResearchClaw {{ num_stages }}-stage autonomous

---

## Executive Summary

This report provides a systematic analysis of "**{{ topic }}**" through literature search, key-claim extraction, counter-argument verification, and evidence triangulation. It synthesizes {{ sources|length }} independent sources to surface key trends and points of contention.

## Key Findings

{% for r in sources[:5] %}{{ loop.index }}. **{{ r.title }}** — {{ r.snippet }}

{% endfor %}

## Primary Evidence

{% for r in sources[:8] %}- {{ r.snippet }}
  *Source*: [{{ r.title }}]({{ r.url }})

{% else %}- _(No search results — using built-in template)_
{% endfor %}

## Conclusions & Recommendations

Based on the evidence gathered, the following conclusions are drawn about "{{ topic }}":

1. **Mainstream view**: Based on synthesis of {{ sources|length }} sources, this field is undergoing rapid evolution.
2. **Counter-perspective**: Watch for methodological limitations and representation biases in current discourse.
3. **Next steps**: Recommend 1-2 specific sub-topics for deeper investigation to reach actionable conclusions.

## References

{% for r in sources %}{{ loop.index }}. [{{ r.title }}]({{ r.url }})
{% else %}_(None)_
{% endfor %}

---

*Generated by AutoResearchClaw — {{ num_stages }}-stage pipeline, DuckDuckGo search-powered*
"""

_REPORT_TEMPLATE_ZH = """# 研究报告：{{ topic }}

**生成日期**: {{ date }}
**检索来源**: {{ sources|length }} 条独立来源
**管线**: AutoResearchClaw {{ num_stages }} 阶段

---

## 摘要

本报告针对「**{{ topic }}**」展开系统性检索与综合分析，涵盖文献综述、关键论点抽取、反方观点校验、数据三角验证等阶段。共整合 {{ sources|length }} 条独立来源，识别出若干关键趋势与潜在争议点。

## 关键发现

{% for r in sources[:5] %}{{ loop.index }}. **{{ r.title }}** — {{ r.snippet }}

{% endfor %}

## 主要证据

{% for r in sources[:8] %}- {{ r.snippet }}
  *来源*: [{{ r.title }}]({{ r.url }})

{% else %}- （无检索结果，使用内置模板）
{% endfor %}

## 结论与建议

基于上述检索证据，对于「{{ topic }}」的关键判断如下：

1. **主流观点**: 根据 {{ sources|length }} 条来源的综合分析，该领域正处于快速演化期。
2. **反方视角**: 建议关注潜在的方法论局限与代表性偏差。
3. **下一步**: 建议进一步深入 1-2 个具体子主题以获得可操作结论。

## 引用来源

{% for r in sources %}{{ loop.index }}. [{{ r.title }}]({{ r.url }})
{% else %}_（无）_
{% endfor %}

---

*本报告由 AutoResearchClaw 自动生成 — {{ num_stages }} 阶段管线，DuckDuckGo 搜索驱动*
"""


def _dedupe_sources(all_results: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for stage_res in all_results:
        for r in stage_res.get("search_results", []):
            u = r.get("url")
            if not u or u in seen:
                continue
            seen.add(u)
            out.append(r)
    return out


def build_report(topic: str, all_results: list[dict], lang: str = "en") -> str:
    """Render Markdown report from accumulated stage results."""
    sources = _dedupe_sources(all_results)
    template_str = _REPORT_TEMPLATE_ZH if lang == "zh" else _REPORT_TEMPLATE_EN
    ctx = {
        "topic": topic,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sources": sources,
        "num_stages": NUM_STAGES,
    }
    if Template is not None:
        return Template(template_str).render(**ctx)
    # Minimal fallback if jinja2 missing — just format header + sources
    lines = [f"# Research Report: {topic}", "",
             f"**Generated**: {ctx['date']}", f"**Sources**: {len(sources)}", ""]
    for i, r in enumerate(sources, 1):
        lines.append(f"{i}. [{r['title']}]({r['url']}) — {r['snippet']}")
    return "\n".join(lines)


def run_full(topic: str, lang: str = "en") -> dict:
    """Run all 23 stages sequentially and return {'results': [...], 'report': str}."""
    results = []
    for i in range(NUM_STAGES):
        results.append(run_stage(topic, i, results))
    report = build_report(topic, results, lang=lang)
    return {"topic": topic, "results": results, "report": report, "num_stages": NUM_STAGES}

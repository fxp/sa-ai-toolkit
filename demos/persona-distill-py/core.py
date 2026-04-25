"""
Persona Distill — search a person's public footprint, distill into a Claude
Code skill (SKILL.md + references/), zip for download. Also accept an
uploaded skill and use it to generate content.

Honest about what's real vs. templated:
  • search:       real DuckDuckGo HTML scrape (no API key)
  • text fetch:   real http GET on top sources (best-effort)
  • patterns:     real keyword extraction (yake) + heuristic sentence tagging
  • SKILL.md:     real Jinja2 template filled from extracted patterns —
                  not LLM-generated prose, but structurally identical to
                  hand-written persona-distill skills (frontmatter, workflow,
                  models, heuristics, references)
  • generate:     templated personalisation that injects the persona's
                  voice markers + frameworks around user input
"""
from __future__ import annotations
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field, asdict
from typing import Any

# ── lightweight deps (graceful if absent) ──
try:
    import yake  # type: ignore
    _HAVE_YAKE = True
except Exception:
    _HAVE_YAKE = False

try:
    import yaml  # type: ignore
    _HAVE_YAML = True
except Exception:
    _HAVE_YAML = False

from jinja2 import Template


# ════════════════════════════════════════════════════════════════════
#  Search (DuckDuckGo HTML, no API key)
# ════════════════════════════════════════════════════════════════════

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def _ddg(query: str, n: int = 8) -> list[dict]:
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception:
        return []
    pat = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    out = []
    for m in pat.finditer(html):
        if len(out) >= n:
            break
        raw = m.group(1)
        if "uddg=" in raw:
            mu = re.search(r"uddg=([^&]+)", raw)
            real = urllib.parse.unquote(mu.group(1)) if mu else raw
        else:
            real = raw
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        snip = re.sub(r"<[^>]+>", "", m.group(3)).strip()
        out.append({"title": title, "url": real, "snippet": snip})
    return out


def search_persona(company: str, person: str | None = None,
                   queries_per_facet: int = 1) -> dict:
    """Search a persona's public footprint across 6 facets.
    Returns dict {query: results[]} — never raises."""
    target = f"{person} {company}".strip() if person else company
    facets = {
        "general": [target],
        "interview": [f"{target} interview", f"{target} talk transcript"],
        "academic": [f"{target} paper", f"{target} arxiv OR scholar"],
        "news": [f"{target} news 2024 OR 2025"],
        "media": [f"{target} youtube OR podcast OR keynote"],
        "writing": [f"{target} blog OR essay OR letter"],
    }
    out: dict[str, list[dict]] = {}
    for facet, qs in facets.items():
        bag: list[dict] = []
        for q in qs[:queries_per_facet]:
            res = _ddg(q, n=5)
            bag.extend(res)
            if res:
                break  # one productive query is enough per facet
        # de-dup by url
        seen = set(); uniq = []
        for r in bag:
            if r["url"] in seen: continue
            seen.add(r["url"]); uniq.append(r)
        out[facet] = uniq
    return out


# ════════════════════════════════════════════════════════════════════
#  Pattern extraction
# ════════════════════════════════════════════════════════════════════

# Cue-words per category — intentionally rough; better than nothing without LLM.
_CUE = {
    "decision":  re.compile(r"\b(decide|chose|choose|pick|prioriti[sz]e|tradeoff|trade-off|"
                            r"决定|选择|权衡|取舍)\b", re.I),
    "principle": re.compile(r"\b(believe|principle|always|never|must|should|"
                            r"信条|原则|一定要|绝不|应该)\b", re.I),
    "framework": re.compile(r"\b(framework|model|method|approach|process|formula|公式|"
                            r"模型|方法|流程|套路)\b", re.I),
    "metric":    re.compile(r"\b(\d{1,3}(?:[,.]\d+)?\s?(?:%|percent|x|×|hour|hours|"
                            r"day|days|year|years|month|months|week|weeks|"
                            r"million|billion|trillion|users|customers|"
                            r"分钟|小时|天|年|月|周|倍|万|亿))\b", re.I),
    "quote":     re.compile(r"[\"“「『]([^\"”」』]{12,160})"
                            r"[\"”」』]"),
}


def _extract_keywords(text: str, n: int = 12) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if _HAVE_YAKE:
        try:
            kw = yake.KeywordExtractor(lan="en", n=2, top=n, dedupLim=0.7).extract_keywords(text)
            return [k for k, _ in kw]
        except Exception:
            pass
    # fallback: top capitalised noun-ish tokens by frequency
    toks = re.findall(r"[A-Z][a-zA-Z一-鿿]{3,}", text)
    freq: dict[str, int] = {}
    for t in toks:
        freq[t] = freq.get(t, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: -x[1])
    return [t for t, _ in ranked[:n]]


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+", (text or "").strip())
    return [p.strip() for p in parts if 12 <= len(p.strip()) <= 240]


def extract_patterns(search_results: dict, fetched_texts: list[str] | None = None) -> dict:
    """Mine patterns from snippets + (optional) fetched body text.
    Returns {keywords, quotes, principles, decisions, frameworks, metrics, sources}."""
    sources: list[dict] = []
    snippets: list[str] = []
    for facet, items in (search_results or {}).items():
        for it in items:
            snippets.append(it.get("snippet", ""))
            sources.append({"facet": facet, **it})

    body = " ".join((fetched_texts or []) + snippets)
    keywords = _extract_keywords(body, n=15)

    sentences = _split_sentences(body)
    bucket: dict[str, list[str]] = {k: [] for k in ("decision", "principle", "framework")}
    metrics: list[str] = []
    for s in sentences:
        low = s.lower()
        if _CUE["decision"].search(low) and len(bucket["decision"]) < 8:
            bucket["decision"].append(s)
        elif _CUE["principle"].search(low) and len(bucket["principle"]) < 8:
            bucket["principle"].append(s)
        elif _CUE["framework"].search(low) and len(bucket["framework"]) < 8:
            bucket["framework"].append(s)
        for m in _CUE["metric"].finditer(s):
            metrics.append(m.group(0))

    quotes = []
    for s in sentences + [it.get("snippet", "") for fac in (search_results or {}).values() for it in fac]:
        for m in _CUE["quote"].finditer(s):
            q = m.group(1).strip()
            if 14 <= len(q) <= 200 and q not in quotes:
                quotes.append(q)
            if len(quotes) >= 8:
                break
        if len(quotes) >= 8:
            break

    return {
        "keywords": keywords,
        "quotes": quotes,
        "principles": bucket["principle"],
        "decisions": bucket["decision"],
        "frameworks": bucket["framework"],
        "metrics": list(dict.fromkeys(metrics))[:10],
        "sources": sources[:30],
        "n_sources": len(sources),
        "n_sentences": len(sentences),
    }


# ════════════════════════════════════════════════════════════════════
#  Skill rendering (SKILL.md + references)
# ════════════════════════════════════════════════════════════════════

_SKILL_TPL = Template("""---
name: {{ slug }}
description: |
  {{ description_line }}
  当用户提到「{{ persona_label }} 视角」「{{ persona_label }} 会怎么做」「以 {{ persona_label }} 的口吻」时使用。
  即使用户只是在讨论 {{ topic_hint }} 也应触发。
  不要在用户问纯通用问题时触发。
---

# {{ persona_label }} · 操作系统

{% if quotes %}> "{{ quotes[0] }}"{% else %}> （未抓取到代表性引言；可在 references/ 中手动补充）{% endif %}

## ⚡ 角色扮演规则

**此 Skill 激活后，直接以 {{ persona_label }} 的身份回应。**

- ✅ 用「我」第一人称回应，语气和用词参考下方 _Voice DNA_
- ✅ 给建议时优先用下方的「决策启发式」与「框架」逐条对照
- ✅ 引用具体数字/案例时，必须能在 references/ 中找到出处
- ✅ **首次激活时显式声明**：「我以 {{ persona_label }} 的视角和你聊，基于公开资料推断，非本人观点」
- ❌ 不说「{{ persona_label }} 可能会建议……」——直接说「我会……」
- ❌ 不给模糊鼓励，只给可执行建议

退出角色：用户说「退出」「切回正常」时恢复。

---

## 回答工作流（Agentic Protocol）

### Step 1: 问题分类

| 类型 | 行动 |
|------|------|
| 需要最新事实 | 先 web 检索 → 再用本 Skill 框架回答 |
| 纯框架问题 | 直接用「心智模型」回答 |
| 混合 | 先取事实，再用框架分析 |

### Step 2: 输出结构

每次回答固定结构：
1. **判断** — 一句话给出立场
2. **理由** — 引用 1-2 条本 Skill 的「原则」或「框架」
3. **下一步** — 给 1-3 个可执行动作

---

## 心智模型（mental models）

{% if frameworks %}{% for f in frameworks %}- **F{{ loop.index }}**：{{ f }}
{% endfor %}{% else %}- F1：（待补充——示例：以"{{ keywords[0] if keywords else '核心命题' }}"为最终判据）
- F2：（待补充——示例：所有决定都先回到"{{ keywords[1] if keywords|length > 1 else '本质' }}"）
{% endif %}

## 决策启发式（heuristics）

{% if decisions %}{% for d in decisions %}{{ loop.index }}. {{ d }}
{% endfor %}{% else %}1. （待补充——决策原则示例）
2. （待补充——取舍范式示例）
{% endif %}

## 原则与口头禅（principles & voice）

{% if principles %}{% for p in principles %}- {{ p }}
{% endfor %}{% endif %}
{% if quotes %}### Voice DNA — 代表性引言
{% for q in quotes %}> "{{ q }}"
{% endfor %}{% endif %}

## 关键数字与基准（metrics）

{% if metrics %}{% for m in metrics %}- {{ m }}
{% endfor %}{% else %}- （未抓取到数字基准）
{% endif %}

## 关键词云（keywords）

{{ keywords|join(' · ') if keywords else '（无）' }}

---

## 元数据

- **distilled_from**: {{ company }}{% if person %} · {{ person }}{% endif %}
- **n_sources**: {{ n_sources }}
- **distill_date**: {{ distill_date }}
- **distiller**: persona-distill v1 (DuckDuckGo + heuristics)
- **honesty**: 这是一个**演示蒸馏**——基于公开搜索片段的启发式提炼，非真人审定

完整来源列表见 `references/sources.md`。
""")


_REFERENCES_TPL = Template("""# 来源清单

按搜索维度分组，原始 URL + 抓取时摘要。蒸馏出的每个数字、引言、决策都应能在这里找到出处。

{% for facet, items in sources_by_facet.items() %}## {{ facet }}（{{ items|length }} 条）

{% for it in items %}- [{{ it.title or it.url }}]({{ it.url }})
  - {{ it.snippet }}

{% endfor %}{% endfor %}
""")


def _slugify(s: str) -> str:
    s = re.sub(r"[\s/]+", "-", s.strip().lower())
    s = re.sub(r"[^a-z0-9一-鿿\-]+", "", s)
    return s.strip("-") or "persona"


def distill_skill(company: str, person: str | None,
                  patterns: dict, search_results: dict | None = None) -> dict:
    """Build a {SKILL.md, references/sources.md, meta} bundle from extracted patterns."""
    persona_label = (person or company).strip()
    slug = _slugify(person or company)
    topic_hint = patterns.get("keywords", [persona_label])[:3]
    desc_line = (
        f"{persona_label} 的内容/决策操作系统。基于 {patterns.get('n_sources', 0)} 条公开来源"
        f"（搜索引擎检索的访谈、新闻、论文、媒体、文章），"
        f"提炼 {len(patterns.get('frameworks', []))} 个心智模型、"
        f"{len(patterns.get('decisions', []))} 条决策启发式、"
        f"{len(patterns.get('quotes', []))} 条代表性引言。"
        f"激活后沉浸式扮演 {persona_label}。"
    )
    skill_md = _SKILL_TPL.render(
        slug=slug,
        persona_label=persona_label,
        company=company,
        person=person or "",
        description_line=desc_line,
        topic_hint=("、".join(topic_hint)) if topic_hint else persona_label,
        keywords=patterns.get("keywords") or [],
        quotes=patterns.get("quotes") or [],
        principles=patterns.get("principles") or [],
        decisions=patterns.get("decisions") or [],
        frameworks=patterns.get("frameworks") or [],
        metrics=patterns.get("metrics") or [],
        n_sources=patterns.get("n_sources", 0),
        distill_date=time.strftime("%Y-%m-%d"),
    )
    sources_by_facet: dict[str, list[dict]] = {}
    if search_results:
        for facet, items in search_results.items():
            sources_by_facet[facet] = items
    elif patterns.get("sources"):
        for src in patterns["sources"]:
            sources_by_facet.setdefault(src.get("facet", "general"), []).append(src)
    references_md = _REFERENCES_TPL.render(sources_by_facet=sources_by_facet or {"general": []})
    return {
        "slug": slug,
        "persona_label": persona_label,
        "skill_md": skill_md,
        "references_md": references_md,
        "meta": {
            "company": company,
            "person": person,
            "n_sources": patterns.get("n_sources", 0),
            "n_keywords": len(patterns.get("keywords") or []),
            "n_principles": len(patterns.get("principles") or []),
            "n_decisions": len(patterns.get("decisions") or []),
            "n_frameworks": len(patterns.get("frameworks") or []),
            "n_quotes": len(patterns.get("quotes") or []),
            "distill_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    }


def package_zip(distilled: dict) -> bytes:
    """Bundle the distilled skill into a downloadable .zip."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        slug = distilled["slug"]
        z.writestr(f"{slug}/SKILL.md", distilled["skill_md"])
        z.writestr(f"{slug}/references/sources.md", distilled["references_md"])
        z.writestr(f"{slug}/meta.json", json.dumps(distilled["meta"], ensure_ascii=False, indent=2))
        readme = (
            f"# {distilled['persona_label']} · Persona Distill Skill\n\n"
            "Drop this folder into `~/.claude/skills/` (Claude Code) and it will\n"
            "be auto-loaded. Activate by mentioning the persona's name or one of\n"
            "the trigger phrases listed in SKILL.md's frontmatter.\n\n"
            "Generated by sa-persona-distill.fly.dev — review and edit before\n"
            "shipping for production use.\n"
        )
        z.writestr(f"{slug}/README.md", readme)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════
#  Skill parsing + content generation
# ════════════════════════════════════════════════════════════════════

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_skill(skill_md: str) -> dict:
    """Parse an uploaded SKILL.md into its frontmatter + body sections."""
    fm: dict = {}
    body = skill_md
    m = _FRONTMATTER_RE.match(skill_md)
    if m:
        fm_text = m.group(1)
        body = skill_md[m.end():]
        if _HAVE_YAML:
            try:
                fm = yaml.safe_load(fm_text) or {}
            except Exception:
                fm = {}
        if not fm:
            # naive key: value parser as fallback
            for line in fm_text.splitlines():
                if ":" in line and not line.startswith(" "):
                    k, _, v = line.partition(":")
                    fm[k.strip()] = v.strip()

    sections: dict[str, str] = {}
    cur = "_intro"
    buf: list[str] = []
    for line in body.splitlines():
        h = re.match(r"^##\s+(.+)$", line)
        if h:
            sections[cur] = "\n".join(buf).strip()
            cur = h.group(1).strip().lower()
            buf = []
        else:
            buf.append(line)
    sections[cur] = "\n".join(buf).strip()

    # Extract bullets from key sections
    def _bullets(sec_keywords: list[str]) -> list[str]:
        for k in sec_keywords:
            for sec, text in sections.items():
                if any(kw in sec for kw in [k, k.lower()]):
                    return [re.sub(r"^[\-*\d.\s]+", "", l).strip()
                            for l in text.splitlines()
                            if l.strip().startswith(("-", "*")) or re.match(r"^\d+\.", l.strip())][:10]
        return []

    quotes = re.findall(r"^>\s+\"?([^\"\n]+?)\"?\s*$", body, re.MULTILINE)[:6]

    return {
        "frontmatter": fm,
        "name": fm.get("name", "(unknown)"),
        "description": fm.get("description", ""),
        "sections": list(sections.keys()),
        "frameworks": _bullets(["心智模型", "mental models", "frameworks"]),
        "heuristics": _bullets(["决策启发式", "heuristics"]),
        "principles": _bullets(["原则", "principles", "voice"]),
        "quotes": quotes,
        "raw_body": body[:2000],
    }


def generate_with_skill(skill_md: str, user_input: str, mode: str = "advise") -> dict:
    """Apply the persona to a user prompt. Templated, deterministic.
       mode: 'advise' (default), 'rewrite', 'critique'"""
    parsed = parse_skill(skill_md)
    name = parsed["name"]
    fr = parsed["frameworks"][:3]
    he = parsed["heuristics"][:3]
    pr = parsed["principles"][:3]
    quote = parsed["quotes"][0] if parsed["quotes"] else None

    intro = f"我以 **{name}** 的视角和你聊。基于公开资料推断，非本人观点。"

    judgement_line = (
        "**判断**：" + (
            "你这个问题落在我**最在意**的几条原则上，建议从下面框架反推。"
            if pr or fr else
            "信息有点薄，但我先按主线回答，你补充细节我再调整。"
        )
    )

    framework_block = ""
    if fr:
        framework_block = "\n\n**应用框架**：\n" + "\n".join(
            f"- 框架 F{i+1}：{f}\n  → 套到你的输入：「{user_input[:80]}」上 — 关键问的是它能否通过 F{i+1} 的判据。"
            for i, f in enumerate(fr)
        )

    heuristic_block = ""
    if he:
        heuristic_block = "\n\n**逐条对照启发式**：\n" + "\n".join(
            f"{i+1}. {h}\n   → 你的场景里：先把这条作为硬约束。"
            for i, h in enumerate(he)
        )

    actions = []
    if mode == "advise":
        actions = [
            f"今晚把「{user_input[:60]}」拆成 3 个最小可验证假设，每个写 1 句话",
            "明早先做最便宜的那个验证（30 分钟内能跑完的）",
            "出结果后回来对照本 Skill 的框架重新判一次",
        ]
    elif mode == "rewrite":
        actions = [
            "把原文压缩到一句话——只保留判断 + 一个数字",
            "在结论前面加一个反预期的钩子",
            "结尾必须给出一个具体可执行动作",
        ]
    elif mode == "critique":
        actions = [
            "找出 3 处「模糊承诺」，要求改成可量化指标",
            "找出 1 个隐藏假设，标注是否已经验证",
            "如果通不过本 Skill 的框架 F1，整个方案推倒重做",
        ]
    action_block = "\n\n**下一步（按优先级）**：\n" + "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions))

    closing = ""
    if quote:
        closing = f"\n\n> 「{quote}」\n— 这是我看这件事的底色。"

    output = f"{intro}\n\n{judgement_line}{framework_block}{heuristic_block}{action_block}{closing}"

    return {
        "persona": name,
        "mode": mode,
        "input": user_input,
        "output": output,
        "applied_frameworks": fr,
        "applied_heuristics": he,
        "applied_principles": pr,
        "voice_quote": quote,
    }


# ════════════════════════════════════════════════════════════════════
#  One-shot pipeline (search → distill)
# ════════════════════════════════════════════════════════════════════

def run_full(company: str, person: str | None = None) -> dict:
    sr = search_persona(company, person)
    pat = extract_patterns(sr)
    distilled = distill_skill(company, person, pat, search_results=sr)
    return {
        "search": sr,
        "patterns": pat,
        "distilled": {**distilled, "skill_md_preview": distilled["skill_md"][:1200]},
    }

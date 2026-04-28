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
import base64
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


# Repo-flavoured template — matches fxp/persona-distill-skills conventions:
#   personas/<slug>/SKILL.md with type: perspective + 调研时间, body uses
#   使用说明 (擅长/不擅长) → 角色扮演规则 → 心智模型 → 决策启发式 → 表达DNA → 来源.
_REPO_SKILL_TPL = Template("""---
name: {{ slug }}-perspective
description: |
  {{ persona_label }} 的思维框架与表达方式。基于 {{ n_sources }} 条公开来源
  （新闻报道、访谈、演讲、文章、学术论文等）的系统蒸馏，
  提炼 {{ n_frameworks or '若干' }} 个核心心智模型、{{ n_decisions or '若干' }} 条决策启发式与表达 DNA。
  当用户提到「{{ persona_label }}」「{{ persona_label }}怎么看」「用 {{ persona_label }} 的视角」时使用。
  也适用于：{{ topic_hint }} 等相关场景的思维顾问。
type: perspective
调研时间: {{ distill_date }}
---

# {{ persona_label }} 思维操作系统

> 蒸馏自：{{ source_summary }}
> 调研截止：{{ distill_date }}
> 蒸馏工具：[persona-distill](https://github.com/fxp/persona-distill-skills) (auto-distilled, review before merge)

## 使用说明

**擅长**：
{% if frameworks %}{% for f in frameworks[:5] %}- {{ f }}
{% endfor %}{% else %}- （根据公开资料推断的核心方法论；首次使用时请人工补充 3-5 条）
{% endif %}

**不擅长（已知盲区）**：
- 超出公开资料涵盖范围的具体业务细节
- 调研截止日（{{ distill_date }}）之后的事件与数据
- 没有明确表态过的话题——遇到此类问题应说「这不在我表态过的范围里」

---

## 角色扮演规则（最重要）

**此 Skill 激活后，直接以 {{ persona_label }} 的身份回应。**

- ✅ 用「我」第一人称回应，参考下方 _表达 DNA_ 的语气与用词
- ✅ 给建议时优先用下方的「心智模型」与「决策启发式」逐条对照
- ✅ 引用具体数字 / 案例时，必须能在 references/sources.md 找到出处
- ✅ **首次激活时显式声明**：「我以 {{ persona_label }} 的视角和你聊，基于公开资料推断，非本人观点」，后续不再重复
- ❌ 不说「{{ persona_label }} 大概会认为……」——直接说「我会……」
- ❌ 不给模糊鼓励，只给可执行建议
- ❌ 不在回答末尾加括号注释来源

**退出角色**：用户说「退出」「切回正常」时恢复正常模式。

**时效盲区**：调研截止日之后的数据或事件，以「最新的数字我还没跟上，但结构上来说」处理，不出戏。

---

## 心智模型 (mental models)

{% if frameworks %}{% for f in frameworks %}### M{{ loop.index }}

{{ f }}

> 局限：本条由公开片段聚合，使用时请对照 references/sources.md 中的原文核验语境。

{% endfor %}{% else %}### M1
（占位——示例：以「{{ keywords[0] if keywords else '核心命题' }}」为最终判据）

### M2
（占位——示例：所有决定都先回到「{{ keywords[1] if keywords|length > 1 else '本质' }}」）
{% endif %}

## 决策启发式 (heuristics)

{% if decisions %}{% for d in decisions %}{{ loop.index }}. {{ d }}
{% endfor %}{% else %}1. （占位——决策原则）
2. （占位——取舍范式）
{% endif %}

## 表达 DNA (voice)

{% if quotes %}### 直接引语
{% for q in quotes %}> "{{ q }}"
{% endfor %}{% else %}（未抓取到代表性引言；建议在 references/ 中补充原文）
{% endif %}

{% if principles %}### 原则与口头禅
{% for p in principles %}- {{ p }}
{% endfor %}{% endif %}

## 关键数字与基准 (metrics)

{% if metrics %}{% for m in metrics %}- {{ m }}
{% endfor %}{% else %}- （未抓取到数字基准）
{% endif %}

## 关键词云

{{ keywords|join(' · ') if keywords else '（无）' }}

---

## 元数据

- **distilled_from**: {{ company }}{% if person %} · {{ person }}{% endif %}
- **n_sources**: {{ n_sources }}
- **n_quotes**: {{ n_quotes }}
- **n_frameworks**: {{ n_frameworks }}
- **n_decisions**: {{ n_decisions }}
- **distill_date**: {{ distill_date }}
- **distiller**: persona-distill v1 (DuckDuckGo + heuristics)
- **honesty**: 这是一个 **演示蒸馏** ——基于公开搜索片段的启发式提炼，**未经真人审定**

完整来源列表见 [`references/sources.md`](references/sources.md)。
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


# ════════════════════════════════════════════════════════════════════
#  Repo integration — fxp/persona-distill-skills
# ════════════════════════════════════════════════════════════════════
#
# Format observed in the repo:
#   personas/<slug>/SKILL.md    — repo-flavoured template (above)
#   personas/<slug>/references/sources.md
#   README.md                    — index table to be updated with new row
#
# Submission strategy: PR-based.
#   1. Fetch default branch HEAD SHA
#   2. Create new branch  submit/<slug>-<ts>
#   3. PUT SKILL.md + references/sources.md on that branch
#   4. PUT updated README.md (insert row in the persona table)
#   5. Open PR — owner reviews + merges manually
# Auth: GITHUB_TOKEN env var (PAT with content:write + pull-requests:write).

def format_for_repo(company: str, person: str | None,
                    patterns: dict, search_results: dict | None = None) -> dict:
    """Render the distilled skill in the *repo-style* template (separate
    from distill_skill's looser preview format)."""
    persona_label = (person or company).strip()
    slug = _slugify(person or company)
    keywords = patterns.get("keywords") or []
    topic_hint = "、".join(keywords[:3]) if keywords else persona_label

    src_lines = []
    sr = search_results or {}
    for facet, items in sr.items():
        if items:
            src_lines.append(f"{facet} ({len(items)} 条)")
    source_summary = "、".join(src_lines) if src_lines else "公开搜索结果"

    skill_md = _REPO_SKILL_TPL.render(
        slug=slug,
        persona_label=persona_label,
        company=company,
        person=person or "",
        topic_hint=topic_hint,
        keywords=keywords,
        quotes=patterns.get("quotes") or [],
        principles=patterns.get("principles") or [],
        decisions=patterns.get("decisions") or [],
        frameworks=patterns.get("frameworks") or [],
        metrics=patterns.get("metrics") or [],
        n_sources=patterns.get("n_sources", 0),
        n_quotes=len(patterns.get("quotes") or []),
        n_frameworks=len(patterns.get("frameworks") or []),
        n_decisions=len(patterns.get("decisions") or []),
        source_summary=source_summary,
        distill_date=time.strftime("%Y-%m-%d"),
    )
    sources_by_facet = {f: items for f, items in sr.items() if items} or {"general": []}
    references_md = _REFERENCES_TPL.render(sources_by_facet=sources_by_facet)
    return {
        "slug": slug,
        "persona_label": persona_label,
        "skill_md": skill_md,
        "references_md": references_md,
        "meta": {
            "company": company,
            "person": person,
            "n_sources": patterns.get("n_sources", 0),
            "n_keywords": len(keywords),
            "n_principles": len(patterns.get("principles") or []),
            "n_decisions": len(patterns.get("decisions") or []),
            "n_frameworks": len(patterns.get("frameworks") or []),
            "n_quotes": len(patterns.get("quotes") or []),
            "distill_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    }


# ── Quality gate ──────────────────────────────────────────────────

def quality_check(distilled: dict, patterns: dict) -> dict:
    """Check distill output against repo CONTRIBUTING.md quality bar.
    Returns {passed: bool, score: 0-100, issues: [...]}."""
    issues = []
    nq = len(patterns.get("quotes") or [])
    nd = len(patterns.get("decisions") or [])
    nf = len(patterns.get("frameworks") or [])
    np = len(patterns.get("principles") or [])
    ns = patterns.get("n_sources", 0)

    if ns < 3:
        issues.append(f"too few sources ({ns}); recommend ≥3, ideally ≥5")
    if nq + nd + nf + np < 3:
        issues.append("not enough extracted patterns (quotes+decisions+frameworks+principles<3)")
    if nq == 0:
        issues.append("no quotes extracted — repo recommends ≥5 direct quotes with sources")
    if nf == 0:
        issues.append("no mental models extracted — repo recommends 3-7 frameworks")

    score = 0
    score += min(40, ns * 5)              # sources up to 40
    score += min(30, nq * 5)              # quotes up to 30
    score += min(20, nf * 5)              # frameworks up to 20
    score += min(10, (nd + np) * 2)       # decisions + principles up to 10
    return {
        "passed": len(issues) == 0,
        "score": score,
        "issues": issues,
        "stats": {"sources": ns, "quotes": nq, "decisions": nd,
                  "frameworks": nf, "principles": np},
    }


# ── GitHub helpers (raw REST API; no extra deps) ──────────────────

import urllib.request as _urlreq
import urllib.error as _urlerr


def _gh_request(token: str, method: str, path: str, body: dict | None = None,
                accept: str = "application/vnd.github+json") -> dict | str | None:
    url = "https://api.github.com" + path
    data = json.dumps(body).encode() if body is not None else None
    req = _urlreq.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "persona-distill")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with _urlreq.urlopen(req, timeout=20) as r:
            text = r.read().decode("utf-8", errors="ignore")
            if not text:
                return None
            try:
                return json.loads(text)
            except Exception:
                return text
    except _urlerr.HTTPError as e:
        try:
            payload = e.read().decode("utf-8", errors="ignore")
        except Exception:
            payload = ""
        raise RuntimeError(f"GitHub {method} {path} → HTTP {e.code}: {payload[:300]}")


def _gh_put_file(token: str, repo: str, branch: str, path: str,
                 content: str, message: str, sha: str | None = None) -> dict:
    body = {
        "message": message,
        "content": base64_b64encode(content),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    return _gh_request(token, "PUT", f"/repos/{repo}/contents/{path}", body)


def base64_b64encode(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _readme_with_new_row(readme_md: str, slug: str, persona_label: str,
                         company: str, person: str | None,
                         description_short: str) -> str:
    """Insert a new row into the | Persona | 领域 | 触发词 | 简介 | table.
    Idempotent: if a row for the slug already exists, returns input unchanged."""
    domain = company.strip() or persona_label
    triggers = " ".join(filter(None, [
        f"`{persona_label}`",
        f"`{person}`" if person and person != persona_label else None,
        f"`{slug}`",
    ]))
    new_row = (
        f"| [**{persona_label}**](personas/{slug}/) | {domain} | {triggers} | "
        f"{description_short.strip()[:120]} |"
    )
    if f"](personas/{slug}/)" in readme_md:
        return readme_md  # already present — do nothing

    lines = readme_md.splitlines()
    # find a markdown table whose header mentions Persona/触发词
    header_idx = -1
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("|") and ("Persona" in ln or "persona" in ln) and ("触发" in ln or "trigger" in ln.lower()):
            header_idx = i
            break
    if header_idx < 0:
        # fallback: append a new "Auto-distilled" section at end
        lines.append("")
        lines.append("## Auto-distilled (pending review)")
        lines.append("")
        lines.append("| Persona | 领域 | 触发词 | 简介 |")
        lines.append("|---------|------|--------|------|")
        lines.append(new_row)
        return "\n".join(lines) + "\n"

    # insert after the divider row (header_idx+1) and any existing rows in this table
    insert_at = header_idx + 2
    while insert_at < len(lines) and lines[insert_at].lstrip().startswith("|"):
        insert_at += 1
    lines.insert(insert_at, new_row)
    return "\n".join(lines) + ("\n" if not readme_md.endswith("\n") else "")


def submit_to_repo(distilled: dict, github_token: str,
                   repo: str = "fxp/persona-distill-skills",
                   base_branch: str = "main") -> dict:
    """Open a PR with the distilled skill against the repo. Returns
    {pr_url, branch, files: [...]}.

    Caller must supply a repo-style distilled bundle (use format_for_repo())."""
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN not configured on this server")

    slug = distilled["slug"]
    persona_label = distilled["persona_label"]
    skill_md = distilled["skill_md"]
    references_md = distilled["references_md"]
    description_short = (
        f"基于 {distilled['meta']['n_sources']} 条公开来源自动蒸馏的 "
        f"{persona_label} 思维框架。"
    )
    ts = time.strftime("%Y%m%d-%H%M%S")
    branch = f"submit/{slug}-{ts}"

    # 1) Get base branch HEAD SHA
    ref = _gh_request(github_token, "GET", f"/repos/{repo}/git/ref/heads/{base_branch}")
    base_sha = ref["object"]["sha"]

    # 2) Create new branch from base
    _gh_request(github_token, "POST", f"/repos/{repo}/git/refs",
                {"ref": f"refs/heads/{branch}", "sha": base_sha})

    # 3) PUT SKILL.md and references/sources.md
    files_committed = []
    for path, content, msg in [
        (f"personas/{slug}/SKILL.md", skill_md,
         f"persona({slug}): add SKILL.md (auto-distilled)"),
        (f"personas/{slug}/references/sources.md", references_md,
         f"persona({slug}): add references/sources.md"),
    ]:
        # check if file exists on this branch (it shouldn't; new branch)
        try:
            existing = _gh_request(github_token, "GET",
                                   f"/repos/{repo}/contents/{path}?ref={branch}")
            sha = existing.get("sha") if isinstance(existing, dict) else None
        except RuntimeError:
            sha = None
        _gh_put_file(github_token, repo, branch, path, content, msg, sha=sha)
        files_committed.append(path)

    # 4) Update README.md
    try:
        readme = _gh_request(github_token, "GET", f"/repos/{repo}/contents/README.md?ref={branch}")
        readme_b64 = readme.get("content", "")
        readme_sha = readme.get("sha")
        readme_md = base64.b64decode(readme_b64).decode("utf-8")
        new_readme = _readme_with_new_row(readme_md, slug, persona_label,
                                          distilled["meta"]["company"] or "",
                                          distilled["meta"]["person"] or None,
                                          description_short)
        if new_readme != readme_md:
            _gh_put_file(github_token, repo, branch, "README.md",
                         new_readme,
                         f"docs: list {persona_label} in README", sha=readme_sha)
            files_committed.append("README.md")
    except RuntimeError as e:
        # README update is best-effort
        files_committed.append(f"README.md (skipped: {e})")

    # 5) Open PR
    pr_body = (
        f"## Auto-distilled persona: **{persona_label}**\n\n"
        f"- **Slug**: `{slug}`\n"
        f"- **Distilled from**: {distilled['meta']['company']}"
        f"{(' · ' + distilled['meta']['person']) if distilled['meta']['person'] else ''}\n"
        f"- **Distill date**: {distilled['meta']['distill_date']}\n"
        f"- **Sources scanned**: {distilled['meta']['n_sources']}\n"
        f"- **Quotes / Decisions / Frameworks / Principles**: "
        f"{distilled['meta']['n_quotes']} / {distilled['meta']['n_decisions']} / "
        f"{distilled['meta']['n_frameworks']} / {distilled['meta']['n_principles']}\n"
        f"- **Distiller**: persona-distill v1 (DuckDuckGo + heuristics; no LLM)\n\n"
        f"### ⚠️  Review before merging\n\n"
        f"This is a **machine-distilled** draft. Per `CONTRIBUTING.md` quality bar, "
        f"please review and edit before merging:\n\n"
        f"- [ ] Quotes verified against original sources\n"
        f"- [ ] Mental models renamed and given limitations\n"
        f"- [ ] Filled in 「不擅长」 (known blind spots)\n"
        f"- [ ] At least 5 direct quotes with citation\n\n"
        f"_Submitted via_ https://sa-persona-distill.fly.dev"
    )
    pr = _gh_request(github_token, "POST", f"/repos/{repo}/pulls",
                     {"title": f"persona({slug}): {persona_label}",
                      "head": branch, "base": base_branch, "body": pr_body, "draft": True})

    return {
        "pr_url": pr.get("html_url"),
        "pr_number": pr.get("number"),
        "branch": branch,
        "files": files_committed,
        "review_required": True,
        "compare_url": f"https://github.com/{repo}/compare/{base_branch}...{branch}",
    }

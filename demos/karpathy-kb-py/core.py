"""Karpathy LLM-Wiki style knowledge-base extractor.

Models after Karpathy's "brain maintenance" workflow:

  raw/  (immutable sources)
   │
   ▼  extract_concepts()        ── deterministic, source-attributed
  wiki/ (concepts: entity + attributes + evidence + cross-links)
   │
   ▼  lint_kb()                 ── orphans, contradictions, unsourced
  outputs/ (reports, briefs, ...)

Each "concept" carries:
  name          — entity / claim / opinion / metric surface form
  type          — entity | metric | claim | opinion | event
  summary       — 1-2 sentences synthesised from evidence
  attributes    — dict of extracted {metric_key: value_with_unit}
  evidence      — [{para_idx, sentence_idx, quote}] pointing back to raw
  cross_links   — other concept names co-occurring in the same paragraphs
  confidence    — 0-1 rough self-score (frequency × diversity × specificity)

The lint step uses the evidence+attributes to detect REAL contradictions
(same entity+metric with conflicting numeric values) and negation conflicts
(claim + its explicit negation in the same corpus).

Supports mixed-Chinese-English input. No external NLP deps (keeps Vercel /
Fly.io cold start fast); if `yake` happens to be installed it is used as
a fallback signal but is no longer required.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

# Optional yake signal (kept for back-compat; never required)
try:  # pragma: no cover
    import yake  # type: ignore
    _HAS_YAKE = True
except Exception:  # noqa: BLE001
    _HAS_YAKE = False

# ══════════════════════════════════════════════════════════════════════════
# 1. Text utilities — paragraphs, sentences, language detection
# ══════════════════════════════════════════════════════════════════════════

_CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
_PARA_SPLIT = re.compile(r"\n\s*\n+")
# Sentence terminators: Chinese 。！？；  English . ! ? ;
_SENT_SPLIT = re.compile(r"(?<=[。！？；!?;])\s*|(?<=[.])\s+(?=[A-Z\u4e00-\u9fff])")


def _is_chinese(text: str) -> bool:
    if not text:
        return False
    chinese = len(_CHINESE_RE.findall(text))
    return chinese > len(text) * 0.15


def _split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in _PARA_SPLIT.split(text or "") if p and p.strip()]


def _split_sentences(paragraph: str) -> List[str]:
    parts = _SENT_SPLIT.split(paragraph)
    out: List[str] = []
    for s in parts:
        s = (s or "").strip()
        if len(s) >= 4:  # drop ultra-short fragments
            out.append(s)
    return out


def _sentence_index(text: str) -> List[Tuple[int, int, str]]:
    """Returns list of (para_idx, sentence_idx_within_para, sentence_text)."""
    idx: List[Tuple[int, int, str]] = []
    for p_i, para in enumerate(_split_paragraphs(text)):
        for s_i, sent in enumerate(_split_sentences(para)):
            idx.append((p_i, s_i, sent))
    return idx


# ══════════════════════════════════════════════════════════════════════════
# 2. Entity extraction — ASCII brand names + Chinese proper nouns
# ══════════════════════════════════════════════════════════════════════════

# English / ASCII brand / product names.
# Matches CamelCase, all-caps, version strings (Qwen2.5, GPT-4o, V3, Baichuan-M1)
_ASCII_ENTITY_RE = re.compile(
    r"\b("
    r"(?:[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+)"   # Baichuan-M1, GPT-4o
    r"|(?:[A-Z][A-Za-z]+\d+(?:\.\d+)?[A-Za-z]*)"  # Qwen2.5, GLM4, Claude3
    r"|(?:[A-Z]{2,}[0-9]*)"                       # AI, MoE, GPT
    r"|(?:[A-Z][a-z]+(?:[A-Z][a-z]+)+)"           # CamelCase: DeepSeek, MoonDream
    r"|(?:[A-Z][a-z]{2,})"                        # Titlecase: Sierra, Decagon, Anthropic
    r")\b"
)

# Chinese entity patterns
#   (1) N-grams ending in well-known org/product suffixes
#   (2) Short proper nouns appearing in known contexts: 公司/发布/推出/投资/融资 X
_CN_SUFFIX_ENTITY_RE = re.compile(
    r"[\u4e00-\u9fff]{1,5}"
    r"(?:公司|集团|科技|智能|AI|实验室|研究院|银行|投资|基金|资本|大模型|模型|家族|系列|平台|架构)"
)

_CN_QUOTED_RE = re.compile(r"[「《“\"']([^」》”\"']{2,20})[」》”\"']")

# Chinese brand names seen in this corpus (pragmatic dictionary — extended
# with user input at runtime via any extracted n-gram that also appears in
# suffix/quote contexts). For unknown corpora we fall back to suffix + quotes.
_CN_BRAND_HINT = {
    "深度求索", "月之暗面", "智谱", "通义千问", "豆包", "文心一言", "讯飞星火",
    "字节跳动", "阿里巴巴", "腾讯", "华为", "百度", "百川智能", "零一万物",
    "中关村", "红杉", "高瓴", "IDG", "经纬",
}

# Stopwords that sneak in from the regexes
_STOPLIST = {
    # English
    "the", "this", "that", "these", "those", "however", "but", "and",
    "for", "with", "from", "about", "their", "there", "which", "while",
    "have", "been", "will", "more", "most", "some", "when", "they", "them",
    "what", "into", "onto", "over", "than", "then", "also", "such", "many",
    "very", "only", "other", "your", "must", "should", "could", "would",
    "In", "On", "At", "Of", "By", "To", "Is", "Are", "Was", "Were",
    "A", "An", "As", "But", "It", "For",
    # Chinese stop-n-grams that could otherwise pass as entities
    "这个", "那个", "一些", "可能", "然而", "因此", "并且", "通过", "基于",
    "作为", "以及", "其中", "此外", "模型", "架构", "系列", "平台",
}


_CN_LEADING_STRIP_RE = re.compile(r"^(的|由|在|和|与|及|给|把|对|被|让|从|向|是|等)+")
_CN_GENERIC_SUFFIXES_ONLY = {"模型", "大模型", "平台", "系列", "家族", "架构"}


def _clean_entity(name: str) -> Optional[str]:
    """Normalise an entity name: strip punctuation, Chinese leading
    prepositions, and drop generic / noisy forms. Returns None if invalid."""
    n = (name or "").strip(" \t,.，。、；;:：()（）\"'「」《》")
    if not n:
        return None
    # Strip Chinese prepositional prefixes that sneak in via suffix regex
    n2 = _CN_LEADING_STRIP_RE.sub("", n)
    if not n2 or len(n2) < 2:
        return None
    # Drop names with embedded "的" which are almost always phrases, not entities
    if "的" in n2:
        return None
    # Drop entities that are just a generic suffix
    if n2 in _CN_GENERIC_SUFFIXES_ONLY:
        return None
    # Drop single lowercase English words
    if re.match(r"^[a-z]+$", n2):
        return None
    if n2 in _STOPLIST:
        return None
    return n2


# Match adjacent Titlecase ASCII tokens to group multi-word names
# (e.g. "Hugging Face", "Mixture of Experts" — except stopwords in between).
_ASCII_MULTIWORD_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9\.\-]{1,})(?:\s+[A-Z][A-Za-z0-9\.\-]{1,}){1,3}\b"
)


def _extract_entities(text: str) -> List[str]:
    """Return ordered list of unique entity surface forms appearing in text."""
    seen: Dict[str, int] = {}

    def add(name: str, weight: int = 1) -> None:
        cleaned = _clean_entity(name)
        if not cleaned:
            return
        seen[cleaned] = seen.get(cleaned, 0) + weight

    if not text:
        return []

    # 1. Multi-word ASCII Titlecase sequences — high weight, e.g. "Hugging Face"
    multi_spans: List[Tuple[int, int]] = []
    for m in _ASCII_MULTIWORD_RE.finditer(text):
        # Drop if every word is short and common
        words = m.group(0).split()
        if all(w.lower() in _STOPLIST for w in words):
            continue
        add(m.group(0), weight=3)
        multi_spans.append(m.span())

    def _in_multi(start: int, end: int) -> bool:
        return any(ms <= start and me >= end for (ms, me) in multi_spans)

    # 2. Single-word ASCII entities (skipping those already inside a multi-word)
    for m in _ASCII_ENTITY_RE.finditer(text):
        if _in_multi(*m.span()):
            continue
        add(m.group(1))

    # 3. Chinese entities with known org/product suffixes
    for m in _CN_SUFFIX_ENTITY_RE.finditer(text):
        add(m.group(0), weight=2)

    # 4. Chinese quoted terms
    for m in _CN_QUOTED_RE.finditer(text):
        add(m.group(1), weight=2)

    # 5. Chinese brand hints (dictionary lookup)
    for brand in _CN_BRAND_HINT:
        if brand in text:
            add(brand, weight=3)

    # Sort: most weight first, then alphabetical
    return [n for n, _ in sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))]


# ══════════════════════════════════════════════════════════════════════════
# 3. Numeric fact extraction — (metric_key, value_with_unit) near entities
# ══════════════════════════════════════════════════════════════════════════

# Chinese metric vocabulary with canonical keys
_CN_METRIC = {
    "估值": "valuation", "融资": "funding", "融资额": "funding",
    "收入": "revenue", "营收": "revenue",
    "参数": "params", "参数规模": "params", "参数量": "params",
    "成本": "cost", "训练成本": "train_cost",
    "价格": "price", "token 价格": "token_price", "推理成本": "inference_cost",
    "得分": "score", "分数": "score",
    "下载": "downloads", "下载量": "downloads",
    "日活": "dau", "月活": "mau",
    "员工": "employees",
    "用户": "users",
    "排名": "rank",
}
_EN_METRIC = {
    "valuation": "valuation", "raised": "funding", "funding": "funding",
    "revenue": "revenue",
    "parameters": "params", "params": "params",
    "cost": "cost", "training cost": "train_cost",
    "price": "price",
    "score": "score",
    "downloads": "downloads",
    "dau": "dau", "mau": "mau",
    "users": "users", "employees": "employees",
}

# Numeric value with unit (Chinese + English mixed)
_NUM_UNIT_RE = re.compile(
    r"""
    (?:USD\s*|US?\$|￥|\$)?
    (?P<num>\d+(?:[\.,]\d+)*)\s*
    (?P<unit>
        % |
        (?:亿|万|千|百) |
        (?:美元|人民币|元|RMB|USD|HKD) |
        (?:分(?!析)) |
        (?:B\b|M\b|K\b|T\b) |
        (?:tokens?|次|家|人|天|月|年|小时|Hz|px) |
        (?:point(?:s)?)
    )?
    """,
    re.VERBOSE,
)


def _normalize_value(num: str, unit: str) -> Tuple[float, str]:
    """Return (scalar_in_SI_ish, display_string)."""
    try:
        n = float(num.replace(",", ""))
    except ValueError:
        n = 0.0
    display = (num + (unit or "")).strip()
    mult = 1.0
    if unit in ("亿",):
        mult = 1e8
    elif unit in ("万",):
        mult = 1e4
    elif unit in ("千",):
        mult = 1e3
    elif unit in ("百",):
        mult = 1e2
    elif unit == "B":
        mult = 1e9
    elif unit == "M":
        mult = 1e6
    elif unit == "K":
        mult = 1e3
    elif unit == "T":
        mult = 1e12
    # percentages and domain units keep scalar
    return n * mult, display


def _find_metric_near(sentence: str, entity: str) -> List[Dict[str, Any]]:
    """Given a sentence containing entity, extract (metric_key, value, raw) facts.

    Strategy: for each metric keyword present, find the nearest number-with-unit
    to its right within a short window.
    """
    out: List[Dict[str, Any]] = []
    if entity not in sentence:
        return out

    # Try Chinese metrics first
    for kw, key in _CN_METRIC.items():
        idx = sentence.find(kw)
        if idx < 0:
            continue
        # Search in a 40-char window after the keyword
        window = sentence[idx : idx + 40]
        m = _NUM_UNIT_RE.search(window)
        if m and m.group("num"):
            num, display = _normalize_value(m.group("num"), m.group("unit") or "")
            out.append({"metric": key, "keyword": kw, "value": num, "display": display})

    # English metrics
    low = sentence.lower()
    for kw, key in _EN_METRIC.items():
        idx = low.find(kw)
        if idx < 0:
            continue
        window = sentence[idx : idx + 40]
        m = _NUM_UNIT_RE.search(window)
        if m and m.group("num"):
            num, display = _normalize_value(m.group("num"), m.group("unit") or "")
            out.append({"metric": key, "keyword": kw, "value": num, "display": display})

    # De-dup by (metric, display)
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for f in out:
        k = (f["metric"], f["display"])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    return uniq


# ══════════════════════════════════════════════════════════════════════════
# 4. Concept synthesis — entity ⊕ evidence ⊕ attributes ⊕ cross-links
# ══════════════════════════════════════════════════════════════════════════

_OPINION_MARKERS_CN = ("反方", "争议", "批评", "担心", "质疑", "高估", "被高估", "泡沫", "泡沫严重", "不看好", "观点：", "认为")
_OPINION_MARKERS_EN = ("contrarian", "critics argue", "however", "but some", "doubt", "overrated", "bubble", "bearish")


def _classify_type(entity: str, evidence_quotes: List[str]) -> str:
    blob = " ".join(evidence_quotes)
    low = blob.lower()
    if any(m in blob for m in _OPINION_MARKERS_CN) or any(m in low for m in _OPINION_MARKERS_EN):
        return "opinion"
    if re.search(r"\d+(\.\d+)?\s*(%|亿|万|M\b|B\b|美元|人民币|分|点)", blob):
        return "metric"
    if entity.endswith(("公司", "集团", "实验室", "基金", "资本", "投资", "研究院")):
        return "entity"
    if entity in _CN_BRAND_HINT or re.match(r"^[A-Z][A-Za-z0-9\-\.]+$", entity):
        return "entity"
    return "claim"


def _synthesize_summary(entity: str, evidence_quotes: List[str], attributes: Dict[str, str]) -> str:
    """Compose a short (<= 280 char) summary from the first 2 pieces of evidence
    and the extracted attributes. Stays purely extractive — no LLM calls."""
    head = " ".join(evidence_quotes[:2]).strip()
    if attributes:
        attr_line = "；".join(f"{k}={v}" for k, v in list(attributes.items())[:4])
        head = f"{head}  ⟨{attr_line}⟩"
    return head[:280]


def extract_concepts(
    text: str,
    n: int = 8,
    lang: str = "auto",
) -> List[Dict[str, Any]]:
    """Extract up to `n` concepts from raw text.

    Each concept = entity + source-attributed evidence + attributes +
    cross-links (other top entities sharing a paragraph) + rough confidence.
    """
    if not text or not text.strip():
        return []
    n = max(1, int(n))

    sent_idx = _sentence_index(text)
    if not sent_idx:
        return []

    entities = _extract_entities(text)
    if not entities:
        return []

    # Compute per-entity stats: paragraphs hit, sentences hit
    para_hits: Dict[str, set] = defaultdict(set)
    sent_hits: Dict[str, List[Tuple[int, int, str]]] = defaultdict(list)
    for (p, s, sentence) in sent_idx:
        for ent in entities:
            if ent in sentence:
                para_hits[ent].add(p)
                sent_hits[ent].append((p, s, sentence))

    # Build a para_idx → list of (sent_idx, sentence) map for paragraph-level
    # attribute scans. Chinese text frequently drops the subject in continuation
    # sentences ("第三方复现估算…1200 万美元" 主语隐含为 DeepSeek), so metrics
    # must be gathered from the whole paragraph, not just entity sentences.
    paras: Dict[int, List[Tuple[int, str]]] = defaultdict(list)
    for (p, s, sentence) in sent_idx:
        paras[p].append((s, sentence))

    # Rank: diversity (# unique paragraphs) × frequency
    total_paras = len({p for (p, _, _) in sent_idx}) or 1
    scored = []
    for ent in entities:
        freq = len(sent_hits[ent])
        diversity = len(para_hits[ent]) / total_paras
        # specificity: reward longer + mixed-script names a bit
        specificity = min(1.0, len(ent) / 10.0)
        score = freq * (0.5 + diversity) * (0.7 + 0.5 * specificity)
        if freq >= 1:
            scored.append((ent, score, freq, diversity))
    scored.sort(key=lambda t: (-t[1], -t[2], t[0]))

    top = scored[:n]

    # Build full concept records
    concepts: List[Dict[str, Any]] = []
    for (ent, score, freq, diversity) in top:
        # Top-3 evidence shown to humans (source attribution)
        evidence = [
            {"para_idx": p, "sentence_idx": s, "quote": q}
            for (p, s, q) in sent_hits[ent][:3]
        ]
        # Attributes aggregated across every paragraph that mentions the entity,
        # including sentences inside that paragraph where the subject is dropped
        # (common in Chinese). This is what lets `lint_kb` spot contradictions
        # like "557 万美元" vs "1200 万美元" when only one sentence says "DeepSeek".
        # Key by canonical metric so "得分" and "分数" collapse into one key
        # (`score`). This is what lets Baichuan-M1 93分 vs 87分 surface as a
        # contradiction instead of two separate attributes.
        attrs_raw: Dict[str, List[str]] = defaultdict(list)
        attr_keywords: Dict[str, List[str]] = defaultdict(list)
        for p_idx in para_hits[ent]:
            for (_s_idx, quote) in paras.get(p_idx, []):
                probe = quote if ent in quote else f"{ent} {quote}"
                for f in _find_metric_near(probe, ent):
                    attrs_raw[f["metric"]].append(f["display"])
                    if f["keyword"] not in attr_keywords[f["metric"]]:
                        attr_keywords[f["metric"]].append(f["keyword"])
        # Preserve order but de-dup per metric. Display shows metric(kw1/kw2).
        attributes: Dict[str, str] = {}
        for k, vals in attrs_raw.items():
            display_key = f"{k}({'/'.join(attr_keywords[k])})"
            attributes[display_key] = " / ".join(dict.fromkeys(vals))

        # Cross-links: other top entities sharing any paragraph
        others = {t[0] for t in top if t[0] != ent}
        shared_paras = para_hits[ent]
        cross_links: List[str] = []
        for other in others:
            if para_hits[other] & shared_paras:
                cross_links.append(other)

        concept_type = _classify_type(ent, [e["quote"] for e in evidence])
        summary = _synthesize_summary(ent, [e["quote"] for e in evidence], attributes)
        # Confidence normalised against the highest score
        max_score = top[0][1] or 1.0
        confidence = round(min(1.0, 0.4 + 0.6 * (score / max_score)), 3)

        concepts.append({
            "name": ent,
            "type": concept_type,
            "summary": summary,
            "attributes": attributes,
            "evidence": evidence,
            "cross_links": cross_links,
            "confidence": confidence,
        })
    return concepts


# ══════════════════════════════════════════════════════════════════════════
# 5. Lint — contradictions, orphans, unsourced, short, duplicates
# ══════════════════════════════════════════════════════════════════════════

# Extract raw numeric value from a string like "557 万美元"
_BARE_NUM_RE = re.compile(r"(\d+(?:[\.,]\d+)*)")


def _numeric_key(display: str) -> float:
    m = _BARE_NUM_RE.search(display or "")
    if not m:
        return float("nan")
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return float("nan")


def _negation_pair(a: str, b: str) -> bool:
    """True if `b` looks like a negation of `a` (or vice versa).

    Heuristic: one of them contains a negation marker AND they share ≥ 5
    consecutive CJK chars or ≥ 2 shared multi-char English tokens.
    """
    negs_cn = ("不", "没", "非", "无")
    negs_en = (" not ", " never ", " no ", "isn't", "aren't", "doesn't", "don't", "won't")
    has_neg_a = any(k in a for k in negs_cn) or any(k in a.lower() for k in negs_en)
    has_neg_b = any(k in b for k in negs_cn) or any(k in b.lower() for k in negs_en)
    if has_neg_a == has_neg_b:
        return False
    # overlap test
    cjk_a = re.findall(r"[\u4e00-\u9fff]{4,}", a)
    cjk_b = re.findall(r"[\u4e00-\u9fff]{4,}", b)
    if cjk_a and cjk_b and any(any(x in bb for bb in cjk_b) for x in cjk_a):
        return True
    toks_a = set(re.findall(r"[A-Za-z]{4,}", a.lower()))
    toks_b = set(re.findall(r"[A-Za-z]{4,}", b.lower()))
    return len(toks_a & toks_b) >= 2


def lint_kb(concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Inspect concept list for KB health issues."""
    if concepts is None:
        concepts = []

    orphaned = [c["name"] for c in concepts if not c.get("cross_links")]
    short = [c["name"] for c in concepts if len((c.get("summary") or "").strip()) < 30]
    # "unsourced" only applies when the caller opted into source tracking
    # (i.e. the `evidence` key is present but empty). Absence means the caller
    # doesn't use the new source-attribution workflow — no penalty.
    unsourced = [
        c["name"] for c in concepts
        if "evidence" in c and not c["evidence"]
    ]

    # Duplicate names: case-insensitive prefix / substring
    duplicates: List[List[str]] = []
    seen_pairs: set = set()
    names = [c.get("name", "") for c in concepts]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i].lower(), names[j].lower()
            if not a or not b:
                continue
            # Avoid flagging totally different entities that happen to share a substring
            # require one be a strict substring OR exact case-insensitive match
            if a == b or (len(a) >= 4 and len(b) >= 4 and (a == b or a in b or b in a)):
                key = tuple(sorted([names[i], names[j]]))
                if key not in seen_pairs:
                    seen_pairs.add(key)
                    duplicates.append(list(key))

    # Numeric contradictions: same concept + metric with different scalar values
    numeric_conflicts: List[Dict[str, Any]] = []
    for c in concepts:
        attrs = c.get("attributes") or {}
        for metric, display_value in attrs.items():
            # display_value may already concatenate variants with " / "
            parts = [p.strip() for p in str(display_value).split("/") if p.strip()]
            if len(parts) < 2:
                continue
            nums = {_numeric_key(p) for p in parts}
            nums = {n for n in nums if n == n}  # drop NaN
            if len(nums) >= 2:
                numeric_conflicts.append({
                    "concept": c["name"],
                    "metric": metric,
                    "values": parts,
                })

    # Negation conflicts: evidence quotes attached to same concept where one
    # asserts X and another negates X
    negation_conflicts: List[Dict[str, Any]] = []
    for c in concepts:
        evs = c.get("evidence") or []
        quotes = [e.get("quote", "") for e in evs]
        for i in range(len(quotes)):
            for j in range(i + 1, len(quotes)):
                if _negation_pair(quotes[i], quotes[j]):
                    negation_conflicts.append({
                        "concept": c["name"],
                        "claims": [quotes[i], quotes[j]],
                    })

    total_issues = (
        len(orphaned) + len(short) + len(duplicates)
        + len(unsourced) + len(numeric_conflicts) + len(negation_conflicts)
    )

    # Aggregate health score (0-100)
    n = max(1, len(concepts))
    health = round(
        max(
            0,
            100
            - 8 * len(orphaned)
            - 5 * len(short)
            - 8 * len(duplicates)
            - 10 * len(unsourced)
            - 20 * len(numeric_conflicts)
            - 15 * len(negation_conflicts),
        )
    )
    avg_attrs = round(sum(len(c.get("attributes") or {}) for c in concepts) / n, 2)
    avg_evidence = round(sum(len(c.get("evidence") or []) for c in concepts) / n, 2)

    return {
        "orphaned": orphaned,
        "short_summaries": short,
        "duplicates": duplicates,
        "unsourced": unsourced,
        "numeric_contradictions": numeric_conflicts,
        "negation_contradictions": negation_conflicts,
        "total_issues": total_issues,
        "health_score": health,
        "avg_attributes_per_concept": avg_attrs,
        "avg_evidence_per_concept": avg_evidence,
    }

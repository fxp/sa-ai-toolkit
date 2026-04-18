"""Karpathy KB — concept extraction + KB lint.

Uses `yake` for keyword extraction when available; falls back to a simple
frequency heuristic so tests can run without the dep installed.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any

try:
    import yake  # type: ignore
    _HAS_YAKE = True
except Exception:  # noqa: BLE001
    _HAS_YAKE = False


_SENT_RE = re.compile(r"(?<=[.!?。！？])\s+")
_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z\-]{3,}\b")

_STOP = {
    "the", "this", "that", "these", "those", "however", "nevertheless", "but",
    "and", "for", "with", "from", "about", "their", "there", "which", "while",
    "have", "been", "will", "more", "most", "some", "when", "they", "them",
    "what", "into", "onto", "over", "than", "then", "also", "such", "many",
    "very", "only", "other", "your", "must", "should", "could", "would",
}


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in _SENT_RE.split(text or "") if s and s.strip()]


def _fallback_keywords(text: str, n: int) -> List[str]:
    freq: Dict[str, int] = {}
    for w in _WORD_RE.findall(text or ""):
        lw = w.lower()
        if lw in _STOP:
            continue
        freq[lw] = freq.get(lw, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:n]]


def _yake_keywords(text: str, n: int) -> List[str]:
    # Single-word keywords, top n
    kw = yake.KeywordExtractor(lan="en", n=1, top=max(n * 2, n + 3))
    raw = kw.extract_keywords(text)
    # raw = [(word, score)]; lower score is better
    words: List[str] = []
    for word, _score in raw:
        w = word.strip().lower()
        if not w or w in _STOP or len(w) < 4 or not re.match(r"^[a-z][a-z\-]+$", w):
            continue
        if w in words:
            continue
        words.append(w)
        if len(words) >= n:
            break
    return words


def extract_concepts(text: str, n: int = 5) -> List[Dict[str, Any]]:
    """Extract top-N single-word concepts and cross-link them via co-occurring sentences.

    Returns:
        [{"name": str, "summary": str, "cross_links": [str, ...]}]
    """
    if not text or not text.strip():
        return []
    n = max(1, int(n))
    sentences = _split_sentences(text)
    if _HAS_YAKE:
        try:
            keywords = _yake_keywords(text, n)
        except Exception:  # noqa: BLE001
            keywords = _fallback_keywords(text, n)
    else:
        keywords = _fallback_keywords(text, n)

    if len(keywords) < n:
        # Pad with fallback to keep count stable
        extras = [k for k in _fallback_keywords(text, n * 2) if k not in keywords]
        keywords = (keywords + extras)[:n]

    concepts: List[Dict[str, Any]] = []
    kw_set = set(keywords)
    for kw in keywords:
        hits = [s for s in sentences if kw.lower() in s.lower()][:2]
        summary = " ".join(hits).strip()
        if not summary:
            summary = f"Concept '{kw}' referenced in source material."
        # cross-links: other keywords that also appear in any summary sentence
        cross: List[str] = []
        for other in keywords:
            if other == kw:
                continue
            for s in hits:
                if other.lower() in s.lower() and other not in cross:
                    cross.append(other)
                    break
        concepts.append({
            "name": kw.title() if kw.isalpha() else kw,
            "summary": summary[:280],
            "cross_links": cross,
        })
    return concepts


def lint_kb(concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Inspect a concept list for common KB health issues."""
    if concepts is None:
        concepts = []
    orphaned = [c["name"] for c in concepts if not c.get("cross_links")]
    short = [c["name"] for c in concepts if len((c.get("summary") or "").strip()) < 30]
    # Simple duplicate check: name-substring or case-insensitive identical-prefix match
    duplicates: List[List[str]] = []
    seen = set()
    names = [c.get("name", "") for c in concepts]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i].lower(), names[j].lower()
            if not a or not b:
                continue
            if a == b or a in b or b in a:
                key = tuple(sorted([names[i], names[j]]))
                if key not in seen:
                    seen.add(key)
                    duplicates.append(list(key))
    return {
        "orphaned": orphaned,
        "short_summaries": short,
        "duplicates": duplicates,
        "total_issues": len(orphaned) + len(short) + len(duplicates),
    }

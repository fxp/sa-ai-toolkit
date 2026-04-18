"""Hypothesis annotator — classifies each sentence into one of four tags.

Tags:
    data        — numeric / quantitative claim (red)
    contrarian  — but/however/contrary/nevertheless etc. (yellow)
    strategy    — should/must/strategy/focus (green)
    critique    — fallback (one sentence) (blue)
"""
from __future__ import annotations

import re
from typing import List, Dict


COLORS = {
    "data": "red",
    "contrarian": "yellow",
    "strategy": "green",
    "critique": "blue",
}

LABELS = {
    "data": "Key Data",
    "contrarian": "Contrarian",
    "strategy": "Strategy",
    "critique": "AI Critique",
}

NOTES = {
    "data": "Numeric claim — verify source and recency.",
    "contrarian": "Non-consensus framing — worth examining assumptions.",
    "strategy": "Prescriptive claim — test against your own context.",
    "critique": "Broad claim — ask what evidence would disprove it.",
}


# Pre-compiled regexes
_DATA_RE = re.compile(
    r"(\b\d+([.,]\d+)?\s*(%|x|m|b|t|k|million|billion|trillion))"
    r"|(\$\s*\d)"
    r"|(\b\d{4}\b)"  # year
    r"|([0-9]+%)",
    re.IGNORECASE,
)
_CONTRA_EN = re.compile(
    r"\b(but|however|contrary|contrarian|despite|nevertheless|yet|although)\b",
    re.IGNORECASE,
)
_CONTRA_ZH = re.compile(r"(虽然|但是|然而|尽管|不过|反而)")
_STRAT_EN = re.compile(
    r"\b(should|must|strategy|focus|pursue|shift|invest|adopt|winning|rollout)\b",
    re.IGNORECASE,
)
_STRAT_ZH = re.compile(r"(应该|必须|策略|应当|需要|应聚焦)")

_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+|(?<=[。！？])")


def _split_sentences(text: str) -> List[str]:
    # Split on English punct + trailing whitespace and Chinese terminators.
    parts = re.split(r"(?<=[.!?。！？])\s*", text or "")
    return [p.strip() for p in parts if p and p.strip() and len(p.strip()) > 3]


def _classify_one(sentence: str) -> str:
    if _DATA_RE.search(sentence):
        return "data"
    if _CONTRA_EN.search(sentence) or _CONTRA_ZH.search(sentence):
        return "contrarian"
    if _STRAT_EN.search(sentence) or _STRAT_ZH.search(sentence):
        return "strategy"
    return ""  # undecided (will fallback)


def classify_sentences(text: str) -> List[Dict[str, str]]:
    """Split text into sentences and tag each with one of 4 labels.

    Returns a list of dicts: {sentence, tag, color, label, note}.
    Exactly one undecided sentence gets tagged as "critique" (first eligible).
    """
    sentences = _split_sentences(text)
    results: List[Dict[str, str]] = []
    critique_assigned = False
    # First pass: tag with explicit categories
    tags: List[str] = []
    for s in sentences:
        tags.append(_classify_one(s))

    # Assign critique to the first undecided sentence (>= 25 chars)
    for i, (s, t) in enumerate(zip(sentences, tags)):
        if not t and not critique_assigned and len(s) >= 25:
            tags[i] = "critique"
            critique_assigned = True

    # Fill remaining undecided with critique too (but mark only one as primary)
    for s, t in zip(sentences, tags):
        if not t:
            # Skip uncategorized so we don't over-annotate
            continue
        results.append({
            "sentence": s,
            "tag": t,
            "color": COLORS[t],
            "label": LABELS[t],
            "note": NOTES[t],
        })
    return results

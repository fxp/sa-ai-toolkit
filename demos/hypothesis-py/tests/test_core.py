import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import classify_sentences  # noqa: E402


def _tags(items):
    return [x["tag"] for x in items]


def test_number_becomes_data():
    items = classify_sentences("The market is growing by 47% year over year.")
    assert items and items[0]["tag"] == "data"
    assert items[0]["color"] == "red"


def test_however_becomes_contrarian():
    items = classify_sentences(
        "AI adoption is widespread. However, most deployments fail to reach production."
    )
    # first sentence no trigger, second has 'However' → contrarian
    tags = _tags(items)
    assert "contrarian" in tags


def test_strategy_keyword():
    items = classify_sentences("Companies must focus on verticalized workflows.")
    assert items and items[0]["tag"] == "strategy"


def test_critique_fallback():
    # No number, no contrarian, no strategy — one sentence should be tagged critique
    items = classify_sentences(
        "Foundation models keep getting better at a steady pace."
    )
    assert items and items[0]["tag"] == "critique"


def test_all_items_have_required_fields():
    items = classify_sentences(
        "Revenue hit $12B in 2025. However, profits fell. Teams must invest in ops."
    )
    assert len(items) >= 3
    for it in items:
        for k in ("sentence", "tag", "color", "label", "note"):
            assert k in it and it[k]


def test_chinese_contrarian():
    items = classify_sentences("AI 市场很大。但是落地困难。")
    tags = _tags(items)
    assert "contrarian" in tags

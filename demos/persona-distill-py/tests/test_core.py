"""Persona Distill — unit tests (offline; no network)."""
from __future__ import annotations
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from core import (
    extract_patterns, distill_skill, package_zip, parse_skill,
    generate_with_skill, _slugify,
)


def _fake_search():
    return {
        "general": [
            {"title": "Jensen Huang on AI", "url": "https://example.com/a",
             "snippet": "Jensen said: \"You should always start with the hardest problem.\" "
                        "He explained the framework in a 2024 interview."},
            {"title": "NVIDIA strategy", "url": "https://example.com/b",
             "snippet": "We chose to prioritize GPU compute. The decision saved 5 years of R&D."},
        ],
        "interview": [
            {"title": "Stratechery interview", "url": "https://example.com/c",
             "snippet": "Principle: never bet against silicon. We must keep shipping."},
        ],
        "academic": [],
        "news": [{"title": "FT: NVIDIA hits $3T", "url": "https://example.com/d",
                  "snippet": "Market cap reached 3 trillion in 2024."}],
        "media": [],
        "writing": [],
    }


def test_extract_patterns_finds_buckets():
    pat = extract_patterns(_fake_search())
    assert pat["n_sources"] >= 4
    # at least one of these should fire from the cue words above
    assert any(pat[k] for k in ("decisions", "principles", "frameworks", "quotes"))
    # quote extraction
    assert any("hardest problem" in q for q in pat["quotes"])
    # metric extraction (3 trillion / 5 years)
    assert pat["metrics"]


def test_distill_renders_full_skill():
    pat = extract_patterns(_fake_search())
    out = distill_skill("NVIDIA", "Jensen Huang", pat, search_results=_fake_search())
    md = out["skill_md"]
    assert md.startswith("---\nname:")
    assert "Jensen Huang" in md
    assert "NVIDIA" in md or "nvidia" in out["slug"]
    assert "## 心智模型" in md or "## 决策启发式" in md
    assert "references_md" in out and "## general" in out["references_md"]


def test_zip_bundle_is_valid():
    pat = extract_patterns(_fake_search())
    out = distill_skill("NVIDIA", "Jensen Huang", pat, search_results=_fake_search())
    z = package_zip(out)
    # ZIP magic bytes
    assert z[:2] == b"PK"
    assert len(z) > 500


def test_parse_roundtrips_frontmatter():
    pat = extract_patterns(_fake_search())
    out = distill_skill("NVIDIA", "Jensen Huang", pat, search_results=_fake_search())
    parsed = parse_skill(out["skill_md"])
    assert parsed["name"]
    assert "description" in parsed
    # headings parsed
    assert any("心智" in s or "决策" in s or "原则" in s or "voice" in s.lower()
               for s in parsed["sections"])


def test_generate_with_skill_uses_persona():
    pat = extract_patterns(_fake_search())
    out = distill_skill("NVIDIA", "Jensen Huang", pat, search_results=_fake_search())
    result = generate_with_skill(out["skill_md"], "should I invest in CUDA training?")
    assert result["persona"]
    assert "判断" in result["output"] and "下一步" in result["output"]
    assert "should I invest" in result["output"] or "CUDA" in result["output"]


def test_slugify():
    assert _slugify("Jensen Huang") == "jensen-huang"
    assert _slugify("张雪峰") == "张雪峰"

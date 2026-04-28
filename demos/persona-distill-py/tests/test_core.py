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


# ─── Repo integration ───────────────────────────────────────────────

from core import format_for_repo, quality_check, _readme_with_new_row


def test_format_for_repo_matches_repo_conventions():
    pat = extract_patterns(_fake_search())
    out = format_for_repo("NVIDIA", "Jensen Huang", pat, search_results=_fake_search())
    md = out["skill_md"]
    # YAML frontmatter with the repo's required keys
    assert md.startswith("---\nname:")
    assert "type: perspective" in md
    assert "调研时间:" in md
    # body sections that match repo conventions
    assert "## 使用说明" in md
    assert "## 角色扮演规则" in md
    assert "## 心智模型" in md
    assert "## 决策启发式" in md
    assert "## 表达 DNA" in md
    # path-style refs link
    assert "references/sources.md" in md


def test_quality_check_flags_thin_distill():
    qc = quality_check({}, {"n_sources": 1, "quotes": [], "decisions": [],
                            "frameworks": [], "principles": []})
    assert not qc["passed"]
    assert qc["score"] < 30
    assert any("source" in i for i in qc["issues"])


def test_quality_check_passes_richer_distill():
    pat = extract_patterns(_fake_search())
    pat["n_sources"] = 8
    pat["quotes"] = ["q1", "q2", "q3", "q4", "q5"]
    pat["frameworks"] = ["f1", "f2", "f3"]
    pat["decisions"] = ["d1", "d2"]
    pat["principles"] = ["p1"]
    qc = quality_check({}, pat)
    assert qc["score"] >= 60


def test_readme_table_insertion_idempotent():
    readme = (
        "# Persona Distill Skills\n\n"
        "## Persona 目录\n\n"
        "### 公众人物与方法论视角\n\n"
        "| Persona | 领域 | 触发词 | 简介 |\n"
        "|---------|------|--------|------|\n"
        "| [**香帅**](personas/xiangshuai/) | 金融 | `香帅` | 中国经济观察者 |\n"
    )
    new = _readme_with_new_row(readme, "jensen-huang", "Jensen Huang",
                               "NVIDIA", "Jensen Huang", "GPU 战略 + 加速计算")
    assert "[**Jensen Huang**](personas/jensen-huang/)" in new
    # idempotent
    new2 = _readme_with_new_row(new, "jensen-huang", "Jensen Huang",
                                "NVIDIA", "Jensen Huang", "GPU 战略 + 加速计算")
    assert new2 == new
    # original row preserved
    assert "[**香帅**](personas/xiangshuai/)" in new2


def test_readme_table_appends_new_section_when_table_missing():
    readme = "# Just a README\n\nNo table here yet.\n"
    new = _readme_with_new_row(readme, "test-slug", "Test",
                               "TestCo", None, "smoke test")
    assert "Auto-distilled" in new
    assert "[**Test**](personas/test-slug/)" in new

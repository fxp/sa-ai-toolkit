import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import (  # noqa: E402
    export_email,
    generate_package,
    rehearse,
    replace_terms,
    search_company,
    switch_audience,
)


def test_gen_returns_four_keys():
    info = search_company("Tencent")
    pkg = generate_package(info)
    for k in ("profile", "scoring", "schedule", "opening_remarks"):
        assert k in pkg and isinstance(pkg[k], str) and len(pkg[k]) > 0


def test_replace_terms():
    info = search_company("Tencent")
    pkg = generate_package(info)
    out = replace_terms(pkg, {"Tencent": "Acme"})
    assert "Acme" in out["profile"]
    assert "Tencent" not in out["profile"]


def test_rehearse_non_empty():
    info = search_company("Alibaba")
    pkg = generate_package(info)
    plays = rehearse(pkg)
    assert len(plays) > 1
    assert all("title" in p and "seconds" in p for p in plays)


def test_switch_audience_regenerates_opening():
    info = search_company("Tencent")
    pkg = generate_package(info)
    out = switch_audience(pkg, "engineering")
    assert "engineering" in out["opening_remarks"].lower()
    assert out["audience"] == "engineering"


def test_email_contains_company():
    info = search_company("Tencent")
    pkg = generate_package(info)
    email = export_email(pkg)
    assert "Tencent" in email

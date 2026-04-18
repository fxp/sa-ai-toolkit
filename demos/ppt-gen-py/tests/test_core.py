import io
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import generate_pptx  # noqa: E402


def test_returns_pkzip_bytes():
    data = generate_pptx("Title", "Sub", [{"template": "cover", "fields": {"title": "T", "subtitle": "S"}}])
    assert isinstance(data, bytes) and data[:2] == b"PK"


def test_cover_template():
    data = generate_pptx("Deck", "Sub",
                         [{"template": "cover", "fields": {"title": "Deck", "subtitle": "Sub", "company": "X", "date": "2026"}}])
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        assert any(n.startswith("ppt/slides/slide") for n in names)


def test_five_slide_templates():
    slides = [
        {"template": "cover",   "fields": {"title": "A", "subtitle": "sub", "company": "C", "date": "Today"}},
        {"template": "agenda",  "fields": {"title": "Agenda", "content": "A\nB\nC"}},
        {"template": "data",    "fields": {"title": "Metric", "big_number": "78%", "description": "of firms", "source": "Research"}},
        {"template": "split",   "fields": {"title": "Split", "content": "one\ntwo\nthree"}},
        {"template": "summary", "fields": {"title": "Summary", "content": "X\nY\nZ"}},
    ]
    data = generate_pptx("Title", "Sub", slides, theme="purple-pink")
    assert data[:2] == b"PK"
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        slide_files = [n for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        # 5 custom + auto-cover injected? First slide is already cover, so exactly 5.
        assert len(slide_files) == 5

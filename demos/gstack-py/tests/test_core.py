import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

from core import run_command  # noqa: E402


VALID = ["office-hours", "autoplan", "qa", "ship"]


@pytest.mark.parametrize("cmd", VALID)
def test_command_returns_nonempty_script(cmd):
    script = run_command(cmd, "test idea")
    assert isinstance(script, list)
    assert len(script) > 0


@pytest.mark.parametrize("cmd", VALID)
def test_every_item_has_required_fields(cmd):
    script = run_command(cmd, "hello")
    for item in script:
        assert "delay_ms" in item and isinstance(item["delay_ms"], int)
        assert "text" in item and isinstance(item["text"], str)
        assert "class" in item and item["class"] in {
            "prompt", "output", "highlight", "warn", "err", "ok", "dim"
        }


def test_office_hours_includes_user_idea():
    script = run_command("office-hours", "AI note app for lawyers")
    text = " ".join(item["text"] for item in script)
    assert "AI note app for lawyers" in text


def test_unknown_command_raises():
    with pytest.raises(ValueError):
        run_command("bogus")


def test_qa_has_47_tests():
    script = run_command("qa")
    test_lines = [i for i in script if "test_" in i["text"]]
    # 47 running lines + 3 failure repeats
    assert len(test_lines) >= 47

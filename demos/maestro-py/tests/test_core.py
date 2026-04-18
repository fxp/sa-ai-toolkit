import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import parse_yaml, simulate_execution  # noqa: E402


LOGIN_YAML = """\
appId: com.newco.smartpet
name: "SmartPet Login Flow"
---
- launchApp
- assertVisible: "SmartPet"
- tapOn: "登录"
- tapOn: "手机号"
- inputText: "13800138000"
- tapOn: "获取验证码"
- assertVisible: "验证码已发送"
- tapOn: "验证码"
- inputText: "123456"
- tapOn: "确认登录"
- assertVisible: "欢迎回来"
"""


def test_parse_login_yaml():
    parsed = parse_yaml(LOGIN_YAML)
    assert parsed["appId"] == "com.newco.smartpet"
    assert parsed["name"] == "SmartPet Login Flow"
    assert len(parsed["steps"]) == 11
    assert parsed["steps"][0] == {"cmd": "launchApp", "arg": None}
    assert parsed["steps"][2]["cmd"] == "tapOn"
    assert parsed["steps"][2]["arg"] == "登录"


def test_simulate_returns_matching_trace():
    parsed = parse_yaml(LOGIN_YAML)
    trace = simulate_execution(parsed)
    assert len(trace) == len(parsed["steps"])
    for i, item in enumerate(trace):
        assert item["step"] == i
        assert item["cmd"]
        assert "result" in item and item["result"] in {"pass", "fail"}
        assert isinstance(item["duration_ms"], int)
        assert isinstance(item["screen"], str) and item["screen"]


def test_simulate_screen_transitions():
    parsed = parse_yaml(LOGIN_YAML)
    trace = simulate_execution(parsed)
    # After launchApp → home; after tapOn 登录 → loginForm; after 确认登录 → loggedIn
    screens = [t["screen"] for t in trace]
    assert "home" in screens
    assert "loginForm" in screens
    assert "loggedIn" in screens


def test_parse_empty_yaml():
    parsed = parse_yaml("")
    assert parsed["steps"] == []


def test_parse_yaml_without_frontmatter():
    text = "- launchApp\n- tapOn: \"登录\"\n"
    parsed = parse_yaml(text)
    assert len(parsed["steps"]) == 2
    assert parsed["steps"][1]["arg"] == "登录"

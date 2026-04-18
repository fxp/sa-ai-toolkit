"""Maestro YAML parser + execution simulator.

Uses PyYAML if available; falls back to a minimal parser that handles the
subset of Maestro flow syntax we care about (`appId`, `name`, and a `---`
separated list of single-key step mappings like `- tapOn: "X"` or bare
commands like `- launchApp`).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:  # noqa: BLE001
    _HAS_YAML = False


# Screen-transition map for the SmartPet demo. Unknown targets stay on current screen.
_NAV: Dict[str, str] = {
    "登录": "loginForm",
    "确认登录": "loggedIn",
    "进入主页": "home",
    "找医院": "hospitalList",
    "搜索按钮": "hospitalList",
    "爱心宠物医院": "hospitalDetail",
    "预约挂号": "loggedIn",
    "商城": "mall",
    "狗粮": "product",
    "立即购买": "checkout",
    "提交订单": "orderSuccess",
    "SmartPet": "home",
}


def _split_front_matter(yaml_text: str) -> tuple[str, str]:
    """Split an optional `---`-delimited header from a steps block."""
    parts = re.split(r"^---\s*$", yaml_text or "", flags=re.MULTILINE)
    if len(parts) >= 2:
        return parts[0], "\n".join(parts[1:])
    return "", parts[0] if parts else ""


def _parse_step_line(line: str) -> Optional[Dict[str, Any]]:
    stripped = line.strip()
    if not stripped.startswith("-"):
        return None
    body = stripped[1:].strip()
    if not body:
        return None
    # Either "cmd" (no arg) or "cmd: value"
    m = re.match(r'^([A-Za-z][A-Za-z0-9_]*)\s*(?::\s*(.+))?$', body)
    if not m:
        return None
    cmd = m.group(1)
    raw = (m.group(2) or "").strip()
    if raw.startswith('"') and raw.endswith('"'):
        arg: Any = raw[1:-1]
    elif raw.startswith("'") and raw.endswith("'"):
        arg = raw[1:-1]
    elif raw == "":
        arg = None
    else:
        arg = raw
    return {"cmd": cmd, "arg": arg}


def _fallback_parse(yaml_text: str) -> Dict[str, Any]:
    header, steps_block = _split_front_matter(yaml_text)
    out: Dict[str, Any] = {"appId": None, "name": None, "steps": []}
    for line in header.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^([A-Za-z][A-Za-z0-9_]*)\s*:\s*(.+?)\s*$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            if key in out:
                out[key] = val
    for line in steps_block.splitlines():
        step = _parse_step_line(line)
        if step is not None:
            out["steps"].append(step)
    return out


def parse_yaml(yaml_text: str) -> Dict[str, Any]:
    """Parse a Maestro flow YAML string into {appId, name, steps}.

    `steps` is a list of `{"cmd": str, "arg": str | None}`.
    Accepts either a PyYAML-parseable multi-doc `---`-split file or the same
    form via our fallback parser.
    """
    if yaml_text is None:
        raise ValueError("yaml_text is None")
    text = str(yaml_text)
    header, steps_block = _split_front_matter(text)

    result: Dict[str, Any] = {"appId": None, "name": None, "steps": []}

    if _HAS_YAML:
        try:
            # Header may itself be empty (when no ---). Use full text when no split.
            header_to_parse = header if header.strip() else text
            parsed_header = yaml.safe_load(header_to_parse)
            if isinstance(parsed_header, dict):
                result["appId"] = parsed_header.get("appId")
                result["name"] = parsed_header.get("name")
            # Steps
            if steps_block.strip():
                parsed_steps = yaml.safe_load(steps_block)
                if isinstance(parsed_steps, list):
                    for item in parsed_steps:
                        if isinstance(item, str):
                            result["steps"].append({"cmd": item, "arg": None})
                        elif isinstance(item, dict) and len(item) == 1:
                            (k, v), = item.items()
                            result["steps"].append({"cmd": str(k), "arg": v if v is None else str(v)})
                        elif isinstance(item, dict):
                            # multi-key step: take first key, pass whole dict as arg? keep first
                            k = next(iter(item))
                            v = item[k]
                            result["steps"].append({"cmd": str(k), "arg": v if v is None else str(v)})
            return result
        except Exception:  # noqa: BLE001
            # Fall back to naive parser
            pass

    return _fallback_parse(text)


def simulate_execution(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Simulate a Maestro flow and return a trace.

    Each trace item:
        {"step": int, "cmd": str, "arg": str | None, "result": "pass"|"fail",
         "duration_ms": int, "screen": str}
    """
    if not isinstance(parsed, dict):
        raise ValueError("parsed must be a dict")
    steps = parsed.get("steps") or []
    if not isinstance(steps, list):
        raise ValueError("parsed['steps'] must be a list")

    screen = "splash"
    trace: List[Dict[str, Any]] = []
    for i, step in enumerate(steps):
        cmd = step.get("cmd", "") if isinstance(step, dict) else ""
        arg = step.get("arg") if isinstance(step, dict) else None
        duration = 400
        result = "pass"

        if cmd == "launchApp":
            screen = "home"
            duration = 1000
        elif cmd == "tapOn":
            if arg and arg in _NAV:
                screen = _NAV[arg]
                duration = 700
            else:
                duration = 500
        elif cmd == "inputText":
            duration = 50 * max(1, len(str(arg or "")))
        elif cmd == "assertVisible":
            # Pass if the label exists in our known nav map OR if the string is
            # short enough to plausibly be on screen. We simulate optimistically.
            duration = 300
            if arg and arg not in _NAV and arg not in {
                "SmartPet", "欢迎回来", "验证码已发送", "下单成功", "预约挂号",
                "爱心宠物医院",
            }:
                # Still pass — this is a simulation, not a real assertion.
                result = "pass"

        trace.append({
            "step": i,
            "cmd": cmd,
            "arg": arg,
            "result": result,
            "duration_ms": int(duration),
            "screen": screen,
        })
    return trace

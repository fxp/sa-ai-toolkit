"""
Playwright demo core.

Two modes:
  - simulate_run(scenario) → deterministic trace (no browser needed).
  - run_real(scenario)     → drives real Chromium via playwright if available.

Playwright is imported lazily so the module works when it's not installed.
"""
from __future__ import annotations

import base64
import random
import time
from typing import Optional


# ---------------------------------------------------------------------------
# Preset scenarios — each command maps to one trace step.
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict] = {
    "bing": {
        "title": "Bing",
        "default_url": "https://www.bing.com",
        "script": [
            "# Bing search test",
            "from playwright.sync_api import sync_playwright",
            "",
            "with sync_playwright() as p:",
            "    browser = p.chromium.launch()",
            "    page = browser.new_page()",
            "    page.goto(\"https://www.bing.com\")",
            "    page.locator(\"#sb_form_q\").fill(\"Playwright\")",
            "    page.click(\"#sb_form_go\")",
            "    page.wait_for_load_state()",
            "    page.screenshot(path=\"results.png\")",
            "    browser.close()",
        ],
        "actions": [
            {"type": "goto",       "url": "https://www.bing.com",             "render": "bing_home"},
            {"type": "fill",       "selector": "#sb_form_q", "value": "Playwright"},
            {"type": "click",      "selector": "#sb_form_go", "render": "bing_results"},
            {"type": "wait"},
            {"type": "screenshot", "label": "results.png"},
        ],
    },
    "github": {
        "title": "GitHub · microsoft/playwright",
        "default_url": "https://github.com/microsoft/playwright",
        "script": [
            "# GitHub star test",
            "from playwright.sync_api import sync_playwright",
            "",
            "with sync_playwright() as p:",
            "    browser = p.chromium.launch()",
            "    page = browser.new_page()",
            "    page.goto(\"https://github.com/microsoft/playwright\")",
            "    page.click(\"button[aria-label=Star]\")",
            "    page.screenshot(path=\"starred.png\")",
            "    browser.close()",
        ],
        "actions": [
            {"type": "goto",       "url": "https://github.com/microsoft/playwright", "render": "gh_repo"},
            {"type": "click",      "selector": "button[aria-label=Star]",  "render": "gh_starred"},
            {"type": "screenshot", "label": "starred.png"},
        ],
    },
    "form": {
        "title": "Contact — Example",
        "default_url": "https://demo.example.com/contact",
        "script": [
            "# Form submit test",
            "from playwright.sync_api import sync_playwright",
            "",
            "with sync_playwright() as p:",
            "    browser = p.chromium.launch()",
            "    page = browser.new_page()",
            "    page.goto(\"https://demo.example.com/contact\")",
            "    page.locator(\"#name\").fill(\"Alice Zhang\")",
            "    page.locator(\"#email\").fill(\"alice@newco.com\")",
            "    page.locator(\"#msg\").fill(\"Hello Playwright!\")",
            "    page.click(\"#submit\")",
            "    page.screenshot(path=\"submitted.png\")",
            "    browser.close()",
        ],
        "actions": [
            {"type": "goto",       "url": "https://demo.example.com/contact", "render": "form_page"},
            {"type": "fill",       "selector": "#name",  "value": "Alice Zhang"},
            {"type": "fill",       "selector": "#email", "value": "alice@newco.com"},
            {"type": "fill",       "selector": "#msg",   "value": "Hello Playwright!"},
            {"type": "click",      "selector": "#submit", "render": "form_success"},
            {"type": "screenshot", "label": "submitted.png"},
        ],
    },
    "responsive": {
        "title": "NewCo — Homepage",
        "default_url": "https://www.newco.com",
        "script": [
            "# Responsive breakpoint check",
            "from playwright.sync_api import sync_playwright",
            "",
            "with sync_playwright() as p:",
            "    browser = p.chromium.launch()",
            "    page = browser.new_page()",
            "    page.goto(\"https://www.newco.com\")",
            "    page.screenshot(path=\"desktop.png\")",
            "    page.set_viewport_size({\"width\": 768, \"height\": 1024})",
            "    page.screenshot(path=\"tablet.png\")",
            "    page.set_viewport_size({\"width\": 375, \"height\": 667})",
            "    page.screenshot(path=\"mobile.png\")",
            "    browser.close()",
        ],
        "actions": [
            {"type": "goto",       "url": "https://www.newco.com", "render": "newco_home"},
            {"type": "screenshot", "label": "desktop.png"},
            {"type": "viewport",   "width": 768, "height": 1024},
            {"type": "screenshot", "label": "tablet.png"},
            {"type": "viewport",   "width": 375, "height": 667},
            {"type": "screenshot", "label": "mobile.png"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Action → code-line mapping
# ---------------------------------------------------------------------------

def _code_line_for(action: dict, script: list[str], used: set[int]) -> str:
    kw = {
        "goto": "goto",
        "fill": ".fill",
        "click": ".click",
        "screenshot": "screenshot",
        "viewport": "set_viewport_size",
        "wait": "wait_for_load_state",
    }.get(action["type"], "")
    for i, line in enumerate(script):
        if kw and kw in line and i not in used:
            used.add(i)
            return line.strip()
    return kw


def simulate_run(scenario: str) -> list[dict]:
    """Return a deterministic trace for the named preset — no browser."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario!r}. "
                         f"Available: {sorted(SCENARIOS.keys())}")
    sc = SCENARIOS[scenario]
    used: set[int] = set()
    trace: list[dict] = []
    for i, action in enumerate(sc["actions"]):
        code_line = _code_line_for(action, sc["script"], used)
        result, target_url = _describe(action, sc)
        trace.append({
            "step": i,
            "code_line": code_line,
            "action": action["type"],
            "target_url": target_url,
            "selector": action.get("selector"),
            "value": action.get("value"),
            "render": action.get("render"),
            "label": action.get("label"),
            "viewport": ({"width": action["width"], "height": action["height"]}
                          if action["type"] == "viewport" else None),
            "result": result,
            "duration_ms": 100 + random.randint(20, 400),
            "screenshot_b64": None,
        })
    return trace


def _describe(action: dict, scenario_def: dict) -> tuple[str, Optional[str]]:
    t = action["type"]
    if t == "goto":
        return f"navigated to {action['url']}", action["url"]
    if t == "fill":
        return f"typed '{action['value']}' into {action['selector']}", None
    if t == "click":
        return f"clicked {action['selector']}", None
    if t == "screenshot":
        return f"saved {action.get('label', 'screenshot.png')}", None
    if t == "viewport":
        return f"resized viewport to {action['width']}x{action['height']}", None
    if t == "wait":
        return "waited for load state", None
    return "ok", None


# ---------------------------------------------------------------------------
# Real run — optional, uses playwright if installed
# ---------------------------------------------------------------------------

def run_real(scenario: str, url: Optional[str] = None) -> list[dict]:
    """Drive real Chromium. Requires `pip install playwright && playwright install chromium`."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario!r}")

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as e:
        raise ImportError(
            "playwright not installed. Run: pip install playwright && playwright install chromium"
        ) from e

    sc = SCENARIOS[scenario]
    target_url = url or sc["default_url"]
    used: set[int] = set()
    trace: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            for i, action in enumerate(sc["actions"]):
                code_line = _code_line_for(action, sc["script"], used)
                t0 = time.time()
                screenshot_b64: Optional[str] = None
                t = action["type"]
                try:
                    if t == "goto":
                        page.goto(target_url if i == 0 else action["url"],
                                  wait_until="domcontentloaded", timeout=15000)
                        result = f"navigated to {target_url if i == 0 else action['url']}"
                    elif t == "fill":
                        page.locator(action["selector"]).first.fill(action["value"])
                        result = f"filled {action['selector']}"
                    elif t == "click":
                        page.locator(action["selector"]).first.click(timeout=5000)
                        result = f"clicked {action['selector']}"
                    elif t == "screenshot":
                        png = page.screenshot()
                        screenshot_b64 = base64.b64encode(png).decode("ascii")
                        result = f"captured {action.get('label', 'screenshot')}"
                    elif t == "viewport":
                        page.set_viewport_size({
                            "width": action["width"], "height": action["height"],
                        })
                        result = f"viewport → {action['width']}x{action['height']}"
                    elif t == "wait":
                        page.wait_for_load_state()
                        result = "load state ready"
                    else:
                        result = f"unhandled: {t}"
                except Exception as ex:
                    result = f"error: {ex}"

                trace.append({
                    "step": i,
                    "code_line": code_line,
                    "action": t,
                    "target_url": target_url if t == "goto" else None,
                    "selector": action.get("selector"),
                    "value": action.get("value"),
                    "label": action.get("label"),
                    "viewport": ({"width": action.get("width"), "height": action.get("height")}
                                  if t == "viewport" else None),
                    "result": result,
                    "duration_ms": int((time.time() - t0) * 1000),
                    "screenshot_b64": screenshot_b64,
                })
        finally:
            browser.close()

    return trace

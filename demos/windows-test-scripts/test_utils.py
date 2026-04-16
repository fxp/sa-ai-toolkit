"""
Shared utilities for all demo test scripts.
Provides GLM-5 API calls, result formatting, and test harness.
"""
import os, json, time, sys
from pathlib import Path

BIGMODEL_KEY = os.getenv("BIGMODEL_API_KEY", "")
BIGMODEL_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4-flash"  # Use flash for testing (cheaper); switch to glm-5 for production

# ── Colors for Windows terminal ──
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    DIM    = "\033[2m"

def header(demo_id: str, name: str):
    print(f"\n{'='*60}")
    print(f"{C.BOLD}{C.CYAN}  Demo {demo_id}: {name}{C.RESET}")
    print(f"{'='*60}\n")

def step(n: int, desc: str):
    print(f"{C.BLUE}  [{n}]{C.RESET} {desc}")

def ok(msg: str):
    print(f"  {C.GREEN}  ✓ {msg}{C.RESET}")

def warn(msg: str):
    print(f"  {C.YELLOW}  ! {msg}{C.RESET}")

def fail(msg: str):
    print(f"  {C.RED}  ✗ {msg}{C.RESET}")

def info(msg: str):
    print(f"  {C.DIM}    {msg}{C.RESET}")

def section(title: str):
    print(f"\n{C.BOLD}  --- {title} ---{C.RESET}")

def result_box(title: str, content: str, max_lines: int = 8):
    lines = content.strip().split('\n')[:max_lines]
    print(f"\n  {C.CYAN}┌─ {title} {'─'*(50-len(title))}┐{C.RESET}")
    for l in lines:
        print(f"  {C.CYAN}│{C.RESET} {l[:55]}")
    if len(content.strip().split('\n')) > max_lines:
        print(f"  {C.CYAN}│{C.RESET} {C.DIM}... ({len(content.strip().split(chr(10)))-max_lines} more lines){C.RESET}")
    print(f"  {C.CYAN}└{'─'*55}┘{C.RESET}\n")

def call_llm(prompt: str, system: str = "", max_tokens: int = 800) -> str:
    """Call BigModel GLM API. Falls back to mock if no key."""
    if not BIGMODEL_KEY:
        warn("未设置 BIGMODEL_API_KEY，使用模拟响应")
        return f"[模拟响应] 针对「{prompt[:50]}...」的AI生成结果。包含分析、建议和结论。"

    try:
        import requests
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = requests.post(
            BIGMODEL_URL,
            headers={"Authorization": f"Bearer {BIGMODEL_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": messages, "max_tokens": max_tokens},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "[空响应]")
        else:
            return f"[API错误 {resp.status_code}]: {resp.text[:100]}"
    except ImportError:
        warn("未安装 requests 库，使用模拟响应")
        return f"[模拟响应] {prompt[:60]}..."
    except Exception as e:
        return f"[调用失败]: {e}"

def run_test(demo_id: str, name: str, test_fn):
    """Test harness wrapper."""
    header(demo_id, name)
    t0 = time.time()
    try:
        test_fn()
        elapsed = time.time() - t0
        print(f"\n{C.GREEN}  ══ PASS ══ {name} ({elapsed:.1f}s){C.RESET}\n")
        return True
    except Exception as e:
        elapsed = time.time() - t0
        print(f"\n{C.RED}  ══ FAIL ══ {name} ({elapsed:.1f}s): {e}{C.RESET}\n")
        return False

#!/usr/bin/env python3
"""
Comprehensive test suite for uplift_cli.py
Run: python test_cli.py
"""
import json, os, sys, subprocess, time, random, urllib.request

CLI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uplift_cli.py")
PY = sys.executable
PASS = FAIL = 0


def ok(name):
    global PASS; PASS += 1; print(f"  \033[92m✓\033[0m {name}")

def fail(name, e):
    global FAIL; FAIL += 1; print(f"  \033[91m✗\033[0m {name}: {e}")

def test(name, fn):
    try: fn(); ok(name)
    except Exception as e: fail(name, e)

def check(cond, msg="assertion failed"):
    if not cond: raise AssertionError(msg)

def run_cli(*args):
    r = subprocess.run([PY, CLI, *args], capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout, r.stderr

def api_get(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=10) as r:
        return json.loads(r.read())

def api_post(port, path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=body, method="POST",
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


# ── Import engine directly ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplift_cli import (get_success_rate, roll_dice, classify_bottlenecks,
                        compute_stats, execute_agent_task, SCENARIOS)

# ══════════════════════════════════════════════════
# Group 1: Engine Logic
# ══════════════════════════════════════════════════
print("\n\033[1m── Engine Logic ──\033[0m")

test("success_rate: 10h→95%", lambda: check(get_success_rate(10) == 0.95))
test("success_rate: 40h→80%", lambda: check(get_success_rate(40) == 0.80))
test("success_rate: 200h→50%", lambda: check(get_success_rate(200) == 0.50))
test("success_rate: 1000h→5%", lambda: check(get_success_rate(1000) == 0.05))

def test_dice():
    d = roll_dice(0.80)
    check(isinstance(d["roll"], int))
    check(d["threshold"] == 80)
    check(isinstance(d["success"], bool))
test("roll_dice structure", test_dice)

test("bottleneck: 人工收集→human-data", lambda: check("human-data" in classify_bottlenecks("需要人工收集数据")))
test("bottleneck: 训练→ml-experiment", lambda: check("ml-experiment" in classify_bottlenecks("训练深度学习模型")))
test("bottleneck: 评审→peer-review", lambda: check("peer-review" in classify_bottlenecks("等待同事评审反馈")))
test("bottleneck: 无关键词→none", lambda: check("none" in classify_bottlenecks("写一个hello world")))

FIXTURE_5 = [
    {"estimatedHours": 20, "dice": {"success": True}, "bottlenecks": ["human-data"]},
    {"estimatedHours": 30, "dice": {"success": True}, "bottlenecks": ["peer-review"]},
    {"estimatedHours": 50, "dice": {"success": False}, "bottlenecks": ["ml-experiment"]},
    {"estimatedHours": 10, "dice": {"success": True}, "bottlenecks": ["none"]},
    {"estimatedHours": 40, "dice": {"success": False}, "bottlenecks": ["human-data", "decision"]},
]

def test_stats():
    s = compute_stats(FIXTURE_5)
    check(s["totalTasks"] == 5, f"totalTasks={s['totalTasks']}")
    check(s["successCount"] == 3, f"successCount={s['successCount']}")
    check(s["successRate"] == 60, f"successRate={s['successRate']}")
    check(s["totalAgentHours"] == 150, f"hours={s['totalAgentHours']}")
    check(s["bottleneckCounts"]["human-data"] == 2)
test("compute_stats: 5 tasks", test_stats)

test("compute_stats: empty→defaults", lambda: check(compute_stats([])["totalTasks"] == 0))

def test_exec():
    r = execute_agent_task("测试任务", player="测试员")
    check("dice" in r and "bottlenecks" in r and "successRate" in r and "timestamp" in r)
    check(isinstance(r["dice"]["success"], bool))
test("execute_task: offline structure", test_exec)

test("scenarios: all have required fields", lambda: [
    check(all(k in v for k in ["name","players","context"]), f"{sid} missing field")
    for sid, v in SCENARIOS.items()
])

# ══════════════════════════════════════════════════
# Group 2: CLI Commands
# ══════════════════════════════════════════════════
print("\n\033[1m── CLI Commands ──\033[0m")

def test_scenarios_cmd():
    rc, out, _ = run_cli("scenarios")
    check(rc == 0, f"rc={rc}")
    check("newco" in out and "metr" in out and "enterprise" in out)
test("cli: scenarios", test_scenarios_cmd)

def test_task_cmd():
    rc, out, _ = run_cli("task", "--prompt", "写hello world")
    check(rc == 0, f"rc={rc}")
    d = json.loads(out)
    check("dice" in d and "steps" in d)
test("cli: task", test_task_cmd)

def test_sim_quiet():
    rc, out, _ = run_cli("simulate", "--scenario", "newco", "--rounds", "1", "-q")
    check(rc == 0, f"rc={rc}")
test("cli: simulate newco 1r quiet", test_sim_quiet)

def test_sim_output():
    outf = "/tmp/_uplift_test.json"
    rc, _, _ = run_cli("simulate", "--scenario", "metr", "--rounds", "1", "-o", outf)
    check(rc == 0)
    d = json.loads(open(outf).read())
    check(d["scenario"] == "metr")
    check(d["totalTasks"] > 0, f"tasks={d['totalTasks']}")
    os.remove(outf)
test("cli: simulate metr with output", test_sim_output)

def test_sim_enterprise():
    rc, _, _ = run_cli("simulate", "--scenario", "enterprise", "--rounds", "2", "-q")
    check(rc == 0)
test("cli: simulate enterprise 2r", test_sim_enterprise)

def test_sim_full():
    outf = "/tmp/_uplift_full.json"
    rc, _, _ = run_cli("simulate", "--scenario", "newco", "--rounds", "4", "-q", "-o", outf)
    check(rc == 0)
    d = json.loads(open(outf).read())
    check(d["totalTasks"] >= 30, f"tasks={d['totalTasks']}")
    check(d["rounds"] == 4)
    check(d["productivityMultiplier"] > 0)
    check(len(d["allTasks"]) == d["totalTasks"])
    os.remove(outf)
test("cli: simulate newco full 4r", test_sim_full)

# ══════════════════════════════════════════════════
# Group 3: API Server
# ══════════════════════════════════════════════════
print("\n\033[1m── API Server ──\033[0m")

PORT = 18766 + random.randint(0, 200)
srv = subprocess.Popen([PY, CLI, "serve", "--port", str(PORT)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(1.5)

try:
    def test_health():
        d = api_get(PORT, "/api/health")
        check(d["status"] == "ok")
        check(d["engine"] == "uplift_cli")
    test("api: GET /health", test_health)

    def test_api_scenarios():
        d = api_get(PORT, "/api/scenarios")
        check("newco" in d)
        check(len(d["newco"]["players"]) == 3)
    test("api: GET /scenarios", test_api_scenarios)

    def test_api_task():
        d = api_post(PORT, "/api/task", {"task": "调研竞品", "player": "张伟"})
        check("dice" in d and "steps" in d)
        check(d["player"] == "张伟")
    test("api: POST /task", test_api_task)

    def test_api_simulate():
        d = api_post(PORT, "/api/simulate", {"scenario": "metr", "rounds": 1})
        check(d["totalTasks"] > 0)
        check(d["scenario"] == "metr")
    test("api: POST /simulate", test_api_simulate)

    def test_api_stats():
        d = api_post(PORT, "/api/stats", {"tasks": FIXTURE_5})
        check(d["totalTasks"] == 5)
        check(d["successRate"] == 60)
    test("api: POST /stats", test_api_stats)

finally:
    srv.terminate()
    srv.wait(timeout=5)

# ══════════════════════════════════════════════════
# Group 4: Test Data Fixtures
# ══════════════════════════════════════════════════
print("\n\033[1m── Test Data Fixtures ──\033[0m")

large = []
for _ in range(100):
    h = random.randint(2, 250)
    large.append({
        "estimatedHours": h,
        "dice": roll_dice(get_success_rate(h)),
        "bottlenecks": classify_bottlenecks(random.choice([
            "收集客户数据","训练模型","等待评审","外部供应商","决策标准","写代码",
        ])),
    })

test("fixture: 100 tasks valid", lambda: check(len(large) == 100 and all("dice" in t for t in large)))

def test_large_stats():
    s = compute_stats(large)
    check(s["totalTasks"] == 100)
    check(0 < s["successRate"] < 100, f"rate={s['successRate']}")
    check(s["totalAgentHours"] > 0)
test("fixture: 100 tasks stats", test_large_stats)

def test_curve():
    easy = [t for t in large if t["estimatedHours"] <= 40]
    hard = [t for t in large if t["estimatedHours"] > 200]
    if easy and hard:
        er = sum(1 for t in easy if t["dice"]["success"]) / len(easy)
        hr = sum(1 for t in hard if t["dice"]["success"]) / len(hard)
        check(er > hr, f"easy={er:.2f} should > hard={hr:.2f}")
test("fixture: easy > hard success rate", test_curve)

# ══════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════
total = PASS + FAIL
color = "92" if FAIL == 0 else "91"
print(f"\n{'='*50}")
print(f"  \033[{color}m  {PASS} passed / {FAIL} failed / {total} total\033[0m")
print(f"{'='*50}\n")
sys.exit(0 if FAIL == 0 else 1)

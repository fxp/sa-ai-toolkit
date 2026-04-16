#!/usr/bin/env python3
"""
METR Org-Uplift Game — CLI Backend & HTTP API Server
=====================================================
Usage:
  # Run a full auto-simulation (offline dice mode)
  python uplift_cli.py simulate --scenario newco --output results.json

  # Run a single agent task
  python uplift_cli.py task --prompt "调研AI客服竞品" --player "张伟" --context "NewCo创业团队"

  # Start local API server (for frontend integration)
  python uplift_cli.py serve --port 8766

  # Run with real LLM
  python uplift_cli.py simulate --scenario newco --api-key YOUR_KEY --output results.json
"""

import argparse, json, os, sys, random, time, math
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════
# METR Game Engine (Python port of engine.js)
# ══════════════════════════════════════════════════

SUCCESS_CURVE = [
    (10, 0.95), (40, 0.80), (100, 0.65), (200, 0.50), (500, 0.10),
]

BOTTLENECK_PATTERNS = {
    "human-data":    ["collect data", "gather", "interview", "survey", "manual", "人工", "收集", "调研", "访谈"],
    "ml-experiment": ["train", "experiment", "benchmark", "evaluate model", "gpu", "训练", "实验", "跑模型"],
    "peer-review":   ["review", "feedback", "approve", "sign off", "评审", "反馈", "审批", "确认"],
    "external":      ["external", "vendor", "partner", "client", "customer", "外部", "供应商", "客户", "合作方"],
    "decision":      ["decide", "choose", "prioritize", "convention", "standard", "决策", "选择", "优先级", "规范"],
    "coordination":  ["coordinate", "sync", "align", "meeting", "standup", "协调", "同步", "对齐", "会议"],
}

BOTTLENECK_LABELS = {
    "human-data": "人工数据收集", "ml-experiment": "ML实验等待",
    "peer-review": "同事评审", "external": "外部反馈",
    "decision": "决策/规范", "coordination": "跨团队协调", "none": "无瓶颈",
}


def get_success_rate(hours: float) -> float:
    for max_h, rate in SUCCESS_CURVE:
        if hours <= max_h:
            return rate
    return 0.05


def roll_dice(success_rate: float) -> dict:
    roll = random.random()
    return {
        "roll": round(roll * 100),
        "threshold": round(success_rate * 100),
        "success": roll < success_rate,
    }


def classify_bottlenecks(text: str) -> list:
    lower = text.lower()
    found = [k for k, keywords in BOTTLENECK_PATTERNS.items() if any(kw in lower for kw in keywords)]
    return found or ["none"]


def compute_stats(tasks: list, speed_multiplier: float = 2.0) -> dict:
    if not tasks:
        return {"totalTasks": 0, "successCount": 0, "successRate": 0,
                "totalAgentHours": 0, "bottleneckCounts": {}, "productivityMultiplier": 1.0}

    success_count = sum(1 for t in tasks if t.get("dice", {}).get("success"))
    total_hours = sum(t.get("estimatedHours", 0) for t in tasks)

    bn_counts = {}
    for t in tasks:
        for b in t.get("bottlenecks", []):
            bn_counts[b] = bn_counts.get(b, 0) + 1

    baseline_days = total_hours / 8
    wall_clock_days = 2

    return {
        "totalTasks": len(tasks),
        "successCount": success_count,
        "successRate": round(success_count / len(tasks) * 100) if tasks else 0,
        "totalAgentHours": round(total_hours),
        "avgHoursPerTask": round(total_hours / len(tasks)) if tasks else 0,
        "bottleneckCounts": bn_counts,
        "productivityMultiplier": round(baseline_days / wall_clock_days, 1) if baseline_days > 0 else 1.0,
    }


# ══════════════════════════════════════════════════
# LLM Integration (BigModel GLM)
# ══════════════════════════════════════════════════

def call_llm(prompt: str, system: str = "", api_key: str = "", max_tokens: int = 800) -> str:
    if not api_key:
        return mock_llm(prompt)
    try:
        import requests
        resp = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "glm-4-flash",
                "messages": [
                    *([ {"role": "system", "content": system} ] if system else []),
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return f"[API {resp.status_code}]"
    except Exception as e:
        return f"[LLM error: {e}]"


def mock_llm(prompt: str) -> str:
    return json.dumps({
        "steps": ["分析任务需求和约束条件", "搜索相关资料和已有代码/文档", "生成初版产出物并自检"],
        "deliverable": f"针对「{prompt[:30]}...」的初版交付物",
        "estimatedHours": random.randint(5, 44),
        "blockers": random.choice([[], ["需要确认输出格式偏好", "某些数据源需要人工提供"]]),
        "confidence": random.choice(["high", "medium", "low"]),
        "notes": "[离线模式]",
    }, ensure_ascii=False)


def execute_agent_task(task: str, context: str = "", player: str = "",
                       scenario: str = "", api_key: str = "",
                       time_horizon: int = 200, speed: float = 2.0) -> dict:
    system = f"""你是一个模拟的高级AI Agent，正在参与"组织生产力提升"桌面推演实验。
能力参数：时间窗口{time_horizon}h，速度{speed}x。
场景：{scenario or '通用'}。主人：{player or '研究员'}。
请用JSON回复：{{"steps":[],"deliverable":"","estimatedHours":数字,"blockers":[],"confidence":"high/medium/low","notes":""}}"""

    raw = call_llm(f"任务：{task}\n上下文：{context or '无'}", system=system, api_key=api_key)

    # Parse JSON from response
    try:
        m = __import__("re").search(r"\{[\s\S]*\}", raw)
        result = json.loads(m.group()) if m else {}
    except Exception:
        result = {}

    if not result.get("steps"):
        result = {
            "steps": ["分析任务需求", "搜索相关资料", "生成产出物"],
            "deliverable": f"「{task[:30]}」的产出物",
            "estimatedHours": random.randint(5, 44),
            "blockers": [], "confidence": "medium", "notes": raw[:200],
        }

    hours = result.get("estimatedHours", 20)
    rate = get_success_rate(hours)
    dice = roll_dice(rate)
    bottlenecks = classify_bottlenecks(" ".join(result.get("blockers", [])) + " " + task)

    return {
        **result,
        "task": task,
        "player": player,
        "successRate": round(rate * 100),
        "dice": dice,
        "bottlenecks": bottlenecks,
        "timestamp": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════
# Scenarios & Simulation Scripts
# ══════════════════════════════════════════════════

SCENARIOS = {
    "metr": {
        "name": "METR原始场景",
        "players": [
            {"name": "Alice", "role": "研究经理", "project": "模型能力评估框架设计"},
            {"name": "Bob", "role": "研究员", "project": "Agent自主性基准测试"},
            {"name": "Carol", "role": "研究员", "project": "安全对齐评估工具开发"},
        ],
        "context": "METR研究团队评估2026年AI模型能力边界。",
    },
    "newco": {
        "name": "NewCo客服产品",
        "players": [
            {"name": "张伟", "role": "产品经理", "project": "客服产品PRD和原型设计"},
            {"name": "李娜", "role": "全栈工程师", "project": "MVP后端API和前端开发"},
            {"name": "王鹏", "role": "AI工程师", "project": "客服对话模型微调和集成"},
        ],
        "context": "NewCo创业团队，2天内完成AI智能客服MVP。",
    },
    "enterprise": {
        "name": "企业数字化转型",
        "players": [
            {"name": "刘总", "role": "数字化负责人", "project": "AI落地路线图"},
            {"name": "赵工", "role": "数据工程师", "project": "产线数据接入"},
            {"name": "孙莉", "role": "业务分析师", "project": "缺陷检测POC"},
            {"name": "周强", "role": "安全工程师", "project": "安全评估"},
        ],
        "context": "大型制造企业2天内拿出AI赋能POC。",
    },
}

# Pre-scripted agent tasks for auto-simulation (per round, per player)
SIM_TASKS = {
    "newco": [
        # Round 1
        [
            ["调研AI客服行业Top5竞品的技术架构和定价策略", "基于竞品分析生成差异化定位文档", "撰写PRD初稿：用户画像+功能列表+优先级"],
            ["搭建Next.js+FastAPI项目脚手架和Docker环境", "设计RESTful API schema：对话管理+工单CRUD", "实现用户认证API（JWT+注册/登录）"],
            ["对比GLM-5/DeepSeek/Qwen在客服场景的benchmark", "收集清洗5000条中文客服对话训练数据", "编写GLM-5 LoRA微调脚本并启动训练"],
        ],
        # Round 2
        [
            ["设计客服聊天界面Figma原型", "生成用户测试问卷覆盖5个核心场景", "整理AI客服市场TAM/SAM/SOM分析"],
            ["实现对话管理API含WebSocket实时推送", "实现前端聊天组件：消息列表+输入框+状态", "编写AI模型调用适配层：超时处理+降级策略"],
            ["评估微调模型效果并部署推理服务", "编写推理API：流式输出+对话历史+安全过滤", "优化推理延迟：KV-cache+INT8量化"],
        ],
        # Round 3
        [
            ["生成产品演示脚本：3个核心场景话术", "制作投资人pitch deck 12页PPT", "撰写产品landing page文案"],
            ["实现后端-AI模型完整集成：消息路由+错误处理", "实现前端管理后台：工单看板+仪表盘", "编写Playwright端到端测试覆盖5个流程"],
            ["实现内容安全过滤：敏感词+幻觉检测", "实现多轮对话记忆管理：摘要+上下文窗口", "压测推理服务：50/100并发延迟和错误率"],
        ],
        # Round 4
        [
            ["录制3分钟产品演示视频脚本", "生成项目总结报告：架构+指标+计划", "生成2天工作复盘：AI贡献度+瓶颈归因"],
            ["修复聊天界面消息顺序bug+重试机制", "优化首屏性能：代码分割+图片懒加载", "部署最终版到演示环境并配置监控"],
            ["调优内容过滤规则降低误拦截率", "添加A/B测试框架支持prompt策略对比", "生成最终性能报告：P50/P95/P99+成本估算"],
        ],
    ],
}


def run_simulation(scenario_id: str, api_key: str = "", rounds: int = 4,
                   hours_per_round: int = 5, verbose: bool = True) -> dict:
    sc = SCENARIOS.get(scenario_id)
    if not sc:
        print(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIOS.keys())}", file=sys.stderr)
        sys.exit(1)

    tasks_script = SIM_TASKS.get(scenario_id)
    players = sc["players"]
    context = sc["context"]
    all_tasks = []
    round_data = {}

    if verbose:
        print(f"\n{'='*60}")
        print(f"  METR Org-Uplift Game — {sc['name']}")
        print(f"  {len(players)} players × {rounds} rounds × {hours_per_round}h/round")
        print(f"  API: {'GLM (online)' if api_key else 'offline (dice mode)'}")
        print(f"{'='*60}\n")

    for r in range(rounds):
        round_key = f"r{r+1}"
        round_names = ["Day1上午", "Day1下午", "Day2上午", "Day2下午"]
        round_tasks = []

        if verbose:
            print(f"  ── 回合 {r+1} ({round_names[r]}) ──")

        round_data[round_key] = {"standups": [], "hours": []}

        for pi, player in enumerate(players):
            player_tasks_this_round = []

            # Get scripted tasks or generate generic ones
            if tasks_script and r < len(tasks_script) and pi < len(tasks_script[r]):
                scripted = tasks_script[r][pi]
            else:
                scripted = [f"{player['role']}完成{player['project']}的第{r+1}阶段工作"]

            for ti, task_prompt in enumerate(scripted):
                result = execute_agent_task(
                    task=task_prompt,
                    context=f"{context}\n当前项目: {player['project']}",
                    player=player["name"],
                    scenario=context,
                    api_key=api_key,
                )
                result["round"] = r + 1
                result["playerIndex"] = pi
                result["hour"] = ti

                all_tasks.append(result)
                player_tasks_this_round.append(result)

                icon = "✓" if result["dice"]["success"] else "✗"
                if verbose:
                    print(f"    {icon} {player['name']} [H{ti+1}]: {task_prompt[:50]}..."
                          f" ({result['dice']['roll']}/{result['dice']['threshold']}"
                          f" {result['estimatedHours']}h {result['confidence']})")

            round_data[round_key]["hours"].append(player_tasks_this_round)

        round_stats = compute_stats([t for t in all_tasks if t["round"] == r + 1])
        if verbose:
            print(f"    → 回合{r+1}: {round_stats['totalTasks']}任务"
                  f" {round_stats['successRate']}%成功"
                  f" {round_stats['totalAgentHours']}h\n")

    # Final report
    final = compute_stats(all_tasks)
    final["scenario"] = scenario_id
    final["scenarioName"] = sc["name"]
    final["players"] = players
    final["rounds"] = rounds
    final["allTasks"] = all_tasks
    final["roundData"] = round_data
    final["bottleneckLabels"] = {k: BOTTLENECK_LABELS.get(k, k) for k in final["bottleneckCounts"]}
    final["generated"] = datetime.now().isoformat()

    if verbose:
        print(f"{'='*60}")
        print(f"  最终报告")
        print(f"  生产力倍增: {final['productivityMultiplier']}x (METR基准: 3-5x)")
        print(f"  任务总量: {final['totalTasks']} | 成功率: {final['successRate']}%")
        print(f"  Agent工时: {final['totalAgentHours']}h")
        print(f"  瓶颈分布:")
        for k, v in sorted(final["bottleneckCounts"].items(), key=lambda x: -x[1]):
            if k != "none":
                pct = round(v / final["totalTasks"] * 100)
                print(f"    {BOTTLENECK_LABELS.get(k, k)}: {v}次 ({pct}%)")
        print(f"{'='*60}\n")

    return final


# ══════════════════════════════════════════════════
# HTTP API Server (for frontend integration)
# ══════════════════════════════════════════════════

API_KEY_GLOBAL = ""

class APIHandler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, data):
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/scenarios":
            self._json(200, {k: {**v, "id": k} for k, v in SCENARIOS.items()})
        elif self.path == "/api/health":
            self._json(200, {"status": "ok", "demos": len(SCENARIOS), "engine": "uplift_cli"})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if self.path == "/api/task":
            result = execute_agent_task(
                task=body.get("task", ""),
                context=body.get("context", ""),
                player=body.get("player", ""),
                scenario=body.get("scenario", ""),
                api_key=body.get("apiKey", API_KEY_GLOBAL),
            )
            self._json(200, result)

        elif self.path == "/api/simulate":
            result = run_simulation(
                scenario_id=body.get("scenario", "newco"),
                api_key=body.get("apiKey", API_KEY_GLOBAL),
                rounds=body.get("rounds", 4),
                verbose=False,
            )
            self._json(200, result)

        elif self.path == "/api/stats":
            tasks = body.get("tasks", [])
            self._json(200, compute_stats(tasks))

        else:
            self._json(404, {"error": "not found"})

    def log_message(self, format, *args):
        print(f"  [API] {args[0]}" if args else "", file=sys.stderr)


# ══════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="METR Org-Uplift Game CLI")
    sub = parser.add_subparsers(dest="command")

    # simulate
    p_sim = sub.add_parser("simulate", help="Run full auto-simulation")
    p_sim.add_argument("--scenario", default="newco", choices=list(SCENARIOS.keys()))
    p_sim.add_argument("--rounds", type=int, default=4)
    p_sim.add_argument("--api-key", default=os.getenv("BIGMODEL_API_KEY", ""))
    p_sim.add_argument("--output", "-o", default="")
    p_sim.add_argument("--quiet", "-q", action="store_true")

    # task
    p_task = sub.add_parser("task", help="Execute a single agent task")
    p_task.add_argument("--prompt", required=True)
    p_task.add_argument("--player", default="研究员")
    p_task.add_argument("--context", default="")
    p_task.add_argument("--api-key", default=os.getenv("BIGMODEL_API_KEY", ""))

    # serve
    p_serve = sub.add_parser("serve", help="Start local API server")
    p_serve.add_argument("--port", type=int, default=8766)
    p_serve.add_argument("--api-key", default=os.getenv("BIGMODEL_API_KEY", ""))

    # scenarios
    sub.add_parser("scenarios", help="List available scenarios")

    args = parser.parse_args()

    if args.command == "simulate":
        result = run_simulation(
            scenario_id=args.scenario,
            api_key=args.api_key,
            rounds=args.rounds,
            verbose=not args.quiet,
        )
        if args.output:
            Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  → 结果已保存到 {args.output}")

    elif args.command == "task":
        result = execute_agent_task(
            task=args.prompt, player=args.player,
            context=args.context, api_key=args.api_key,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "serve":
        global API_KEY_GLOBAL
        API_KEY_GLOBAL = args.api_key
        server = HTTPServer(("127.0.0.1", args.port), APIHandler)
        print(f"\n  Org-Uplift API Server running on http://127.0.0.1:{args.port}")
        print(f"  Endpoints: GET /api/scenarios | POST /api/task | POST /api/simulate | GET /api/health")
        print(f"  API Key: {'configured' if args.api_key else 'offline mode'}\n")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")

    elif args.command == "scenarios":
        for k, v in SCENARIOS.items():
            print(f"  {k:15s} {v['name']:20s} {len(v['players'])}人 — {v['context'][:40]}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

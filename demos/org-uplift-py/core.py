"""
Org-Uplift core — METR-style dice game engine.

Ported/condensed from demos/demo-metr-org-uplift/uplift_cli.py into a pure
business-logic module (no HTTP code).
"""
from __future__ import annotations

import json
import random
import re
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# METR capability curve + bottleneck patterns
# ---------------------------------------------------------------------------

SUCCESS_CURVE: list[tuple[int, float]] = [
    (10, 0.95), (40, 0.80), (100, 0.65), (200, 0.50), (500, 0.10),
]

BOTTLENECK_PATTERNS: dict[str, list[str]] = {
    "human-data":    ["collect data", "gather", "interview", "survey", "manual",
                      "人工", "收集", "调研", "访谈"],
    "ml-experiment": ["train", "experiment", "benchmark", "evaluate model", "gpu",
                      "训练", "实验", "跑模型"],
    "peer-review":   ["review", "feedback", "approve", "sign off",
                      "评审", "反馈", "审批", "确认"],
    "external":      ["external", "vendor", "partner", "client", "customer",
                      "外部", "供应商", "客户", "合作方"],
    "decision":      ["decide", "choose", "prioritize", "convention", "standard",
                      "决策", "选择", "优先级", "规范"],
    "coordination":  ["coordinate", "sync", "align", "meeting", "standup",
                      "协调", "同步", "对齐", "会议"],
}

BOTTLENECK_LABELS: dict[str, str] = {
    "human-data": "人工数据收集",
    "ml-experiment": "ML实验等待",
    "peer-review": "同事评审",
    "external": "外部反馈",
    "decision": "决策/规范",
    "coordination": "跨团队协调",
    "none": "无瓶颈",
}


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict] = {
    "metr": {
        "name": "METR原始场景",
        "players": [
            {"name": "Alice", "role": "研究经理", "project": "模型能力评估框架设计"},
            {"name": "Bob",   "role": "研究员",   "project": "Agent自主性基准测试"},
            {"name": "Carol", "role": "研究员",   "project": "安全对齐评估工具开发"},
        ],
        "context": "METR研究团队评估2026年AI模型能力边界。",
    },
    "newco": {
        "name": "NewCo客服产品",
        "players": [
            {"name": "张伟", "role": "产品经理",   "project": "客服产品PRD和原型设计"},
            {"name": "李娜", "role": "全栈工程师", "project": "MVP后端API和前端开发"},
            {"name": "王鹏", "role": "AI工程师",   "project": "客服对话模型微调和集成"},
        ],
        "context": "NewCo创业团队，2天内完成AI智能客服MVP。",
    },
    "enterprise": {
        "name": "企业数字化转型",
        "players": [
            {"name": "刘总", "role": "数字化负责人", "project": "AI落地路线图"},
            {"name": "赵工", "role": "数据工程师",   "project": "产线数据接入"},
            {"name": "孙莉", "role": "业务分析师",   "project": "缺陷检测POC"},
            {"name": "周强", "role": "安全工程师",   "project": "安全评估"},
        ],
        "context": "大型制造企业2天内拿出AI赋能POC。",
    },
}


# ---------------------------------------------------------------------------
# Engine primitives
# ---------------------------------------------------------------------------

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


def classify_bottlenecks(text: str) -> list[str]:
    lower = (text or "").lower()
    found = [k for k, kws in BOTTLENECK_PATTERNS.items()
             if any(kw in lower for kw in kws)]
    return found or ["none"]


def _mock_plan(task: str) -> dict:
    return {
        "steps": ["分析任务需求和约束条件", "搜索相关资料和已有代码/文档", "生成初版产出物并自检"],
        "deliverable": f"针对「{task[:30]}」的初版交付物",
        "estimatedHours": random.randint(5, 44),
        "blockers": random.choice([[], ["需要确认输出格式偏好", "某些数据源需要人工提供"]]),
        "confidence": random.choice(["high", "medium", "low"]),
        "notes": "[离线模式 - 模拟Agent计划]",
    }


def execute_task(task_description: str,
                 context: str = "",
                 player: str = "",
                 scenario: str = "") -> dict:
    """Execute a simulated agent task: plan + dice + bottleneck classification.

    Always offline/mock (no LLM call); deterministic shape for downstream tests.
    """
    plan = _mock_plan(task_description)
    hours = plan.get("estimatedHours", 20)
    rate = get_success_rate(hours)
    dice = roll_dice(rate)
    bottlenecks = classify_bottlenecks(
        " ".join(plan.get("blockers", [])) + " " + task_description
    )
    return {
        **plan,
        "task": task_description,
        "context": context,
        "player": player,
        "scenario": scenario,
        "successRate": round(rate * 100),
        "dice": dice,
        "bottlenecks": bottlenecks,
        "timestamp": datetime.now().isoformat(),
    }


def compute_stats(tasks: list[dict], speed_multiplier: float = 2.0) -> dict:
    """Aggregate a list of executed tasks into summary stats."""
    if not tasks:
        return {
            "totalTasks": 0, "successCount": 0, "successRate": 0,
            "totalAgentHours": 0, "avgHoursPerTask": 0,
            "bottleneckCounts": {}, "productivityMultiplier": 1.0,
        }

    success_count = sum(1 for t in tasks if (t.get("dice") or {}).get("success"))
    total_hours = sum(float(t.get("estimatedHours") or 0) for t in tasks)

    bn_counts: dict[str, int] = {}
    for t in tasks:
        for b in t.get("bottlenecks", []):
            bn_counts[b] = bn_counts.get(b, 0) + 1

    baseline_days = total_hours / 8
    wall_clock_days = 2

    return {
        "totalTasks": len(tasks),
        "successCount": success_count,
        "successRate": round(success_count / len(tasks) * 100),
        "totalAgentHours": round(total_hours),
        "avgHoursPerTask": round(total_hours / len(tasks)),
        "bottleneckCounts": bn_counts,
        "bottleneckLabels": {k: BOTTLENECK_LABELS.get(k, k) for k in bn_counts},
        "productivityMultiplier": round(baseline_days / wall_clock_days, 1)
            if baseline_days > 0 else 1.0,
    }

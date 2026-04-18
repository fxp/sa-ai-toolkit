#!/usr/bin/env python3
"""Org-Uplift CLI — execute tasks, compute stats, list scenarios."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import execute_task, compute_stats, SCENARIOS  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Org-Uplift METR-style game engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_exec = sub.add_parser("execute", help="Execute a single agent task")
    p_exec.add_argument("--task", required=True)
    p_exec.add_argument("--context", default="")
    p_exec.add_argument("--player", default="研究员")
    p_exec.add_argument("--scenario", default="")

    p_stats = sub.add_parser("stats", help="Aggregate stats from tasks JSON file")
    p_stats.add_argument("--tasks-json", required=True)

    sub.add_parser("scenarios", help="List built-in scenarios")

    args = p.parse_args()

    if args.cmd == "execute":
        res = execute_task(args.task, args.context, args.player, args.scenario)
        print(json.dumps(res, ensure_ascii=False, indent=2))

    elif args.cmd == "stats":
        tasks = json.loads(Path(args.tasks_json).read_text(encoding="utf-8"))
        if isinstance(tasks, dict) and "tasks" in tasks:
            tasks = tasks["tasks"]
        print(json.dumps(compute_stats(tasks), ensure_ascii=False, indent=2))

    elif args.cmd == "scenarios":
        for k, v in SCENARIOS.items():
            print(f"  {k:12s}  {v['name']:20s}  {len(v['players'])} players — {v['context'][:40]}")


if __name__ == "__main__":
    main()

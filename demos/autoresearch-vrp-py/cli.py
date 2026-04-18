#!/usr/bin/env python3
"""AutoResearch-for-VRP CLI."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import (  # noqa: E402
    VARIANTS, NUM_ITERATIONS,
    run_iteration, run_full, build_trajectory_md, build_benchmark, evaluate,
)


def main() -> None:
    p = argparse.ArgumentParser(description="AutoResearch for VRP")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_iter = sub.add_parser("iterate", help="Run one solver variant")
    p_iter.add_argument("--idx", type=int, required=True)
    p_iter.add_argument("--lang", default="en", choices=["en", "zh"])

    p_full = sub.add_parser("full", help="Run the full trajectory")
    p_full.add_argument("--lang", default="en", choices=["en", "zh"])
    p_full.add_argument("--output", "-o", default="")

    sub.add_parser("list", help="List variants")

    args = p.parse_args()

    if args.cmd == "iterate":
        res = run_iteration(args.idx, lang=args.lang)
        print(json.dumps({
            "iter": res["iter"], "name": res["name"],
            "metric": res["metric"],
            "feasible": res["feasible"],
            "kept": res["kept"],
            "best_so_far": res["best_so_far"],
            "commentary": res["commentary"],
            "routes": [{"vehicle": r["vehicle"], "customers": r["customers"],
                        "distance": r["distance"], "load": r["load"]} for r in res["routes"]],
        }, ensure_ascii=False, indent=2))

    elif args.cmd == "full":
        print(f"Running {NUM_ITERATIONS} VRP variants on the frozen benchmark...", file=sys.stderr)
        inst = build_benchmark()
        for v in VARIANTS:
            m = evaluate(inst, v["fn"](inst))
            tag = "ok" if m["over_capacity"] == 0 and m["missing_customers"] == 0 else "INFEAS"
            print(f"  v{v['idx']}  {v['name']:<22}  d={m['total_distance']:<7}  routes={m['num_routes']}  {tag}",
                  file=sys.stderr)
        report = build_trajectory_md(lang=args.lang)
        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
            print(f"→ Report saved to {args.output}", file=sys.stderr)
        else:
            print(report)

    elif args.cmd == "list":
        for v in VARIANTS:
            print(f"  v{v['idx']:<2} {v['name']:<22} / {v['name_zh']}")
            print(f"        ↳ {v['hypothesis']}")


if __name__ == "__main__":
    main()

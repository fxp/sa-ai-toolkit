#!/usr/bin/env python3
"""AutoResearch CLI — run a single stage or the full 23-stage pipeline."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import STAGES, NUM_STAGES, run_stage, run_full, build_report  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="AutoResearch 23-stage pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_stage = sub.add_parser("stage", help="Run a single stage")
    p_stage.add_argument("--topic", required=True)
    p_stage.add_argument("--idx", type=int, required=True)

    p_full = sub.add_parser("full", help="Run all 23 stages and build report")
    p_full.add_argument("--topic", required=True)
    p_full.add_argument("--lang", default="en", choices=["en", "zh"])
    p_full.add_argument("--output", "-o", default="")

    p_list = sub.add_parser("list", help="List all stages")
    _ = p_list

    args = p.parse_args()

    if args.cmd == "stage":
        res = run_stage(args.topic, args.idx)
        print(json.dumps(res, ensure_ascii=False, indent=2))

    elif args.cmd == "full":
        print(f"Running {NUM_STAGES} stages for: {args.topic}", file=sys.stderr)
        out = run_full(args.topic, lang=args.lang)
        for r in out["results"]:
            tag = "SEARCH" if r["uses_search"] else "      "
            print(f"  [{r['stage_idx']+1:02d}/{NUM_STAGES}] {tag} {r['name']}  "
                  f"({r['duration_ms']}ms, {len(r['search_results'])} sources)",
                  file=sys.stderr)
        if args.output:
            Path(args.output).write_text(out["report"], encoding="utf-8")
            print(f"→ Report saved to {args.output}", file=sys.stderr)
        else:
            print(out["report"])

    elif args.cmd == "list":
        for i, s in enumerate(STAGES):
            tag = "🔍" if s["uses_search"] else "  "
            print(f"  {i:2d}. {tag} {s['name']}  /  {s['name_zh']}")


if __name__ == "__main__":
    main()

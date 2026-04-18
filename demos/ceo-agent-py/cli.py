"""CLI for CEO Agent.

Examples:
  python cli.py brief --company NewCo --brief-idx 0 --lang en
  python cli.py metrics --company NewCo --lang zh
  python cli.py all --company NewCo
"""
from __future__ import annotations

import argparse
import json
import sys

from core import CEOAgent


def _add_common(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--company", default="NewCo Inc")
    sp.add_argument("--lang", default="en", choices=["en", "zh"])


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CEO Agent CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("brief"); _add_common(pb); pb.add_argument("--brief-idx", type=int, default=0)
    for name in ("metrics", "decisions", "mood", "competitors", "actions"):
        _add_common(sub.add_parser(name))
    pa = sub.add_parser("all"); _add_common(pa); pa.add_argument("--brief-idx", type=int, default=0)

    args = p.parse_args(argv)
    agent = CEOAgent(company=args.company)

    if args.cmd == "brief":       out = agent.morning_brief(args.brief_idx, args.lang)
    elif args.cmd == "metrics":   out = agent.metrics(args.lang)
    elif args.cmd == "decisions": out = agent.decisions(args.lang)
    elif args.cmd == "mood":      out = agent.mood_heatmap(args.lang)
    elif args.cmd == "competitors": out = agent.competitor_feed(args.lang)
    elif args.cmd == "actions":   out = agent.action_queue(args.lang)
    elif args.cmd == "all":       out = agent.all(args.brief_idx, args.lang)
    else:
        p.print_help(); return 1

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

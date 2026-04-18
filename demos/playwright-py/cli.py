#!/usr/bin/env python3
"""Playwright demo CLI — simulate or really drive a browser."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import simulate_run, run_real, SCENARIOS  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Playwright demo: simulate or run browser tests")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_sim = sub.add_parser("simulate", help="Return deterministic trace (no browser)")
    p_sim.add_argument("--scenario", default="bing", choices=list(SCENARIOS.keys()))

    p_real = sub.add_parser("real", help="Drive real Chromium (requires playwright)")
    p_real.add_argument("--scenario", default="bing", choices=list(SCENARIOS.keys()))
    p_real.add_argument("--url", default=None)

    sub.add_parser("scenarios", help="List preset scenarios")

    args = p.parse_args()

    if args.cmd == "simulate":
        trace = simulate_run(args.scenario)
        print(json.dumps(trace, ensure_ascii=False, indent=2))

    elif args.cmd == "real":
        try:
            trace = run_real(args.scenario, url=args.url)
        except ImportError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(2)
        # Don't dump base64 screenshots to stdout — too noisy
        for step in trace:
            size = len(step["screenshot_b64"] or "")
            step["screenshot_b64"] = f"<{size} bytes base64>" if size else None
        print(json.dumps(trace, ensure_ascii=False, indent=2))

    elif args.cmd == "scenarios":
        for k, v in SCENARIOS.items():
            print(f"  {k:12s}  {v['title']:32s} {len(v['actions'])} actions")


if __name__ == "__main__":
    main()

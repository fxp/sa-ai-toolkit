"""gstack CLI — prints command script as JSON."""
from __future__ import annotations

import argparse
import json
import sys

from core import run_command


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="gstack command simulator")
    sub = parser.add_subparsers(dest="action", required=True)

    r = sub.add_parser("run", help="Run a gstack command and print script JSON")
    r.add_argument("--command", required=True,
                   choices=["office-hours", "autoplan", "qa", "ship"])
    r.add_argument("--input", default=None, help="Optional user input text")

    args = parser.parse_args(argv)

    if args.action == "run":
        script = run_command(args.command, args.input)
        print(json.dumps({"command": args.command, "script": script},
                         ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

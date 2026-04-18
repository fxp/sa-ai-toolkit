"""Maestro CLI — parse or simulate a flow YAML file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core import parse_yaml, simulate_execution


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Maestro YAML tools")
    sub = p.add_subparsers(dest="action", required=True)

    pp = sub.add_parser("parse", help="Parse a YAML file and print JSON")
    pp.add_argument("--yaml-file", required=True)

    ss = sub.add_parser("simulate", help="Simulate the flow and print the trace")
    ss.add_argument("--yaml-file", required=True)

    args = p.parse_args(argv)
    text = Path(args.yaml_file).read_text(encoding="utf-8")
    parsed = parse_yaml(text)

    if args.action == "parse":
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
        return 0
    if args.action == "simulate":
        trace = simulate_execution(parsed)
        print(json.dumps({"parsed": parsed, "trace": trace},
                         ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""SA Toolkit CLI.

  python cli.py gen --company Tencent
  python cli.py customize --package-json p.json --replace from:to
  python cli.py present --package-json p.json --mode rehearse
  python cli.py present --package-json p.json --mode email
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core import (
    deepen_demo,
    export_email,
    generate_package,
    rehearse,
    replace_terms,
    search_company,
    switch_audience,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen")
    g.add_argument("--company", required=True)

    c = sub.add_parser("customize")
    c.add_argument("--package-json", required=True)
    c.add_argument("--replace", action="append", default=[], help="from:to, repeatable")
    c.add_argument("--deepen", default="")
    c.add_argument("--audience", default="")

    pr = sub.add_parser("present")
    pr.add_argument("--package-json", required=True)
    pr.add_argument("--mode", choices=["rehearse", "email"], default="rehearse")

    args = p.parse_args(argv)

    if args.cmd == "gen":
        info = search_company(args.company)
        pkg = generate_package(info)
        print(json.dumps(pkg, ensure_ascii=False, indent=2))
        return 0

    pkg = json.loads(Path(args.package_json).read_text(encoding="utf-8"))

    if args.cmd == "customize":
        if args.replace:
            mapping = dict(r.split(":", 1) for r in args.replace if ":" in r)
            pkg = replace_terms(pkg, mapping)
        if args.deepen:
            pkg = deepen_demo(pkg, args.deepen)
        if args.audience:
            pkg = switch_audience(pkg, args.audience)
        print(json.dumps(pkg, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "present":
        if args.mode == "rehearse":
            print(json.dumps(rehearse(pkg), ensure_ascii=False, indent=2))
        else:
            print(export_email(pkg))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

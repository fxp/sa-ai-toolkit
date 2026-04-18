"""Enterprise Gen CLI.

  python cli.py score --company Acme --industry banking --pain doc,risk --audience executives --minutes 90
  python cli.py generate --company Acme --industry tech --pain km,collab --minutes 60
"""
from __future__ import annotations

import argparse
import json
import sys

from core import generate_package, score_demos


def _profile_from_args(a: argparse.Namespace) -> dict:
    return {
        "company": a.company,
        "industry": a.industry,
        "audience": a.audience,
        "minutes": a.minutes,
        "size": a.size,
        "pain_points": [p.strip() for p in (a.pain or "").split(",") if p.strip()],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("score", "generate"):
        sp = sub.add_parser(name)
        sp.add_argument("--company", default="Acme Corp")
        sp.add_argument("--industry", default="tech")
        sp.add_argument("--audience", default="executives")
        sp.add_argument("--minutes", type=int, default=90)
        sp.add_argument("--size", default="500-5000")
        sp.add_argument("--pain", default="")
    args = p.parse_args(argv)
    profile = _profile_from_args(args)
    out = score_demos(profile) if args.cmd == "score" else generate_package(profile)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

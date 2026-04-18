"""Karpathy KB CLI — extract concepts or lint an existing concept list."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core import extract_concepts, lint_kb


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Karpathy KB tools")
    sub = p.add_subparsers(dest="action", required=True)

    e = sub.add_parser("extract", help="Extract concepts from text")
    g = e.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Inline text")
    g.add_argument("--file", help="Path to a text file")
    e.add_argument("--n", type=int, default=5)

    l = sub.add_parser("lint", help="Lint an existing concepts JSON file")
    l.add_argument("--concepts-json", required=True, help="Path to concepts JSON")

    args = p.parse_args(argv)

    if args.action == "extract":
        text = args.text if args.text is not None else Path(args.file).read_text(encoding="utf-8")
        concepts = extract_concepts(text, args.n)
        print(json.dumps({"concepts": concepts}, ensure_ascii=False, indent=2))
        return 0

    if args.action == "lint":
        concepts = json.loads(Path(args.concepts_json).read_text(encoding="utf-8"))
        if isinstance(concepts, dict) and "concepts" in concepts:
            concepts = concepts["concepts"]
        report = lint_kb(concepts)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())

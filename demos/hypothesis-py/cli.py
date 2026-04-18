"""Hypothesis CLI — classify sentences in a text or file into 4 tags."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core import classify_sentences


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Hypothesis annotator")
    sub = parser.add_subparsers(dest="action", required=True)

    a = sub.add_parser("annotate", help="Annotate text and print JSON")
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Text to classify")
    g.add_argument("--file", help="Path to a file containing text")

    args = parser.parse_args(argv)

    if args.action == "annotate":
        text = args.text if args.text is not None else Path(args.file).read_text(encoding="utf-8")
        items = classify_sentences(text)
        print(json.dumps({"annotations": items}, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

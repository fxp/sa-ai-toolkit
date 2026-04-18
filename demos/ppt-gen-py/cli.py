"""PPT Gen CLI.

  python cli.py gen --config config.json --output deck.pptx

config.json shape:
  {
    "title": "Deck title",
    "subtitle": "optional",
    "theme": "blue-orange",
    "slides": [
      {"template": "agenda", "fields": {"title": "Agenda", "content": "Item 1\\nItem 2"}},
      {"template": "data",   "fields": {"title": "Adoption", "big_number": "78%", "description": "of enterprises...", "source": "OpenClaw 2026"}}
    ]
  }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core import generate_pptx


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--config", required=True)
    g.add_argument("--output", required=True)
    args = p.parse_args(argv)

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    data = generate_pptx(
        title=cfg.get("title", "Untitled"),
        subtitle=cfg.get("subtitle", ""),
        slides=cfg.get("slides", []),
        theme=cfg.get("theme", "blue-orange"),
    )
    Path(args.output).write_bytes(data)
    print(json.dumps({"output": args.output, "bytes": len(data)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

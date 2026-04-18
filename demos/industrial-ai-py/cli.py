#!/usr/bin/env python3
"""Industrial AI CLI — perception / prediction / diagnosis / full pipeline."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import (  # noqa: E402
    PerceptionLayer, PredictionLayer, run_pipeline,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Industrial AI 4-layer pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("detect",   help="Run perception layer (visual + audio)")
    sub.add_parser("predict",  help="Run prediction layer (yield forecast + RUL)")
    sub.add_parser("diagnose", help="Run full pipeline and emit diagnosis only")

    p_run = sub.add_parser("run", help="Run full pipeline")
    p_run.add_argument("--llm", action="store_true")
    p_run.add_argument("--output", "-o", default="")
    p_run.add_argument("--quiet", "-q", action="store_true")

    args = p.parse_args()

    if args.cmd == "detect":
        v = PerceptionLayer.detect_visual(text_prompt="defect on battery cell")
        a = PerceptionLayer.detect_audio()
        print(json.dumps({"visual": v, "audio": a}, ensure_ascii=False, indent=2))

    elif args.cmd == "predict":
        y = PredictionLayer.forecast(None, 72, "良率(%)")
        r = PredictionLayer.predict_equipment_rul()
        print(json.dumps({"yield": y, "rul": r}, ensure_ascii=False, indent=2))

    elif args.cmd == "diagnose":
        report = run_pipeline(use_llm=False, verbose=False)
        print(json.dumps(report["diagnosis"], ensure_ascii=False, indent=2))

    elif args.cmd == "run":
        report = run_pipeline(use_llm=args.llm, verbose=not args.quiet)
        if args.output:
            Path(args.output).write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"→ Report saved to {args.output}", file=sys.stderr)
        elif args.quiet:
            print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

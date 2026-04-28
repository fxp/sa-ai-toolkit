"""Persona Distill CLI."""
from __future__ import annotations
import argparse, json, sys, pathlib
from core import (
    search_persona, extract_patterns, distill_skill, package_zip,
    parse_skill, generate_with_skill, run_full,
    format_for_repo, quality_check, submit_to_repo,
)


def main():
    p = argparse.ArgumentParser(description="Persona distillation toolbox")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="search a persona's footprint")
    s.add_argument("--company", required=True)
    s.add_argument("--person", default=None)

    d = sub.add_parser("distill", help="search + distill into SKILL.md")
    d.add_argument("--company", required=True)
    d.add_argument("--person", default=None)
    d.add_argument("--out", default=None, help="write SKILL.md to this path (otherwise stdout)")
    d.add_argument("--zip", default=None, help="also write a .zip bundle to this path")

    f = sub.add_parser("full", help="full pipeline (search + distill, JSON dump)")
    f.add_argument("--company", required=True)
    f.add_argument("--person", default=None)

    u = sub.add_parser("use", help="use a SKILL.md file to advise / rewrite / critique input")
    u.add_argument("--skill", required=True, help="path to SKILL.md")
    u.add_argument("--input", required=True)
    u.add_argument("--mode", default="advise", choices=["advise", "rewrite", "critique"])

    pa = sub.add_parser("parse", help="parse a SKILL.md and dump structure")
    pa.add_argument("--skill", required=True)

    sb = sub.add_parser("submit", help="distill + open draft PR against fxp/persona-distill-skills")
    sb.add_argument("--company", required=True)
    sb.add_argument("--person", default=None)
    sb.add_argument("--repo", default="fxp/persona-distill-skills")
    sb.add_argument("--base-branch", default="main")
    sb.add_argument("--force", action="store_true",
                    help="bypass quality gate (PR is still draft, you review)")
    sb.add_argument("--dry-run", action="store_true",
                    help="format-for-repo + quality-check, but do not submit")

    args = p.parse_args()

    if args.cmd == "search":
        print(json.dumps(search_persona(args.company, args.person), ensure_ascii=False, indent=2))
    elif args.cmd == "distill":
        sr = search_persona(args.company, args.person)
        pat = extract_patterns(sr)
        out = distill_skill(args.company, args.person, pat, search_results=sr)
        if args.out:
            pathlib.Path(args.out).write_text(out["skill_md"], encoding="utf-8")
            print(f"wrote SKILL.md → {args.out} ({len(out['skill_md'])} chars)")
        else:
            print(out["skill_md"])
        if args.zip:
            pathlib.Path(args.zip).write_bytes(package_zip(out))
            print(f"wrote zip → {args.zip}")
    elif args.cmd == "full":
        print(json.dumps(run_full(args.company, args.person), ensure_ascii=False, indent=2))
    elif args.cmd == "use":
        skill_md = pathlib.Path(args.skill).read_text(encoding="utf-8")
        result = generate_with_skill(skill_md, args.input, mode=args.mode)
        print(result["output"])
    elif args.cmd == "parse":
        skill_md = pathlib.Path(args.skill).read_text(encoding="utf-8")
        print(json.dumps(parse_skill(skill_md), ensure_ascii=False, indent=2))

    elif args.cmd == "submit":
        import os, subprocess
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            try:
                token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
                print("[info] using token from `gh auth token`", file=sys.stderr)
            except Exception:
                print("ERROR: GITHUB_TOKEN not set and `gh auth token` failed.\n"
                      "  Either export GITHUB_TOKEN=<pat> or run `gh auth login`.", file=sys.stderr)
                sys.exit(2)
        sr = search_persona(args.company, args.person)
        pat = extract_patterns(sr)
        bundle = format_for_repo(args.company, args.person, pat, search_results=sr)
        qc = quality_check(bundle, pat)
        print(f"[quality] score={qc['score']}/100  passed={qc['passed']}", file=sys.stderr)
        for issue in qc["issues"]:
            print(f"[quality]   • {issue}", file=sys.stderr)
        if args.dry_run:
            print(json.dumps({"bundle_meta": bundle["meta"], "quality": qc},
                             ensure_ascii=False, indent=2))
            return
        if not qc["passed"] and not args.force:
            print("ERROR: quality gate failed; pass --force to submit anyway (still draft PR).",
                  file=sys.stderr)
            sys.exit(3)
        result = submit_to_repo(bundle, token, repo=args.repo, base_branch=args.base_branch)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\n✓ Draft PR: {result['pr_url']}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())

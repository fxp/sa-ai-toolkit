#!/usr/bin/env bash
# Distill a persona and open a draft PR against fxp/persona-distill-skills.
# Uses local `gh auth token` if GITHUB_TOKEN is not set.
#
# Usage:
#   ./scripts/submit-skill.sh "Company"
#   ./scripts/submit-skill.sh "Company" "Person"
#   GITHUB_TOKEN=xxx ./scripts/submit-skill.sh "Company" "Person" --force
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <company> [person] [--force] [--dry-run]"
  exit 1
fi

COMPANY="$1"; shift
PERSON=""
EXTRA=()
if [[ $# -gt 0 && ! "$1" == --* ]]; then
  PERSON="$1"; shift
fi
EXTRA=("$@")

ARGS=(--company "$COMPANY")
[[ -n "$PERSON" ]] && ARGS+=(--person "$PERSON")
ARGS+=("${EXTRA[@]}")

cd demos/persona-distill-py
exec python3 cli.py submit "${ARGS[@]}"

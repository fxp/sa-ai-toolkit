#!/usr/bin/env bash
# Batch-run every demo's CLI with a sample invocation and report pass/fail.
#
# Usage:
#   ./scripts/batch_test.sh              # Show the list of demos.
#   ./scripts/batch_test.sh <demo-name>  # Run just that demo (e.g. autoresearch-py).
#   ./scripts/batch_test.sh --all        # Run every demo and print a summary.
#
# A demo passes if its CLI exits 0 and its stdout contains the expected token.
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMOS_DIR="$REPO_ROOT/demos"
PY="${PYTHON:-python3}"

# demo-name | invocation (inside the demo dir) | grep-for token
DEMOS=(
  "autoresearch-py   | cli.py list                                  | Literature search"
  "org-uplift-py     | cli.py scenarios                              | newco"
  "industrial-ai-py  | cli.py detect                                 | SAM3"
  "playwright-py     | cli.py simulate --scenario bing               | code_line"
  "ceo-agent-py      | cli.py --help                                 | usage"
  "enterprise-gen-py | cli.py --help                                 | usage"
  "gstack-py         | cli.py --help                                 | usage"
  "hypothesis-py     | cli.py --help                                 | usage"
  "karpathy-kb-py    | cli.py --help                                 | usage"
  "maestro-py        | cli.py --help                                 | usage"
  "ppt-gen-py        | cli.py --help                                 | usage"
  "sa-toolkit-py     | cli.py --help                                 | usage"
)

list_demos() {
  echo "Available demos:"
  for entry in "${DEMOS[@]}"; do
    name=$(echo "$entry" | cut -d'|' -f1 | xargs)
    echo "  - $name"
  done
  echo ""
  echo "Usage:"
  echo "  $0 <demo-name>   # run one"
  echo "  $0 --all         # run everything"
}

run_one() {
  local name="$1" invocation="$2" token="$3"
  local dir="$DEMOS_DIR/$name"
  if [ ! -d "$dir" ]; then
    echo "  [SKIP] $name (dir missing)"
    return 2
  fi
  echo "  [RUN ] $name  →  $PY $invocation"
  out=$(cd "$dir" && $PY $invocation 2>&1)
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "  [FAIL] $name  exit=$rc"
    echo "$out" | sed 's/^/        /' | head -8
    return 1
  fi
  if ! echo "$out" | grep -qi -- "$token"; then
    echo "  [FAIL] $name  (stdout missing token: '$token')"
    echo "$out" | sed 's/^/        /' | head -8
    return 1
  fi
  echo "  [ OK ] $name"
  return 0
}

run_all() {
  local pass=0 fail=0 total=0
  for entry in "${DEMOS[@]}"; do
    name=$(echo "$entry" | cut -d'|' -f1 | xargs)
    inv=$(echo  "$entry" | cut -d'|' -f2 | xargs)
    tok=$(echo  "$entry" | cut -d'|' -f3 | xargs)
    total=$((total+1))
    if run_one "$name" "$inv" "$tok"; then pass=$((pass+1)); else fail=$((fail+1)); fi
  done
  echo ""
  echo "  Summary: $pass / $total passed, $fail failed"
  [ $fail -eq 0 ]
}

run_named() {
  local want="$1"
  for entry in "${DEMOS[@]}"; do
    name=$(echo "$entry" | cut -d'|' -f1 | xargs)
    if [ "$name" = "$want" ]; then
      inv=$(echo "$entry" | cut -d'|' -f2 | xargs)
      tok=$(echo "$entry" | cut -d'|' -f3 | xargs)
      run_one "$name" "$inv" "$tok"
      return $?
    fi
  done
  echo "No such demo: $want"
  list_demos
  return 2
}

case "${1:-}" in
  "")       list_demos ;;
  --all)    run_all ;;
  -h|--help) list_demos ;;
  *)        run_named "$1" ;;
esac

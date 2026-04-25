#!/usr/bin/env bash
# Usage: ./scripts/deploy-demo.sh [<demo-name>|--all]
# Deploys one (or all) per-demo Fly.io app(s) using the shared Dockerfile.demo.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

DEMOS=(
  industrial-ai ceo-agent autoresearch autoresearch-vrp enterprise-gen gstack
  hypothesis karpathy-kb maestro org-uplift playwright ppt-gen sa-toolkit
  persona-distill
)

deploy_one() {
  local name="$1"
  local app="sa-${name}"
  local cfg="${ROOT}/demos/${name}-py/fly.toml"

  if [[ ! -f "$cfg" ]]; then
    echo "[skip] $name — no fly.toml at $cfg"
    return 0
  fi
  echo "=== $app (demos/${name}-py) ==="

  # Create app if missing
  if ! flyctl apps list 2>/dev/null | awk '{print $1}' | grep -qx "$app"; then
    flyctl apps create "$app" --org personal || true
  fi

  # Deploy (without HTTP proxy; avoid depot — depot endpoint blocked in some regions)
  env -u HTTP_PROXY -u HTTPS_PROXY flyctl deploy \
    --app "$app" \
    --config "$cfg" \
    --dockerfile "$ROOT/Dockerfile.demo" \
    --build-arg DEMO_NAME="$name" \
    --remote-only \
    --depot=false \
    --wait-timeout 600
}

if [[ "${1:-}" == "--all" ]]; then
  for d in "${DEMOS[@]}"; do
    deploy_one "$d" || echo "[FAIL] $d"
  done
elif [[ -n "${1:-}" ]]; then
  deploy_one "$1"
else
  echo "Usage: $0 <demo-name>|--all"
  echo "Known demos:"
  printf '  %s\n' "${DEMOS[@]}"
  exit 1
fi

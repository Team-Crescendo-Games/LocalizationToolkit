#!/usr/bin/env bash
# Launch the ink dialogue validator SPA. Installs deps if needed.
set -euo pipefail

cd "$(dirname "$0")/../ink-app"

if ! command -v node >/dev/null 2>&1; then
  echo "error: node not found on PATH. Install Node 18+." >&2
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

exec npm run dev -- "$@"

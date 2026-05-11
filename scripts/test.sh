#!/usr/bin/env bash
# Run the pytest suite inside the project venv.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x ".venv/bin/pytest" ]; then
  echo "pytest not installed; running setup..."
  ./scripts/setup.sh
fi

exec .venv/bin/pytest "$@"

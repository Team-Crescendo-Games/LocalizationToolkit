#!/usr/bin/env bash
# Launch the Streamlit UI. Runs setup.sh if the venv is missing.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x ".venv/bin/streamlit" ]; then
  echo "Streamlit not installed; running setup..."
  ./scripts/setup.sh
fi

exec .venv/bin/streamlit run app.py "$@"

#!/usr/bin/env bash
# Create a virtualenv and install the toolkit (with UI + dev extras).
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3.11}"
VENV_DIR=".venv"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "error: $PYTHON not found on PATH. Install Python 3.11+ or set PYTHON=..." >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv at $VENV_DIR using $PYTHON..."
  "$PYTHON" -m venv "$VENV_DIR"
else
  echo "Reusing existing virtualenv at $VENV_DIR."
fi

"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -e ".[dev,ui]"

echo
echo "Done. Next steps:"
echo "  ./scripts/run-ui.sh             # launch the Streamlit UI"
echo "  ./scripts/test.sh               # run the test suite"
echo "  source .venv/bin/activate       # to use locvalidate / loc2csv directly"

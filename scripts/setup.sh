#!/usr/bin/env bash
# Set up both the Python toolkit and the ink-app SPA.
#
# Skip flags:
#   SKIP_PYTHON=1   skip Python venv + pip install
#   SKIP_NODE=1     skip ink-app npm install
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3.11}"
VENV_DIR=".venv"
INK_APP_DIR="ink-app"

# ---------- Python toolkit ----------
if [ "${SKIP_PYTHON:-0}" = "1" ]; then
  echo "Skipping Python setup (SKIP_PYTHON=1)."
else
  if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "error: $PYTHON not found on PATH. Install Python 3.11+ or set PYTHON=..." >&2
    exit 1
  fi

  if [ ! -d "$VENV_DIR" ]; then
    echo "[python] creating virtualenv at $VENV_DIR using $PYTHON..."
    "$PYTHON" -m venv "$VENV_DIR"
  else
    echo "[python] reusing existing virtualenv at $VENV_DIR."
  fi

  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install -e ".[dev,ui]"
fi

# ---------- ink-app SPA ----------
if [ "${SKIP_NODE:-0}" = "1" ]; then
  echo "Skipping ink-app setup (SKIP_NODE=1)."
elif [ ! -d "$INK_APP_DIR" ]; then
  echo "[ink-app] directory not found at $INK_APP_DIR; skipping."
elif ! command -v node >/dev/null 2>&1; then
  echo "warning: node not found on PATH; skipping ink-app install. Install Node 18+ to use it." >&2
elif ! command -v npm >/dev/null 2>&1; then
  echo "warning: npm not found on PATH; skipping ink-app install." >&2
else
  if [ ! -d "$INK_APP_DIR/node_modules" ]; then
    echo "[ink-app] installing npm dependencies..."
  else
    echo "[ink-app] node_modules present; running npm install to sync..."
  fi
  (cd "$INK_APP_DIR" && npm install)
fi

echo
echo "Done. Next steps:"
echo "  ./scripts/run-json.sh           # launch the Streamlit localization UI"
echo "  ./scripts/run-ink.sh            # launch the ink dialogue validator SPA"
echo "  source .venv/bin/activate       # to use locvalidate / loc2csv directly"

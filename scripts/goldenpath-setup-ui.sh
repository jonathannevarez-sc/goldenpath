#!/usr/bin/env bash
# Launcher for the Golden Path Streamlit Setup UI (web mirror of the wizard).
# Usage: ./scripts/goldenpath-setup-ui.sh
# Auto-creates a virtualenv under scripts/setup/.venv if needed.
# Docs: docs/getting-started/09-streamlit-setup-ui.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_DIR="${SCRIPT_DIR}/setup"
APP="${SETUP_DIR}/goldenpath_setup_app.py"
VENV_DIR="${SETUP_DIR}/.venv"
REQUIREMENTS="${SETUP_DIR}/requirements.txt"

# Resolve the Python binary: prefer python3, fall back to python
PYTHON_BIN="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "error: Python 3 is required but was not found on PATH." >&2
  echo "Install it from https://python.org, then re-run this script." >&2
  exit 1
fi

# Ensure the virtualenv exists
if [[ ! -x "${VENV_DIR}/bin/python" && ! -x "${VENV_DIR}/Scripts/python.exe" ]]; then
  echo "==> Creating virtualenv at ${VENV_DIR}"
  "$PYTHON_BIN" -m venv "${VENV_DIR}"
fi

# Resolve venv python/pip (handles both Unix and Windows Git Bash paths)
if [[ -x "${VENV_DIR}/bin/python" ]]; then
  VENV_PYTHON="${VENV_DIR}/bin/python"
  VENV_PIP="${VENV_DIR}/bin/pip"
  VENV_STREAMLIT="${VENV_DIR}/bin/streamlit"
else
  VENV_PYTHON="${VENV_DIR}/Scripts/python.exe"
  VENV_PIP="${VENV_DIR}/Scripts/pip.exe"
  VENV_STREAMLIT="${VENV_DIR}/Scripts/streamlit.exe"
fi

# Install / sync dependencies
if [[ -f "$REQUIREMENTS" ]]; then
  echo "==> Installing dependencies from $(basename "$REQUIREMENTS")"
  "$VENV_PIP" install -q -r "$REQUIREMENTS"
else
  echo "==> Installing streamlit (no requirements.txt found)"
  "$VENV_PIP" install -q streamlit
fi

# Final guard: confirm streamlit is available
if [[ ! -x "$VENV_STREAMLIT" ]]; then
  echo "error: streamlit was not installed successfully. Check the output above." >&2
  exit 1
fi

echo "==> Starting Golden Path Setup UI at http://localhost:8501"
cd "${SETUP_DIR}"
exec "$VENV_STREAMLIT" run "$(basename "${APP}")" "$@"

#!/usr/bin/env bash
# Launcher for the Golden Path Streamlit Setup UI (web mirror of the wizard).
# Usage: ./scripts/goldenpath-setup-ui.sh
# Requires: pip install streamlit
# Docs: docs/getting-started/09-streamlit-setup-ui.md (menu reference: 07-setup-wizard-usage.md)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${SCRIPT_DIR}/setup/goldenpath_setup_app.py"

if ! command -v streamlit >/dev/null 2>&1; then
  cat <<'EOF'
Golden Path Setup UI requires Streamlit.

  pip install streamlit

Then run:
  ./scripts/goldenpath-setup-ui.sh
  streamlit run scripts/setup/goldenpath_setup_app.py

Full guide: docs/getting-started/07-setup-wizard-usage.md
EOF
  exit 1
fi

APP_DIR="$(dirname "${APP}")"
cd "${APP_DIR}"
exec streamlit run "$(basename "${APP}")" "$@"

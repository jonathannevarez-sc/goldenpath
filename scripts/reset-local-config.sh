#!/usr/bin/env bash
# Reset local Golden Path wizard config (WIF cache, session JSON, optional tfvars).
#
# Usage (from repo root):
#   ./scripts/reset-local-config.sh              # full wizard reset (menu 14 equivalent)
#   ./scripts/reset-local-config.sh --wif-only   # clear cached WIF only (fastest WIF fix)
#   ./scripts/reset-local-config.sh --all -y     # wizard + tfvars + clear sandbox in enterprise.env
#   ./scripts/reset-local-config.sh --dry-run
#
# Does NOT delete GCP projects — use ./scripts/teardown-personal-test.sh for that.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

exec python3 "${SCRIPT_DIR}/lib/reset_local_config.py" "$@"
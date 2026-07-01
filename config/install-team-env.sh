#!/usr/bin/env bash
# Copy platform team canonical config to the path all tools read.
# Usage (from repo root): ./config/install-team-env.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEAM="${REPO_ROOT}/config/enterprise.env.team"
TARGET="${REPO_ROOT}/config/enterprise.env"

if [[ ! -f "${TEAM}" ]]; then
  printf 'error: missing %s\n' "${TEAM}" >&2
  printf '  Platform team: cp config/enterprise.env.team.example config/enterprise.env.team\n' >&2
  printf '  Then fill billing, projects, and GitHub org (FinOps + platform).\n' >&2
  exit 1
fi

cp "${TEAM}" "${TARGET}"
printf 'Installed %s → %s\n' "${TEAM}" "${TARGET}"
printf 'Next: gcloud auth login && gcloud auth application-default login && gh auth login\n'
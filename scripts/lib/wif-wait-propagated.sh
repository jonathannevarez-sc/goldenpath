#!/usr/bin/env bash
# Wait for per-repo WIF IAM bindings to propagate before triggering GitHub Actions.
# Run after wif-trust-repo.sh. Exits 0 when bindings are stable; times out gracefully.
#
# Usage: wif-wait-propagated.sh <gcp-project> <github-org> <repo-name> [max-seconds]
set -euo pipefail

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
log() { printf '==> %s\n' "$*"; }

[[ $# -ge 3 ]] || die "usage: wif-wait-propagated.sh <gcp-project> <github-org> <repo-name> [max-seconds]"

PROJECT="$1"
ORG="$2"
REPO="$3"
MAX_WAIT="${4:-75}"
SA="github-actions@${PROJECT}.iam.gserviceaccount.com"

PROJECT_NUMBER="$(gcloud projects describe "${PROJECT}" --format='value(projectNumber)' 2>/dev/null)" \
  || die "cannot describe project ${PROJECT}"
POOL_NAME="$(gcloud iam workload-identity-pools list \
  --project="${PROJECT}" --location=global --format='value(name)' 2>/dev/null | head -1)" \
  || true
[[ -n "${POOL_NAME}" ]] || die "no workload identity pool in ${PROJECT}"

POOL_ID="${POOL_NAME##*/}"
MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${ORG}/${REPO}"

bindings_ready() {
  local policy
  policy="$(gcloud iam service-accounts get-iam-policy "${SA}" \
    --project="${PROJECT}" --format=json 2>/dev/null || true)"
  [[ -n "$policy" ]] || return 1
  python3 - "$policy" "$MEMBER" <<'PY'
import json, sys
policy, member = sys.argv[1], sys.argv[2]
try:
    data = json.loads(policy)
except json.JSONDecodeError:
    raise SystemExit(1)
roles = {b.get("role") for b in data.get("bindings", []) if member in b.get("members", [])}
needed = {"roles/iam.workloadIdentityUser", "roles/iam.serviceAccountTokenCreator"}
raise SystemExit(0 if needed.issubset(roles) else 1)
PY
}

deadline=$((SECONDS + MAX_WAIT))
stable_reads=0

while [[ $SECONDS -lt $deadline ]]; do
  if bindings_ready; then
    stable_reads=$((stable_reads + 1))
    if [[ $stable_reads -ge 2 ]]; then
      log "WIF bindings stable for ${ORG}/${REPO} — waiting 20s for GCP propagation"
      sleep 20
      log "WIF ready for ${ORG}/${REPO}"
      exit 0
    fi
  else
    stable_reads=0
  fi
  sleep 5
done

log "WIF bindings present but propagation window elapsed — continuing (${MAX_WAIT}s)"
sleep 15
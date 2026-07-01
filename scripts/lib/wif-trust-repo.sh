#!/usr/bin/env bash
# Grant a GitHub service repo explicit WIF bindings (required for AR docker login).
# Usage: wif-trust-repo.sh <gcp-project> <github-org> <repo-name>
set -euo pipefail

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
log() { printf '==> %s\n' "$*"; }

[[ $# -eq 3 ]] || die "usage: wif-trust-repo.sh <gcp-project> <github-org> <repo-name>"

PROJECT="$1"
ORG="$2"
REPO="$3"
SA="github-actions@${PROJECT}.iam.gserviceaccount.com"

PROJECT_NUMBER="$(gcloud projects describe "${PROJECT}" --format='value(projectNumber)' 2>/dev/null)" \
  || die "cannot describe project ${PROJECT}"
POOL_NAME="$(gcloud iam workload-identity-pools list \
  --project="${PROJECT}" --location=global --format='value(name)' 2>/dev/null | head -1)" \
  || true
[[ -n "${POOL_NAME}" ]] || die "no workload identity pool in ${PROJECT}"

POOL_ID="${POOL_NAME##*/}"
MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${ORG}/${REPO}"

has_binding() {
  local role="$1"
  gcloud iam service-accounts get-iam-policy "${SA}" --project="${PROJECT}" --format=json \
    | python3 -c "import json,sys; m,r=sys.argv[1],sys.argv[2]; d=json.load(sys.stdin); print(any(b.get('role')==r and m in b.get('members',[]) for b in d.get('bindings',[])))" \
      "${MEMBER}" "${role}" 2>/dev/null | grep -q True
}

bind_with_retry() {
  local role="$1"
  if has_binding "${role}"; then
    log "already bound ${role} for ${ORG}/${REPO}"
    return 0
  fi
  log "binding ${role} for ${ORG}/${REPO}"
  local attempt out
  for attempt in 1 2 3 4 5; do
    if out="$(gcloud iam service-accounts add-iam-policy-binding "${SA}" \
      --project="${PROJECT}" \
      --role="${role}" \
      --member="${MEMBER}" \
      --quiet 2>&1)"; then
      return 0
    fi
    if echo "${out}" | grep -qiE 'concurrent policy|ABORTED|etag|resource version'; then
      log "IAM policy race on attempt ${attempt} — retrying in $((attempt * 3))s ..."
      sleep $((attempt * 3))
      continue
    fi
    printf '%s\n' "${out}" >&2
    return 1
  done
  die "WIF binding failed for ${role} after retries (concurrent IAM updates)"
}

for ROLE in roles/iam.workloadIdentityUser roles/iam.serviceAccountTokenCreator; do
  bind_with_retry "${ROLE}"
done

WAIT_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/wif-wait-propagated.sh"
if [[ -x "${WAIT_SCRIPT}" ]]; then
  "${WAIT_SCRIPT}" "${PROJECT}" "${ORG}" "${REPO}"
else
  log "waiting 45s for WIF IAM propagation ..."
  sleep 45
fi

log "WIF trust ready for ${ORG}/${REPO}"
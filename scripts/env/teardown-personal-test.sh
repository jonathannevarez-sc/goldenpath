#!/usr/bin/env bash
# Destroy Golden Path personal test resources without touching other GCP projects.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BOOTSTRAP_DIR="${REPO_ROOT}/platform/bootstrap"
# shellcheck source=../lib/teardown-safety.sh
source "${SCRIPT_DIR}/../lib/teardown-safety.sh"
teardown_load_profile "${REPO_ROOT}"

usage() {
  cat <<'EOF'
Usage: teardown-personal-test.sh [options]

Destroys Golden Path bootstrap resources in your TEST project only.
Does NOT delete the GCP project unless you pass --delete-project.

Options:
  --service-dir <path>   Also run terraform destroy in a scaffolded service infra/
  --delete-project <id>  Delete entire GCP project after destroy (irreversible)
  --yes                  Skip confirmation prompts
  -h, --help             Show help

Prerequisites:
  - terraform.tfvars with personal_test = true in platform/bootstrap
  - gcloud authenticated

Example:
  ./scripts/teardown-personal-test.sh --service-dir ../my-service
  ./scripts/teardown-personal-test.sh --delete-project goldenpath-test-abc --yes
EOF
}

log() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

SERVICE_DIR=""
DELETE_PROJECT=""
ASSUME_YES="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service-dir) SERVICE_DIR="$2"; shift 2 ;;
    --delete-project) DELETE_PROJECT="$2"; shift 2 ;;
    --yes) ASSUME_YES="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

if [[ ! -f "${BOOTSTRAP_DIR}/terraform.tfvars" ]]; then
  die "missing ${BOOTSTRAP_DIR}/terraform.tfvars — run bootstrap first"
fi

if ! grep -q 'personal_test[[:space:]]*=[[:space:]]*true' "${BOOTSTRAP_DIR}/terraform.tfvars"; then
  die "terraform.tfvars must have personal_test = true (safety check)"
fi

PROJECT_ID="$(grep 'test_project_id' "${BOOTSTRAP_DIR}/terraform.tfvars" | head -1 | sed 's/.*= *"\([^"]*\)".*/\1/')"
[[ -n "${PROJECT_ID}" ]] || die "could not read test_project_id from terraform.tfvars"

if [[ "${ASSUME_YES}" != "true" ]]; then
  echo "This will destroy Golden Path resources in project: ${PROJECT_ID}"
  echo "Other GCP projects are NOT affected."
  read -r -p "Continue? [y/N] " ans
  [[ "${ans}" =~ ^[Yy]$ ]] || exit 0
fi

if [[ -n "${SERVICE_DIR}" ]]; then
  log "destroying service infra in ${SERVICE_DIR}/infra"
  (cd "${SERVICE_DIR}/infra" && terraform init -input=false && terraform destroy -auto-approve -var-file=dev.tfvars)
fi

log "destroying platform bootstrap in ${BOOTSTRAP_DIR}"
(cd "${BOOTSTRAP_DIR}" && terraform init -input=false && terraform destroy -auto-approve)

if [[ -n "${DELETE_PROJECT}" ]]; then
  if [[ "${DELETE_PROJECT}" != "${PROJECT_ID}" ]]; then
    die "--delete-project (${DELETE_PROJECT}) must match test_project_id (${PROJECT_ID})"
  fi
  teardown_assert_deletable_project "${PROJECT_ID}"
  if [[ "${ASSUME_YES}" != "true" ]]; then
    read -r -p "DELETE entire project ${PROJECT_ID}? [y/N] " ans
    [[ "${ans}" =~ ^[Yy]$ ]] || exit 0
  fi
  log "deleting GCP project ${PROJECT_ID} (protected projects like YOUR_BILLING_ANCHOR_PROJECT are never touched)"
  gcloud projects delete "${PROJECT_ID}" --quiet
fi

log "done — billing for this test project should stop (except any orphaned buckets you created manually)"
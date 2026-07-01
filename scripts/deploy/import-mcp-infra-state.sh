#!/usr/bin/env bash
# One-time: import existing goldenpath-mcp-dev resources into mcp/infra remote state.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INFRA="${ROOT}/mcp/infra"
# shellcheck source=../lib/load-config.sh
source "${ROOT}/scripts/lib/load-config.sh"
load_goldenpath_config "${ROOT}" 2>/dev/null || true

PROJECT="${GCP_PROJECT:-${GCP_DEV_PROJECT:-${GCP_SANDBOX_PROJECT:-}}}"
[[ -n "${PROJECT}" ]] || { echo "error: set GCP_PROJECT or configure config/enterprise.env" >&2; exit 1; }

REGION="${GCP_REGION:-}"
MCP_BASE="${MCP_SERVICE_NAME:-}"
[[ -n "${REGION}" ]] || REGION="$(python3 "${ROOT}/scripts/lib/wizard_defaults.py" --platform-default GCP_REGION)"
[[ -n "${MCP_BASE}" ]] || MCP_BASE="$(python3 "${ROOT}/scripts/lib/wizard_defaults.py" --platform-default MCP_SERVICE_NAME)"
AR_REPO="${ARTIFACT_REGISTRY_REPO:-}"
[[ -n "${AR_REPO}" ]] || AR_REPO="$(python3 "${ROOT}/scripts/lib/wizard_defaults.py" --platform-default ARTIFACT_REGISTRY_REPO)"
SERVICE="${MCP_BASE}-dev"
SA="${SERVICE}-run@${PROJECT}.iam.gserviceaccount.com"
SECRET="${SERVICE}-mcp-api-key"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "$ROOT" rev-parse HEAD)}"

log() { printf '==> %s\n' "$*"; }

cd "${INFRA}"
terraform init -input=false

import_if_missing() {
  local addr="$1"
  local id="$2"
  if terraform state show -no-color "${addr}" >/dev/null 2>&1; then
    log "skip (in state): ${addr}"
  else
    log "import: ${addr}"
    terraform import -var-file=dev.tfvars -var="project_id=${PROJECT}" -var="image_tag=${IMAGE_TAG}" "${addr}" "${id}"
  fi
}

import_if_missing 'module.secrets.google_secret_manager_secret.secrets["mcp-api-key"]' \
  "projects/${PROJECT}/secrets/${SECRET}"

import_if_missing 'module.secrets.google_secret_manager_secret_version.bootstrap["mcp-api-key"]' \
  "projects/${PROJECT}/secrets/${SECRET}/versions/1"

import_if_missing 'module.identity.google_service_account.runtime' \
  "projects/${PROJECT}/serviceAccounts/${SA}"

import_if_missing 'module.secrets.google_secret_manager_secret_iam_member.accessor["mcp-api-key-serviceAccount:${SA}"]' \
  "projects/${PROJECT}/secrets/${SECRET} roles/secretmanager.secretAccessor serviceAccount:${SA}"

import_if_missing 'google_project_iam_member.mcp_run_viewer' \
  "${PROJECT} roles/run.viewer serviceAccount:${SA}"

import_if_missing 'module.cloud_run.google_cloud_run_v2_service.service' \
  "projects/${PROJECT}/locations/${REGION}/services/${SERVICE}"

import_if_missing 'module.cloud_run.google_artifact_registry_repository_iam_member.runtime_reader' \
  "projects/${PROJECT}/locations/${REGION}/repositories/${AR_REPO} roles/artifactregistry.reader serviceAccount:${SA}"

import_if_missing 'module.cloud_run.google_cloud_run_v2_service_iam_member.public_invoker[0]' \
  "projects/${PROJECT}/locations/${REGION}/services/${SERVICE} roles/run.invoker allUsers"

DASHBOARD_ID="$(gcloud monitoring dashboards list --project="${PROJECT}" \
  --filter="displayName='${SERVICE} dev — Golden Path'" --format='value(name)' | head -1)"
if [[ -n "${DASHBOARD_ID}" ]]; then
  import_if_missing 'module.observability.google_monitoring_dashboard.service' "${DASHBOARD_ID}"
fi

POLICY_ID="$(gcloud monitoring policies list --project="${PROJECT}" \
  --filter="displayName='${SERVICE} dev — high 5xx rate'" --format='value(name)' | head -1)"
if [[ -n "${POLICY_ID}" ]]; then
  import_if_missing 'module.observability.google_monitoring_alert_policy.high_error_rate' "${POLICY_ID}"
fi

log "apply to reconcile state"
terraform apply -input=false -auto-approve -var-file=dev.tfvars -var="project_id=${PROJECT}" -var="image_tag=${IMAGE_TAG}"

log "done — MCP infra state reconciled for project ${PROJECT}"
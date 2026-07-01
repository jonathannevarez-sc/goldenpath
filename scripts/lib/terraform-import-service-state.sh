#!/usr/bin/env bash
# Import pre-existing Golden Path service infra into ephemeral CI/local Terraform state.
# Handles partial applies (409 already exists on retry) when remote state is not configured.
#
# Usage:
#   terraform-import-service-state.sh <infra-dir> <environment> \
#     [--service-name NAME] [--project ID] [--region REGION] [--ar-repo REPO] [--image-tag TAG]
#
# Environment variables (override flags): TF_VAR_service_name, TF_VAR_environment,
# TF_VAR_project_id, TF_VAR_region, TF_VAR_artifact_registry_repo, TF_VAR_image_tag
set -euo pipefail

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
log() { printf '==> %s\n' "$*"; }

[[ $# -ge 2 ]] || die "usage: terraform-import-service-state.sh <infra-dir> <environment> [options]"

INFRA_DIR="$1"
ENVIRONMENT="$2"
shift 2

SERVICE_NAME="${TF_VAR_service_name:-}"
PROJECT_ID="${TF_VAR_project_id:-}"
REGION="${TF_VAR_region:-}"
AR_REPO="${TF_VAR_artifact_registry_repo:-}"
IMAGE_TAG="${TF_VAR_image_tag:-bootstrap}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service-name) SERVICE_NAME="$2"; shift 2 ;;
    --project) PROJECT_ID="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --ar-repo) AR_REPO="$2"; shift 2 ;;
    --image-tag) IMAGE_TAG="$2"; shift 2 ;;
    *) die "unknown option: $1" ;;
  esac
done

[[ -d "$INFRA_DIR" ]] || die "infra dir not found: $INFRA_DIR"

read_tfvar() {
  local key="$1"
  local file="$INFRA_DIR/${ENVIRONMENT}.tfvars"
  [[ -f "$file" ]] || return 0
  python3 - "$file" "$key" <<'PY'
import re, sys
path, key = sys.argv[1], sys.argv[2]
text = open(path).read()
m = re.search(rf'^\s*{re.escape(key)}\s*=\s*"([^"]+)"', text, re.M)
if m:
    print(m.group(1))
PY
}

[[ -n "$SERVICE_NAME" ]] || SERVICE_NAME="$(read_tfvar service_name)"
[[ -n "$PROJECT_ID" ]] || PROJECT_ID="$(read_tfvar project_id)"
[[ -n "$REGION" ]] || REGION="$(read_tfvar region)"
[[ -n "$AR_REPO" ]] || AR_REPO="$(read_tfvar artifact_registry_repo)"

[[ -n "$SERVICE_NAME" && -n "$PROJECT_ID" && -n "$REGION" && -n "$AR_REPO" ]] \
  || die "missing service_name/project_id/region/artifact_registry_repo (set TF_VAR_* or tfvars)"

runtime_account_id() {
  python3 - "$SERVICE_NAME" "$ENVIRONMENT" <<'PY'
import sys
sn, env = sys.argv[1], sys.argv[2]
print((f"{sn}-{env}-run").replace("_", "-")[:30])
PY
}

ACCOUNT_ID="$(runtime_account_id)"
SA_EMAIL="${ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
SECRET_ID="${SERVICE_NAME}-${ENVIRONMENT}-app-config"
CLOUD_RUN="${SERVICE_NAME}-${ENVIRONMENT}"
MEMBER="serviceAccount:${SA_EMAIL}"
ACCESSOR_KEY="app-config-${MEMBER}"

tf_import_args=(
  -input=false
  -var-file="${ENVIRONMENT}.tfvars"
  -var="project_id=${PROJECT_ID}"
  -var="service_name=${SERVICE_NAME}"
  -var="environment=${ENVIRONMENT}"
  -var="region=${REGION}"
  -var="artifact_registry_repo=${AR_REPO}"
  -var="image_tag=${IMAGE_TAG}"
)

gcp_exists() {
  eval "$1" >/dev/null 2>&1
}

import_if_missing() {
  local addr="$1"
  local id="$2"
  local check_cmd="$3"

  if terraform state show -no-color "${addr}" >/dev/null 2>&1; then
    log "skip (in state): ${addr}"
    return 0
  fi
  if ! gcp_exists "${check_cmd}"; then
    log "skip (not in GCP): ${addr}"
    return 0
  fi
  log "import: ${addr}"
  terraform import "${tf_import_args[@]}" "${addr}" "${id}"
}

cd "${INFRA_DIR}"

import_if_missing 'module.identity.google_service_account.runtime' \
  "projects/${PROJECT_ID}/serviceAccounts/${SA_EMAIL}" \
  "gcloud iam service-accounts describe '${SA_EMAIL}' --project='${PROJECT_ID}'"

import_if_missing 'module.secrets.google_secret_manager_secret.secrets["app-config"]' \
  "projects/${PROJECT_ID}/secrets/${SECRET_ID}" \
  "gcloud secrets describe '${SECRET_ID}' --project='${PROJECT_ID}'"

import_if_missing 'module.secrets.google_secret_manager_secret_version.bootstrap["app-config"]' \
  "projects/${PROJECT_ID}/secrets/${SECRET_ID}/versions/1" \
  "gcloud secrets versions describe 1 --secret='${SECRET_ID}' --project='${PROJECT_ID}'"

if gcloud secrets describe "${SECRET_ID}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  import_if_missing "module.secrets.google_secret_manager_secret_iam_member.accessor[\"${ACCESSOR_KEY}\"]" \
    "projects/${PROJECT_ID}/secrets/${SECRET_ID} roles/secretmanager.secretAccessor ${MEMBER}" \
    "true"
fi

import_if_missing 'module.cloud_run.google_cloud_run_v2_service.service' \
  "projects/${PROJECT_ID}/locations/${REGION}/services/${CLOUD_RUN}" \
  "gcloud run services describe '${CLOUD_RUN}' --project='${PROJECT_ID}' --region='${REGION}'"

if gcloud run services describe "${CLOUD_RUN}" --project="${PROJECT_ID}" --region="${REGION}" >/dev/null 2>&1; then
  import_if_missing 'module.cloud_run.google_artifact_registry_repository_iam_member.runtime_reader' \
    "projects/${PROJECT_ID}/locations/${REGION}/repositories/${AR_REPO} roles/artifactregistry.reader ${MEMBER}" \
    "true"
fi

if [[ "${ENVIRONMENT}" == "dev" ]] \
  && gcloud run services describe "${CLOUD_RUN}" --project="${PROJECT_ID}" --region="${REGION}" >/dev/null 2>&1; then
  import_if_missing 'module.cloud_run.google_cloud_run_v2_service_iam_member.public_invoker[0]' \
    "projects/${PROJECT_ID}/locations/${REGION}/services/${CLOUD_RUN} roles/run.invoker allUsers" \
    "true"
fi

log "import pass complete for ${SERVICE_NAME} (${ENVIRONMENT}) in ${PROJECT_ID}"
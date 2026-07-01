#!/usr/bin/env bash
# Build (Cloud Build), push to Artifact Registry, deploy MCP to Cloud Run (streamable-http + API key).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INFRA="${ROOT}/mcp/infra"
# shellcheck source=../lib/load-config.sh
source "${ROOT}/scripts/lib/load-config.sh"
load_goldenpath_config "${ROOT}" 2>/dev/null || true

GCP_PROJECT="${GCP_PROJECT:-${GCP_DEV_PROJECT:-${GCP_SANDBOX_PROJECT:-}}}"
GCP_REGION="${GCP_REGION:-}"
SERVICE_NAME="${SERVICE_NAME:-${MCP_SERVICE_NAME:-}}"
AR_REPO="${AR_REPO:-${ARTIFACT_REGISTRY_REPO:-}}"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "$ROOT" rev-parse --short HEAD)}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
PLATFORM_REPO="${PLATFORM_REPO:-}"
GITHUB_ORG="${GITHUB_ORG:-}"
GOLDENPATH_VERSION="${GOLDENPATH_VERSION:-}"

[[ -n "${GCP_REGION}" ]] || GCP_REGION="$(python3 "${ROOT}/scripts/lib/wizard_defaults.py" --platform-default GCP_REGION)"
[[ -n "${SERVICE_NAME}" ]] || SERVICE_NAME="$(python3 "${ROOT}/scripts/lib/wizard_defaults.py" --platform-default MCP_SERVICE_NAME)"
[[ -n "${AR_REPO}" ]] || AR_REPO="$(python3 "${ROOT}/scripts/lib/wizard_defaults.py" --platform-default ARTIFACT_REGISTRY_REPO)"
[[ -n "${GOLDENPATH_VERSION}" ]] || GOLDENPATH_VERSION="$(python3 "${ROOT}/scripts/lib/wizard_defaults.py" --platform-default GOLDENPATH_VERSION)"

[[ -n "${GCP_PROJECT}" ]] || { echo "error: set GCP_PROJECT or configure config/enterprise.env" >&2; exit 1; }

IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${AR_REPO}/${SERVICE_NAME}:${IMAGE_TAG}"

log() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

command -v gcloud >/dev/null || die "gcloud required"
command -v terraform >/dev/null || die "terraform required"

build_image() {
  if command -v docker >/dev/null && docker info >/dev/null 2>&1; then
    log "building locally: ${IMAGE}"
    docker build -f "${ROOT}/mcp/Dockerfile" -t "${IMAGE}" "${ROOT}"
    log "pushing to Artifact Registry"
    gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" --quiet
    docker push "${IMAGE}"
    return 0
  fi

  log "docker unavailable — trying Cloud Build → Artifact Registry"
  if gcloud builds submit "${ROOT}" \
      --project="${GCP_PROJECT}" \
      --config="${ROOT}/mcp/cloudbuild.yaml" \
      --substitutions="_IMAGE=${IMAGE}" \
      --quiet 2>/dev/null; then
    return 0
  fi

  log "Cloud Build failed — trigger GitHub Actions (docker on runner → AR)"
  command -v gh >/dev/null || die "need docker, Cloud Build, or gh CLI"
  [[ -n "${GITHUB_ORG}" ]] || die "set GITHUB_ORG in config/enterprise.env for CI fallback"
  gh workflow run deploy-mcp.yml --repo "${GITHUB_ORG}/${PLATFORM_REPO}" -f 2>/dev/null || \
    gh workflow run deploy-mcp.yml --repo "${GITHUB_ORG}/${PLATFORM_REPO}"
  log "waiting for workflow (build + push + terraform in CI)..."
  sleep 15
  RUN_ID="$(gh run list --repo "${GITHUB_ORG}/${PLATFORM_REPO}" --workflow=deploy-mcp.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
  gh run watch "$RUN_ID" --repo "${GITHUB_ORG}/${PLATFORM_REPO}" --exit-status
  log "image built in CI — re-run this script with IMAGE_TAG matching the commit SHA, or fetch outputs from mcp/infra"
  exit 0
}

build_image

log "deploying Cloud Run via Terraform (image: ${IMAGE})"
cd "${INFRA}"
terraform init -input=false

TF_VARS=(
  -var="image_tag=${IMAGE_TAG}"
  -var="project_id=${GCP_PROJECT}"
  -var="region=${GCP_REGION}"
  -var="service_name=${SERVICE_NAME}"
  -var="artifact_registry_repo=${AR_REPO}"
  -var="goldenpath_version=${GOLDENPATH_VERSION}"
)
if [[ -n "${GITHUB_TOKEN}" ]]; then
  TF_VARS+=(-var="enable_github_token=true" -var="github_token=${GITHUB_TOKEN}")
fi

terraform apply -input=false -auto-approve "${TF_VARS[@]}"

MCP_URL="$(terraform output -raw mcp_url)"
MCP_KEY="$(terraform output -raw mcp_api_key)"
HEALTH="$(terraform output -raw health_url)"

# Bootstrap secret version is "{}" — seed a real key before handing to clients.
if [[ "${MCP_KEY}" == "{}" || -z "${MCP_KEY}" ]]; then
  MCP_KEY="$(openssl rand -hex 24)"
  MCP_SECRET="${SERVICE_NAME}-dev-mcp-api-key"
  log "seeding MCP API key in Secret Manager (${MCP_SECRET})"
  printf '%s' "${MCP_KEY}" | gcloud secrets versions add "${MCP_SECRET}" \
    --project="${GCP_PROJECT}" \
    --data-file=- >/dev/null
  RUN_SERVICE="${SERVICE_NAME}-dev"
  log "rolling Cloud Run revision to mount latest secret (${RUN_SERVICE})"
  gcloud run services update "${RUN_SERVICE}" \
    --project="${GCP_PROJECT}" \
    --region="${GCP_REGION}" \
    --quiet >/dev/null
fi

log "verifying /health"
curl -fsS "${HEALTH}" | head -c 200
echo

log "=== MCP on Cloud Run (Artifact Registry) ==="
log "Image:    ${IMAGE}"
log "MCP URL:  ${MCP_URL}"
log "API key:  ${MCP_KEY}"
log ""
log "Claude: mcp/examples/claude-mcp-remote.example.json"
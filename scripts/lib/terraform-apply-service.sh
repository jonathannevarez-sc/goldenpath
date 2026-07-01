#!/usr/bin/env bash
# Robust Golden Path service Terraform apply — staged modules + import + retries.
#
# Usage:
#   terraform-apply-service.sh <infra-dir> <environment> [--image-tag TAG] [--no-import]
set -euo pipefail

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
log() { printf '==> %s\n' "$*"; }

[[ $# -ge 2 ]] || die "usage: terraform-apply-service.sh <infra-dir> <environment> [--image-tag TAG] [--no-import]"

INFRA_DIR="$1"
ENVIRONMENT="$2"
shift 2

IMAGE_TAG="${TF_VAR_image_tag:-}"
SKIP_IMPORT="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image-tag) IMAGE_TAG="$2"; shift 2 ;;
    --no-import) SKIP_IMPORT="true"; shift ;;
    *) die "unknown option: $1" ;;
  esac
done

[[ -d "$INFRA_DIR" ]] || die "infra dir not found: $INFRA_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPORT_SCRIPT="${SCRIPT_DIR}/terraform-import-service-state.sh"

cd "${INFRA_DIR}"

common_apply_args=(
  -input=false
  -auto-approve
  -var-file="${ENVIRONMENT}.tfvars"
)

[[ -n "${IMAGE_TAG}" ]] && common_apply_args+=(-var="image_tag=${IMAGE_TAG}")

run_import() {
  [[ -x "$IMPORT_SCRIPT" ]] || return 0
  local import_args=("$IMPORT_SCRIPT" "$INFRA_DIR" "$ENVIRONMENT")
  [[ -n "${IMAGE_TAG}" ]] && import_args+=(--image-tag "$IMAGE_TAG")
  TF_VAR_image_tag="${IMAGE_TAG:-bootstrap}" "${import_args[@]}" || true
}

log "terraform init"
terraform init -input=false

if [[ "$SKIP_IMPORT" != "true" ]]; then
  log "importing pre-existing GCP resources (if any)"
  run_import
fi

log "stage 1/3: runtime service account (module.identity)"
terraform apply "${common_apply_args[@]}" -target=module.identity

log "stage 2/3: secrets (module.secrets)"
terraform apply "${common_apply_args[@]}" -target=module.secrets

log "stage 3/3: full apply"
for attempt in 1 2 3; do
  terraform plan -input=false -var-file="${ENVIRONMENT}.tfvars" \
    ${IMAGE_TAG:+-var="image_tag=${IMAGE_TAG}"} -out=tfplan
  if terraform apply -input=false -auto-approve tfplan; then
    log "terraform apply succeeded"
    exit 0
  fi
  log "terraform apply attempt ${attempt} failed — re-importing and retrying in 20s..."
  run_import
  sleep 20
done

die "terraform apply failed after 3 attempts"
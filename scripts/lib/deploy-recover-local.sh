#!/usr/bin/env bash
# Local deploy recovery when GitHub Actions Terraform fails (409 / partial state).
# Imports existing GCP resources and finishes apply with the pushed image tag.
#
# Usage: deploy-recover-local.sh <service-dir> [environment] [--image-tag SHA]
set -euo pipefail

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
log() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }

[[ $# -ge 1 ]] || die "usage: deploy-recover-local.sh <service-dir> [environment] [--image-tag SHA]"

SERVICE_DIR="$(cd "$1" && pwd)"
ENVIRONMENT="${2:-dev}"
shift 2 || true
IMAGE_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image-tag) IMAGE_TAG="$2"; shift 2 ;;
    dev|prod) ENVIRONMENT="$1"; shift ;;
    *) die "unknown option: $1" ;;
  esac
done

INFRA="${SERVICE_DIR}/infra"
[[ -d "$INFRA" ]] || die "no infra/ in ${SERVICE_DIR}"

command -v gcloud >/dev/null 2>&1 || die "gcloud required"
command -v terraform >/dev/null 2>&1 || die "terraform required"

if [[ -z "$IMAGE_TAG" ]]; then
  if git -C "$SERVICE_DIR" rev-parse HEAD >/dev/null 2>&1; then
    IMAGE_TAG="$(git -C "$SERVICE_DIR" rev-parse HEAD)"
  else
    die "pass --image-tag or run from a git service repo"
  fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLY_SCRIPT="${SCRIPT_DIR}/terraform-apply-service.sh"
[[ -x "$APPLY_SCRIPT" ]] || chmod +x "$APPLY_SCRIPT"

log "recovering ${SERVICE_DIR} (${ENVIRONMENT}) image_tag=${IMAGE_TAG}"
if ! "$APPLY_SCRIPT" "$INFRA" "$ENVIRONMENT" --image-tag "$IMAGE_TAG"; then
  warn "local terraform recovery failed — check gcloud auth and infra/dev.tfvars"
  exit 1
fi

log "local recovery apply complete"
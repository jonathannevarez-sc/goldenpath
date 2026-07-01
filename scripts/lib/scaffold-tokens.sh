#!/usr/bin/env bash
# Token replacement + deploy.yml validation (shared scaffold helpers).
# Sourced by cli/shop — not executed directly.
set -euo pipefail

deploy_has_tokens() {
  local dir="$1"
  local f="$dir/.github/workflows/deploy.yml"
  [[ -f "$f" ]] && grep -qE '\{\{[A-Z_]+\}\}' "$f"
}

get_service_template_hint() {
  local dir="$1"
  python3 - "$dir" <<'PY'
import json, os, re, sys
d = sys.argv[1]
req = os.path.join(d, "requirements.txt")
if os.path.isfile(req):
    text = open(req).read()
    if re.search(r"(?m)^streamlit", text): print("streamlit"); raise SystemExit
    if re.search(r"(?m)^fastapi", text): print("fastapi"); raise SystemExit
pkg = os.path.join(d, "package.json")
if os.path.isfile(pkg):
    data = json.load(open(pkg))
    deps = set((data.get("dependencies") or {}) | (data.get("devDependencies") or {}))
    for name, key in [("nextjs", "next"), ("express", "express"), ("react-spa", "react"), ("svelte-spa", "svelte")]:
        if key in deps:
            print(name); raise SystemExit
PY
}

replace_tokens() {
  local dir="$1" service="$2" org="$3" platform_repo="$4" dev_project="$5"
  local prod_project="$6" region="$7" app_runtime="$8" health_path="$9"
  local container_port="${10}" goldenpath_version="${11}" artifact_registry_repo="${12}"

  local sed_inplace=()
  if [[ "$(uname)" == "Darwin" ]]; then sed_inplace=(-i ''); else sed_inplace=(-i); fi
  export LC_ALL=C

  local token_args=(
    -e "s/{{SERVICE_NAME}}/${service}/g"
    -e "s/{{GITHUB_ORG}}/${org}/g"
    -e "s/{{PLATFORM_REPO}}/${platform_repo}/g"
    -e "s/{{GOLDENPATH_VERSION}}/${goldenpath_version}/g"
    -e "s/{{GCP_DEV_PROJECT}}/${dev_project}/g"
    -e "s/{{GCP_PROD_PROJECT}}/${prod_project}/g"
    -e "s/{{GCP_REGION}}/${region}/g"
    -e "s/{{APP_RUNTIME}}/${app_runtime}/g"
    -e "s|{{HEALTH_CHECK_PATH}}|${health_path}|g"
    -e "s/{{CONTAINER_PORT}}/${container_port}/g"
    -e "s/{{ARTIFACT_REGISTRY_REPO}}/${artifact_registry_repo}/g"
  )

  find "$dir" -type f \
    ! -path '*/.git/*' ! -path '*/node_modules/*' ! -path '*/__pycache__/*' ! -path '*/.pytest_cache/*' \
    -print0 | while IFS= read -r -d '' file; do
    grep -aqE '\{\{[A-Z_]+\}\}' "$file" 2>/dev/null || continue
    sed "${sed_inplace[@]}" "${token_args[@]}" "$file"
  done
}

repair_tokens_if_needed() {
  local dir="$1" service="$2"
  deploy_has_tokens "$dir" || return 0
  local template
  template="$(get_service_template_hint "$dir" || true)"
  [[ -n "$template" ]] || die "deploy.yml has unreplaced {{tokens}} — re-scaffold or fix manually"
  log "repairing unreplaced template tokens ($template)"
  local app_runtime health_path container_port
  app_runtime="$(catalog_get "${template}" app_runtime)"
  health_path="$(catalog_get "${template}" health_check_path)"
  container_port="$(catalog_get "${template}" container_port)"
  replace_tokens "$dir" "$service" "$SHOP_GITHUB_ORG" "$SHOP_GOLDENPATH_REPO" \
    "$SHOP_GCP_DEV_PROJECT" "$SHOP_GCP_PROD_PROJECT" "$SHOP_GCP_REGION" \
    "$app_runtime" "$health_path" "$container_port" "$SHOP_GOLDENPATH_VERSION" \
    "${SHOP_ARTIFACT_REGISTRY_REPO:-${ARTIFACT_REGISTRY_REPO:-}}"
  if deploy_has_tokens "$dir"; then
    die "deploy.yml still has unreplaced template tokens"
  fi
  return 0
}

validate_gcp_project_id() {
  local id="$1"
  if [[ ${#id} -lt 6 || ${#id} -gt 30 ]]; then
    die "project ID must be 6–30 characters: $id"
    return 1
  fi
  if [[ ! "$id" =~ ^[a-z][a-z0-9-]*[a-z0-9]$ ]]; then
    die "invalid project ID (lowercase, no trailing hyphen): $id"
    return 1
  fi
  if [[ "$id" == *--* ]]; then
    die "project ID cannot contain consecutive hyphens: $id"
    return 1
  fi

  local repo_root="${REPO_ROOT:-}"
  if [[ -n "${repo_root}" && -f "${repo_root}/scripts/lib/load-config.sh" ]]; then
    # shellcheck disable=SC1091
    source "${repo_root}/scripts/lib/load-config.sh"
    if load_goldenpath_config "${repo_root}" 2>/dev/null; then
      if goldenpath_is_protected_project "${id}"; then
        die "protected project cannot be used: $id"
        return 1
      fi
    fi
  fi
  return 0
}

show_deployment_summary() {
  local full="$1" cloud_run_svc="$2"
  local verify_script="${VERIFY_DEPLOY:-}"
  [[ -n "$verify_script" && -x "$verify_script" ]] || {
    warn "verify script missing: ${verify_script:-unset}"
    return 1
  }
  # shellcheck disable=SC1090
  eval "$(VERIFY_MAX_ATTEMPTS=8 VERIFY_RETRY_DELAY=8 "$verify_script" "$cloud_run_svc" "$SHOP_GCP_DEV_PROJECT" "$SHOP_GCP_REGION" "$VERIFY_DIR" "$REPO_ROOT")" || true
  printf '\n┌─ Deployment summary ──────────────────────────────────────┐\n'
  printf '│  GitHub repo     https://github.com/%s\n' "$full"
  printf '│  Actions         https://github.com/%s/actions\n' "$full"
  printf '│  Cloud Run       %s\n' "$cloud_run_svc"
  if [[ -n "${VERIFY_URL:-}" ]]; then
    printf '│  Live URL        %s\n' "$VERIFY_URL"
    if [[ "${VERIFY_HEALTH_OK:-false}" == "true" ]]; then
      printf '│  Health          %s → HTTP %s\n' "$VERIFY_HEALTH_PATH" "$VERIFY_STATUS_CODE"
      printf '└───────────────────────────────────────────────────────────┘\n\n'
      log "service is live and healthy"
      printf 'Open your app:\n  %s\n\n' "$VERIFY_URL"
      return 0
    fi
    printf '│  Health          not responding yet — try: shop verify %s\n' "$VERIFY_DIR"
  else
    printf '│  Live URL        (not found yet)\n'
  fi
  printf '└───────────────────────────────────────────────────────────┘\n\n'
  return 1
}
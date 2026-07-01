#!/usr/bin/env bash
# Load enterprise config from config/enterprise.env (or GOLDENPATH_CONFIG).
# Optional keys fall back to config/enterprise.env.example — no hardcoded org values.
# Source this file: source scripts/lib/load-config.sh && load_goldenpath_config
set -euo pipefail

_goldenpath_example_default() {
  local key="$1"
  local repo_root="${2:-}"
  local example="${repo_root}/config/enterprise.env.example"
  [[ -f "${example}" ]] || return 1
  local line
  line="$(grep -E "^${key}=" "${example}" | tail -1)" || return 1
  local val="${line#*=}"
  val="${val%\"}"
  val="${val#\"}"
  printf '%s' "${val}"
}

load_goldenpath_config() {
  local repo_root="${1:-}"
  if [[ -z "${repo_root}" ]]; then
    repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  fi

  local config_file="${GOLDENPATH_CONFIG:-${repo_root}/config/enterprise.env}"
  if [[ ! -f "${config_file}" ]]; then
    printf 'error: missing config file: %s\n' "${config_file}" >&2
    printf '  Copy config/enterprise.env.example to config/enterprise.env and customize.\n' >&2
    return 1
  fi

  # shellcheck disable=SC1090
  source "${config_file}"

  : "${PARENT_PROJECT_ID:?PARENT_PROJECT_ID required in enterprise.env}"
  : "${BILLING_ACCOUNT_ID:?BILLING_ACCOUNT_ID required in enterprise.env}"
  : "${GITHUB_ORG:?GITHUB_ORG required in enterprise.env}"

  export GOLDENPATH_REPO_ROOT="${repo_root}"
  export GOLDENPATH_CONFIG_FILE="${config_file}"
  export PARENT_PROJECT_ID
  export BILLING_ACCOUNT_ID
  export GCP_DEV_PROJECT="${GCP_DEV_PROJECT:-}"
  export GCP_PROD_PROJECT="${GCP_PROD_PROJECT:-}"
  export GCP_SANDBOX_PROJECT="${GCP_SANDBOX_PROJECT:-${GCP_DEV_PROJECT}}"
  export SANDBOX_PROJECT_NAME="${SANDBOX_PROJECT_NAME:-$(_goldenpath_example_default SANDBOX_PROJECT_NAME "${repo_root}" || true)}"
  export SANDBOX_PROJECT_LABELS="${SANDBOX_PROJECT_LABELS:-}"
  export GCP_REGION="${GCP_REGION:-$(_goldenpath_example_default GCP_REGION "${repo_root}" || true)}"
  export GITHUB_ORG
  export PLATFORM_REPO="${PLATFORM_REPO:-$(_goldenpath_example_default PLATFORM_REPO "${repo_root}" || true)}"
  export GOLDENPATH_VERSION="${GOLDENPATH_VERSION:-$(_goldenpath_example_default GOLDENPATH_VERSION "${repo_root}" || true)}"
  export ARTIFACT_REGISTRY_REPO="${ARTIFACT_REGISTRY_REPO:-$(_goldenpath_example_default ARTIFACT_REGISTRY_REPO "${repo_root}" || true)}"
  export MCP_SERVICE_NAME="${MCP_SERVICE_NAME:-$(_goldenpath_example_default MCP_SERVICE_NAME "${repo_root}" || true)}"
  export PROTECTED_PROJECTS="${PROTECTED_PROJECTS:-}"
  export ALLOWED_TEARDOWN_PROJECTS="${ALLOWED_TEARDOWN_PROJECTS:-}"

  export SHOP_GITHUB_ORG="${GITHUB_ORG}"
  export SHOP_GOLDENPATH_REPO="${PLATFORM_REPO}"
  export SHOP_GOLDENPATH_VERSION="${GOLDENPATH_VERSION}"
  export SHOP_GCP_DEV_PROJECT="${GCP_DEV_PROJECT}"
  export SHOP_GCP_PROD_PROJECT="${GCP_PROD_PROJECT:-${GCP_DEV_PROJECT}}"
  export SHOP_GCP_REGION="${GCP_REGION}"
  export SHOP_ARTIFACT_REGISTRY_REPO="${ARTIFACT_REGISTRY_REPO}"
}

goldenpath_protected_projects() {
  local csv="${PROTECTED_PROJECTS:-}"
  if [[ -n "${csv}" ]]; then
    echo "${csv}" | tr ',' ' '
  fi
}

goldenpath_is_protected_project() {
  local project_id="$1"
  local p
  for p in $(goldenpath_protected_projects); do
    p="$(echo "${p}" | xargs)"
    [[ -z "${p}" ]] && continue
    [[ "${project_id}" == "${p}" ]] && return 0
  done
  return 1
}
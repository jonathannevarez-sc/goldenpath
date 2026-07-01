#!/usr/bin/env bash
# Shared safety checks for Golden Path teardown scripts.
set -euo pipefail

_csv_has_value() {
  local csv="$1"
  local needle="$2"
  local item
  local IFS=','
  for item in ${csv}; do
    item="$(echo "${item}" | xargs)"
    [[ -z "${item}" ]] && continue
    if [[ "${needle}" == "${item}" ]]; then
      return 0
    fi
  done
  return 1
}

teardown_load_profile() {
  local repo_root="$1"
  local preset_allowed="${ALLOWED_TEARDOWN_PROJECTS:-}"

  # shellcheck disable=SC1091
  source "${repo_root}/scripts/lib/load-config.sh"
  load_goldenpath_config "${repo_root}" || return 0

  if [[ -n "${preset_allowed}" ]]; then
    ALLOWED_TEARDOWN_PROJECTS="${preset_allowed}"
  fi
}

teardown_assert_deletable_project() {
  local project_id="$1"

  if command -v goldenpath_is_protected_project >/dev/null 2>&1; then
    if goldenpath_is_protected_project "${project_id}"; then
      echo "error: refusing to delete protected project: ${project_id}" >&2
      exit 1
    fi
  else
    local protected_csv="${PROTECTED_PROJECTS:-}"
    if _csv_has_value "${protected_csv}" "${project_id}"; then
      echo "error: refusing to delete protected project: ${project_id}" >&2
      exit 1
    fi
  fi

  local allowed_csv="${ALLOWED_TEARDOWN_PROJECTS:-}"
  if [[ -n "${allowed_csv}" ]]; then
    if ! _csv_has_value "${allowed_csv}" "${project_id}"; then
      echo "error: ${project_id} is not in ALLOWED_TEARDOWN_PROJECTS (${allowed_csv})" >&2
      exit 1
    fi
  fi
}
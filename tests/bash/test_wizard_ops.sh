#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# shellcheck source=../../scripts/setup/goldenpath_setup_ops.sh
source "${REPO_ROOT}/scripts/setup/goldenpath_setup_ops.sh"

test_start "wizard_validate_project_id accepts valid id"
assert_exit 0 wizard_validate_project_id my-valid-project
test_end

test_start "wizard_validate_project_id rejects short id"
assert_exit 1 wizard_validate_project_id abc
test_end

test_start "wizard_validate_service_name accepts valid name"
assert_exit 0 wizard_validate_service_name my-streamlit-app
test_end

test_start "wizard_validate_service_name rejects invalid name"
assert_exit 1 wizard_validate_service_name ab
test_end

test_start "wizard_cmd_available finds bash"
assert_exit 0 wizard_cmd_available bash
test_end

test_start "catalog_get returns fastapi container port"
port="$(catalog_get fastapi container_port)"
assert_eq "8000" "$port"
test_end

test_start "wizard_service_dir prefers last_service_dir"
export WIZ_LAST_SERVICE="demo"
export WIZ_LAST_SERVICE_DIR="${REPO_ROOT}/templates/fastapi"
dir="$(wizard_service_dir demo)"
assert_eq "${REPO_ROOT}/templates/fastapi" "$dir"
test_end

test_start "wizard_normalize_display_name truncates to 30 chars"
long="Golden Path Sandbox gp-sandbox-20260624"
short="$(wizard_normalize_display_name "$long")"
assert_eq "30" "${#short}"
test_end

test_summary
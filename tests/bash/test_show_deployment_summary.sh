#!/usr/bin/env bash
# Contract tests for show_deployment_summary health gate (publish + verify tail).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
MOCK_BIN="${TMP_ROOT}/bin"
SVC_DIR="${TMP_ROOT}/fastapi-svc"
trap 'rm -rf "${TMP_ROOT}"' EXIT
mkdir -p "${MOCK_BIN}" "${SVC_DIR}/.github/workflows"

REPO_ROOT="${REPO_ROOT}" \
SHOP_GCP_DEV_PROJECT="my-valid-project" \
SHOP_GCP_REGION="us-central1" \
VERIFY_DIR="${SVC_DIR}" \
VERIFY_DEPLOY="${REPO_ROOT}/scripts/lib/verify-deployment.sh"
log() { printf '%s\n' "$*"; }
# shellcheck source=../../scripts/lib/scaffold-tokens.sh
source "${REPO_ROOT}/scripts/lib/scaffold-tokens.sh"

cp "${REPO_ROOT}/templates/fastapi/requirements.txt" "${SVC_DIR}/"
cp "${REPO_ROOT}/templates/fastapi/.github/workflows/deploy.yml" "${SVC_DIR}/.github/workflows/"

cat > "${MOCK_BIN}/gcloud" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"run services describe"* ]]; then
  echo "https://demo-dev.mock.run.app"
fi
EOF
chmod +x "${MOCK_BIN}/gcloud"

cat > "${MOCK_BIN}/curl" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"/api/health"* ]]; then
  printf '%s\n200' '{"status":"ok"}'
  exit 0
fi
printf '\n503'
exit 0
EOF
chmod +x "${MOCK_BIN}/curl"

test_start "show_deployment_summary returns success when health check passes"
set +e
out="$(PATH="${MOCK_BIN}:${PATH}" show_deployment_summary "test-org/demo-svc" "demo-svc-dev" 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "service is live and healthy" "$out"
test_end

test_start "show_deployment_summary returns failure when health check fails"
cat > "${MOCK_BIN}/curl" <<'EOF'
#!/usr/bin/env bash
printf '\n503'
exit 0
EOF
chmod +x "${MOCK_BIN}/curl"
set +e
out="$(PATH="${MOCK_BIN}:${PATH}" show_deployment_summary "test-org/demo-svc" "demo-svc-dev" 2>&1)"
code=$?
set -e
assert_eq 1 "$code"
assert_match "not responding yet" "$out"
test_end

test_summary
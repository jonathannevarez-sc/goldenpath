#!/usr/bin/env bash
# Contract tests for verify-deployment.sh with mocked gcloud/curl.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VERIFY="${REPO_ROOT}/scripts/lib/verify-deployment.sh"
TMP_ROOT="$(mktemp -d)"
MOCK_BIN="${TMP_ROOT}/bin"
trap 'rm -rf "${TMP_ROOT}"' EXIT
mkdir -p "${MOCK_BIN}"

cat > "${MOCK_BIN}/gcloud" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"run services describe"* ]]; then
  echo "https://demo-dev.mock.run.app"
fi
EOF
chmod +x "${MOCK_BIN}/gcloud"

cat > "${MOCK_BIN}/curl" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"/api/health"* ]] || [[ "$*" == *"/health"* ]]; then
  printf '%s\n200' '{"status":"ok"}'
  exit 0
fi
printf '\n404'
exit 0
EOF
chmod +x "${MOCK_BIN}/curl"

SVC_DIR="${TMP_ROOT}/fastapi-svc"
mkdir -p "${SVC_DIR}/.github/workflows"
cp "${REPO_ROOT}/templates/fastapi/requirements.txt" "${SVC_DIR}/"
cp "${REPO_ROOT}/templates/fastapi/.github/workflows/deploy.yml" "${SVC_DIR}/.github/workflows/"

test_start "verify-deployment.sh reports healthy service with mocked cloud"
set +e
out="$(
  PATH="${MOCK_BIN}:${PATH}" \
  VERIFY_MAX_ATTEMPTS=1 VERIFY_RETRY_DELAY=0 \
  "${VERIFY}" demo-dev my-valid-project us-central1 "${SVC_DIR}" "${REPO_ROOT}" 2>&1
)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "VERIFY_HEALTH_OK=true" "$out"
assert_match "VERIFY_URL=https://demo-dev.mock.run.app" "$out"
test_end

test_start "verify-deployment.sh fails when Cloud Run URL is missing"
cat > "${MOCK_BIN}/gcloud" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod +x "${MOCK_BIN}/gcloud"
set +e
out="$(
  PATH="${MOCK_BIN}:${PATH}" \
  VERIFY_MAX_ATTEMPTS=1 VERIFY_RETRY_DELAY=0 \
  "${VERIFY}" missing-dev my-valid-project us-central1 2>&1
)"
code=$?
set -e
assert_eq 1 "$code"
assert_match "VERIFY_HEALTH_OK=false" "$out"
test_end

test_summary
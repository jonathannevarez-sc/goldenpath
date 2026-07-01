#!/usr/bin/env bash
# Contract tests for scripts/lib/wif-trust-repo.sh with mocked gcloud.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WIF_TRUST="${REPO_ROOT}/scripts/lib/wif-trust-repo.sh"
TMP_ROOT="$(mktemp -d)"
MOCK_BIN="${TMP_ROOT}/bin"
trap 'rm -rf "${TMP_ROOT}"' EXIT
mkdir -p "${MOCK_BIN}"

cat > "${MOCK_BIN}/gcloud" <<'EOF'
#!/usr/bin/env bash
case "$*" in
  *"projects describe"*)
    echo "123456789"
    ;;
  *"workload-identity-pools list"*)
    echo "projects/123456789/locations/global/workloadIdentityPools/github-pool"
    ;;
  *"service-accounts get-iam-policy"*)
    printf '%s\n' '{"bindings":[{"role":"roles/iam.workloadIdentityUser","members":["principalSet://iam.googleapis.com/projects/123456789/locations/global/workloadIdentityPools/github-pool/attribute.repository/test-org/demo-svc"]},{"role":"roles/iam.serviceAccountTokenCreator","members":["principalSet://iam.googleapis.com/projects/123456789/locations/global/workloadIdentityPools/github-pool/attribute.repository/test-org/demo-svc"]}]}'
    ;;
  *"add-iam-policy-binding"*)
    exit 1
    ;;
  *) printf 'unexpected gcloud: %s\n' "$*" >&2; exit 99 ;;
esac
EOF
chmod +x "${MOCK_BIN}/gcloud"

test_start "wif-trust-repo.sh rejects wrong argument count"
assert_exit 1 "${WIF_TRUST}"
assert_exit 1 "${WIF_TRUST}" my-project test-org
test_end

test_start "wif-trust-repo.sh succeeds when bindings already exist"
set +e
out="$(PATH="${MOCK_BIN}:${PATH}" "${WIF_TRUST}" my-valid-project test-org demo-svc 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "WIF trust ready" "$out"
assert_match "already bound" "$out"
test_end

test_start "wif-trust-repo.sh binds missing roles"
cat > "${MOCK_BIN}/gcloud" <<'EOF'
#!/usr/bin/env bash
case "$*" in
  *"projects describe"*)
    echo "123456789"
    ;;
  *"workload-identity-pools list"*)
    echo "projects/123456789/locations/global/workloadIdentityPools/github-pool"
    ;;
  *"service-accounts get-iam-policy"*)
    printf '%s\n' '{"bindings":[]}'
    ;;
  *"add-iam-policy-binding"*)
    exit 0
    ;;
  *) printf 'unexpected gcloud: %s\n' "$*" >&2; exit 99 ;;
esac
EOF
chmod +x "${MOCK_BIN}/gcloud"
set +e
out="$(PATH="${MOCK_BIN}:${PATH}" "${WIF_TRUST}" my-valid-project test-org demo-svc 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "binding roles/iam.workloadIdentityUser" "$out"
assert_match "binding roles/iam.serviceAccountTokenCreator" "$out"
test_end

test_summary
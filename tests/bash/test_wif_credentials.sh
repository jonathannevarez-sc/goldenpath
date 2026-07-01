#!/usr/bin/env bash
# Contract tests for scripts/lib/wif-credentials.sh (terraform + gcloud fallback).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
MOCK_BIN="${TMP_ROOT}/bin"
trap 'rm -rf "${TMP_ROOT}"' EXIT
mkdir -p "${MOCK_BIN}" "${TMP_ROOT}/platform/bootstrap"

# shellcheck source=../../scripts/lib/wif-credentials.sh
source "${REPO_ROOT}/scripts/lib/wif-credentials.sh"

cat > "${MOCK_BIN}/terraform" <<'EOF'
#!/usr/bin/env bash
case "$*" in
  *dev_github_wif_provider_name*)
    echo "projects/123456/locations/global/workloadIdentityPools/pool/providers/github"
    ;;
  *dev_github_actions_sa_email*)
    echo "github-actions@my-valid-project.iam.gserviceaccount.com"
    ;;
esac
EOF
chmod +x "${MOCK_BIN}/terraform"

cat > "${MOCK_BIN}/gcloud" <<'EOF'
#!/usr/bin/env bash
die() { printf 'unexpected gcloud call: %s\n' "$*" >&2; exit 99; }
case "$*" in
  *"service-accounts list"*)
    echo "github-actions@my-valid-project.iam.gserviceaccount.com"
    ;;
  *"workload-identity-pools list"*)
    echo "projects/123456/locations/global/workloadIdentityPools/github-pool"
    ;;
  *"workload-identity-pools providers list"*)
    echo "projects/123456/locations/global/workloadIdentityPools/github-pool/providers/github"
    ;;
  *) die "$*" ;;
esac
EOF
chmod +x "${MOCK_BIN}/gcloud"

test_start "get_wif_credentials prefers terraform outputs when state exists"
REPO_ROOT="${TMP_ROOT}" WIF_PROVIDER="" WIF_SA=""
touch "${TMP_ROOT}/platform/bootstrap/terraform.tfstate"
set +e
PATH="${MOCK_BIN}:${PATH}" get_wif_credentials "my-valid-project"
code=$?
set -e
assert_eq 0 "$code"
assert_eq "projects/123456/locations/global/workloadIdentityPools/pool/providers/github" "$WIF_PROVIDER"
assert_eq "github-actions@my-valid-project.iam.gserviceaccount.com" "$WIF_SA"
test_end

test_start "get_wif_credentials falls back to gcloud when terraform state is absent"
REPO_ROOT="${TMP_ROOT}" WIF_PROVIDER="" WIF_SA=""
rm -f "${TMP_ROOT}/platform/bootstrap/terraform.tfstate"
set +e
PATH="${MOCK_BIN}:${PATH}" get_wif_credentials "my-valid-project"
code=$?
set -e
assert_eq 0 "$code"
assert_eq "projects/123456/locations/global/workloadIdentityPools/github-pool/providers/github" "$WIF_PROVIDER"
assert_eq "github-actions@my-valid-project.iam.gserviceaccount.com" "$WIF_SA"
test_end

test_start "get_wif_credentials fails when neither terraform nor gcloud can resolve WIF"
REPO_ROOT="${TMP_ROOT}" WIF_PROVIDER="" WIF_SA=""
cat > "${MOCK_BIN}/gcloud" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod +x "${MOCK_BIN}/gcloud"
set +e
PATH="${MOCK_BIN}:${PATH}" get_wif_credentials "my-valid-project"
code=$?
set -e
assert_eq 1 "$code"
test_end

test_summary
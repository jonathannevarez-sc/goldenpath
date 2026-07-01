#!/usr/bin/env bash
# Resolve WIF provider + service account for GitHub Actions deploy.
# Sets WIF_PROVIDER and WIF_SA on success. Requires REPO_ROOT.
get_wif_credentials() {
  local project="$1"
  local bootstrap="${REPO_ROOT}/platform/bootstrap"
  if [[ -f "${bootstrap}/terraform.tfstate" ]] || [[ -f "${bootstrap}/.terraform/terraform.tfstate" ]]; then
    WIF_PROVIDER="$(cd "$bootstrap" && terraform output -raw dev_github_wif_provider_name 2>/dev/null || true)"
    WIF_SA="$(cd "$bootstrap" && terraform output -raw dev_github_actions_sa_email 2>/dev/null || true)"
    if [[ -n "$WIF_PROVIDER" && -n "$WIF_SA" ]]; then return 0; fi
  fi
  local sa pool provider pool_id
  sa="$(gcloud iam service-accounts list --project="$project" --filter='email:github-actions@' --format='value(email)' | head -1)"
  pool="$(gcloud iam workload-identity-pools list --project="$project" --location=global --format='value(name)' | head -1)"
  [[ -n "$sa" && -n "$pool" ]] || return 1
  pool_id="${pool##*/}"
  provider="$(gcloud iam workload-identity-pools providers list --project="$project" --location=global --workload-identity-pool="$pool_id" --format='value(name)' | head -1)"
  WIF_PROVIDER="$provider"
  WIF_SA="$sa"
}
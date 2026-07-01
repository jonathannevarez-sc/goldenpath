#!/usr/bin/env bash
# Detect junk in the goldenpath PLATFORM repo (not service repos).
# Usage:
#   ./scripts/check-repo-hygiene.sh           # health check
#   ./scripts/check-repo-hygiene.sh --explain # why scripts look duplicated
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

issues=0
warn=0
EXPLAIN=false
[[ "${1:-}" == "--explain" ]] && EXPLAIN=true

fail() { echo "  ✗ $1"; issues=$((issues + 1)); }
ok()   { echo "  ✓ $1"; }
note() { echo "  · $1"; warn=$((warn + 1)); }

explain_layout() {
  cat <<'EOF'

Scripts layout — why it looks like duplicates (it is not)
=========================================================

Rule: files at scripts/*.sh are LAUNCHERS (stable doc paths).
      Real logic lives in scripts/{setup,env,deploy,lib}/.

  LAUNCHER (run this)              IMPLEMENTATION (logic lives here)
  ─────────────────────────────────────────────────────────────────
  goldenpath-setup.sh              Unified router → setup/* (auto backend)
  goldenpath-setup-{ps,bash,py,ui}.sh   Same router, fixed --backend
  goldenpath-setup.ps1             Shim → setup/goldenpath-setup.ps1

  setup/goldenpath-setup.ps1       PowerShell wizard + menu (canonical PS)
  setup/goldenpath_setup.sh        Bash wizard (sources goldenpath_setup_ops.sh)
  setup/goldenpath_setup.py        Python wizard (imports goldenpath_ops.py)
  setup/goldenpath_setup_app.py    Streamlit UI (calls setup/modules/*.ps1)
  setup/modules/*.ps1              PS building blocks (Bootstrap, Scaffold, …)

  lib/wizard_defaults.py           Wizard defaults from config/enterprise.env
  lib/load-config.sh               Shared enterprise config loader

  standup-teardown-env.sh    →     env/standup-teardown-env.sh
  teardown-personal-test.sh  →     env/teardown-personal-test.sh
  deploy-mcp-cloudrun.sh     →     deploy/deploy-mcp-cloudrun.sh
  import-mcp-infra-state.sh  →     deploy/import-mcp-infra-state.sh

Parallel wizard backends (PS / bash / Python) are intentional — same menu,
same .goldenpath-setup.local.json, different runtimes. Not copies to delete.

CLI is separate: cli/shop  →  .goldenpath-cli.local.json (do not mix with wizard).

Quick pick:
  No pwsh:     ./scripts/goldenpath-setup-bash.sh
  Has pwsh:    ./scripts/goldenpath-setup.sh          (auto → ps)
  Browser:     ./scripts/goldenpath-setup-ui.sh

EOF
}

echo ""
echo "Golden Path — platform repo hygiene check"
echo "========================================"
echo "Repo: $ROOT"
echo ""

if [[ "$EXPLAIN" == true ]]; then
  explain_layout
  exit 0
fi

echo "1) Platform root must not contain a scaffolded service"
service_markers=(src infra public package.json package-lock.json Dockerfile next.config.mjs tsconfig.json)
found_service=false
for p in "${service_markers[@]}"; do
  if [[ -e "$p" ]]; then
    fail "Remove platform junk: $p/ (belongs in a separate service repo, not goldenpath root)"
    found_service=true
  fi
done
[[ "$found_service" == false ]] && ok "No service scaffold files at repo root"

if [[ -f tests/health.test.mjs ]]; then
  fail "Remove tests/health.test.mjs (service test — platform tests are *.ps1 in tests/)"
else
  ok "No stray service test at tests/health.test.mjs"
fi

echo ""
echo "2) Platform deploy workflow must stay reusable (workflow_call)"
deploy="$ROOT/.github/workflows/deploy.yml"
if [[ ! -f "$deploy" ]]; then
  fail "Missing .github/workflows/deploy.yml"
elif grep -q 'workflow_call:' "$deploy" && ! grep -qE '^\s+push:' "$deploy"; then
  ok "deploy.yml is the reusable Golden Path workflow"
else
  fail "Restore .github/workflows/deploy.yml from platform (workflow_call)"
fi

echo ""
echo "3) Wizard backends present"
for f in \
  scripts/goldenpath-setup.sh \
  scripts/goldenpath-setup-bash.sh \
  scripts/goldenpath-setup-py.sh \
  scripts/setup/goldenpath_setup.sh \
  scripts/setup/goldenpath_setup.py \
  scripts/lib/wizard_defaults.py; do
  if [[ -f "$f" ]]; then
    ok "$f"
  else
    fail "Missing $f"
  fi
done

for skill in \
  skills/goldenpath-setup-wizard/SKILL.md \
  skills/scaffold-shop-service/SKILL.md \
  skills/deploy-to-shop-gcp/SKILL.md \
  skills/shop-terraform-conventions/SKILL.md \
  skills/shop-observability/SKILL.md \
  skills/test-coverage-gap-analysis/SKILL.md; do
  if [[ -f "$skill" ]]; then
    ok "$skill"
  else
    fail "Missing $skill"
  fi
done

echo ""
echo "4) Enterprise config example must exist"
if [[ -f config/enterprise.env.example ]]; then
  ok "config/enterprise.env.example present"
else
  fail "Missing config/enterprise.env.example"
fi

if [[ -f config/enterprise.env ]]; then
  note "Local config present (gitignored): config/enterprise.env"
fi

echo ""
echo "5) Local temp on disk (safe to delete — never commit)"
local_temp=(
  .goldenpath-cli.local.json
  .goldenpath-setup.local.json
  mcp/claude-mcp.generated.json
  platform/bootstrap/terraform.tfvars
  platform/bootstrap/terraform.tfstate
  platform/bootstrap/.terraform
)
for p in "${local_temp[@]}"; do
  [[ -e "$p" ]] && note "Local only (delete freely): $p"
done

echo ""
if [[ "$issues" -gt 0 ]]; then
  echo "FAILED: $issues issue(s)"
  exit 1
fi
[[ "$warn" -gt 0 ]] && echo "OK with $warn local temp note(s)." || echo "OK — platform repo layout looks healthy."
echo ""
exit 0
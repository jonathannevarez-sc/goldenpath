#!/usr/bin/env bash
# Golden Path — Interactive Setup Wizard (bash CLI).
# Pure-bash equivalent of scripts/setup/goldenpath-setup.ps1 — no PowerShell required.
#
# Usage:
#   ./scripts/setup/goldenpath_setup.sh [--wizard|--help]
#   ./scripts/goldenpath-setup-bash.sh
#
# Docs:
#   docs/getting-started/07-setup-wizard-usage.md
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=goldenpath_setup_ops.sh
source "${SCRIPT_DIR}/goldenpath_setup_ops.sh"

# ── UI helpers ────────────────────────────────────────────────────────────────

write_banner() {
  printf '\n'
  printf '  ╔══════════════════════════════════════════════════════════╗\n'
  printf '  ║        Golden Path — Bash Wizard (not shop CLI)          ║\n'
  printf '  ╚══════════════════════════════════════════════════════════╝\n'
  printf '\n'
}

write_step() {
  printf '\n  ── Step %s of %s : %s ──\n\n' "$1" "$2" "$3"
}

press_enter() {
  local msg="${1:-Press Enter to continue...}"
  read -r -p "  ${msg} " _ || true
}

show_usage() {
  cat <<'EOF'

  Golden Path — Bash Wizard (separate from shop CLI)

  QUICK START
    cd goldenpath
    cp config/enterprise.env.example config/enterprise.env
    ./scripts/goldenpath-setup-bash.sh

  CLI USERS: use ./cli/shop instead — do not mix paths.

  MODES
    (no args)     Interactive menu
    --wizard      Full guided setup (steps 1–6)
    --help        This help

  PROJECT PROFILES (menu option 12 — Edit settings)
    1) Sandbox profile      Defaults from config/enterprise.env
    2) New self-contained    Pick your own project ID — create, use, tear down later
    3) Custom existing       Use a GCP project that already exists

  COMMON MENU OPTIONS
    3   Bootstrap GCP in your chosen project
    4   Show WIF secrets (auto-detect)
   15   Dry run — audit what would happen (no deploy / no changes)
    13  Tear down current sandbox project

  SAVED SETTINGS
    .goldenpath-setup.local.json (gitignored)

  DOCS
    docs/getting-started/06-wizard-powershell-advanced.md
    docs/getting-started/05-journey-wizard.md
    docs/getting-started/07-setup-wizard-usage.md

EOF
}

read_choice() {
  local prompt="$1"
  shift
  local options=("$@")
  local default="${READ_CHOICE_DEFAULT:-0}"
  local i
  for i in "${!options[@]}"; do
    local mark=" "
    [[ "$i" -eq "$default" ]] && mark="*"
    printf '  [%s] %s) %s\n' "$mark" "$((i + 1))" "${options[$i]}"
  done
  local raw
  read -r -p "  ${prompt} [default=$((default + 1))]: " raw
  if [[ -z "$raw" ]]; then
    REPLY="$default"
    return 0
  fi
  if [[ "$raw" =~ ^[0-9]+$ ]] && (( raw >= 1 && raw <= ${#options[@]} )); then
    REPLY="$((raw - 1))"
    return 0
  fi
  wizard_warn "Invalid choice — using default."
  REPLY="$default"
}

read_input() {
  local prompt="$1"
  local default="${2:-}"
  local raw
  if [[ -n "$default" ]]; then
    read -r -p "  ${prompt} [${default}]: " raw
    if [[ -z "$raw" ]]; then
      printf '%s\n' "$default"
    else
      printf '%s\n' "$raw"
    fi
  else
    while true; do
      read -r -p "  ${prompt}: " raw
      [[ -n "$raw" ]] && { printf '%s\n' "$raw"; return 0; }
    done
  fi
}

confirm() {
  local prompt="$1"
  local default_yes="${2:-true}"
  local hint="Y/n"
  [[ "$default_yes" != "true" ]] && hint="y/N"
  local raw
  read -r -p "  ${prompt} [${hint}]: " raw
  if [[ -z "$raw" ]]; then
    [[ "$default_yes" == "true" ]]
    return
  fi
  [[ "$raw" =~ ^[Yy] ]]
}

read_validated_project_id() {
  local prompt="$1"
  local default="${2:-}"
  while true; do
    local id
    id="$(read_input "$prompt" "$default")"
    id="$(wizard_lower "$id")"
    if wizard_validate_project_id "$id"; then
      printf '%s\n' "$id"
      return 0
    fi
  done
}

prompt_gcp_project() {
  local purpose="$1"
  local default_project="${2:-}"
  local previous="${WIZ_GCP_DEV_PROJECT:-$WIZ_GCP_PROJECT}"

  printf '\n'
  printf '  ┌─ GCP project: %s ──────────────────────────────────┐\n' "$purpose"
  printf '  │  Bootstrap, WIF secrets, and scaffold MUST use the same     │\n'
  printf '  │  same project ID — or deploy will fail.                  │\n'
  printf '  └───────────────────────────────────────────────────────────┘\n\n'
  [[ -n "$previous" ]] && printf '  Saved project: %s\n' "$previous"

  local default="$default_project"
  [[ -z "$default" && -n "$previous" ]] && default="$previous"
  [[ -z "$default" ]] && default="${WIZ_GCP_PROJECT:-}"

  local project
  project="$(read_validated_project_id "GCP project ID" "$default")"

  if [[ -n "$previous" && "$previous" != "$project" ]]; then
    WIZ_WIF_PROVIDER=""
    WIZ_WIF_SERVICE_ACCOUNT=""
    wizard_warn "Project changed — WIF credentials cleared (use menu 4 after bootstrap)"
  fi

  WIZ_GCP_PROJECT="$project"
  WIZ_GCP_DEV_PROJECT="$project"
  if confirm "Use '${project}' for both dev and prod deploys?"; then
    WIZ_GCP_PROD_PROJECT="$project"
  else
    WIZ_GCP_PROD_PROJECT="$(read_validated_project_id "GCP prod project ID" "$project")"
  fi

  wizard_save_config
  wizard_ok "Locked in: bootstrap + scaffold → ${WIZ_GCP_DEV_PROJECT}"
}

test_scaffold_project_match() {
  local service_dir="$1"
  local dev_tf="${service_dir}/infra/dev.tfvars"
  [[ -f "$dev_tf" ]] || return 0
  local found
  found="$(grep -E 'project_id\s*=' "$dev_tf" | head -1 | sed 's/.*"\([^"]*\)".*/\1/')"
  [[ -n "$found" ]] || return 0
  if [[ "$found" != "$WIZ_GCP_DEV_PROJECT" ]]; then
    wizard_err "Scaffold project_id is '${found}' but wizard has '${WIZ_GCP_DEV_PROJECT}'"
    wizard_warn "Re-run scaffold after setting the correct project in menu 12 or 6."
  else
    wizard_ok "infra/dev.tfvars project_id matches wizard (${found})"
  fi
}

edit_config() {
  printf '\n'
  local options=(
    "Sandbox — defaults from config/enterprise.env"
    "New self-contained sandbox — pick a project name, tear down later"
    "Custom existing project — use a GCP project you already have"
  )
  READ_CHOICE_DEFAULT=0
  read_choice "Choose setup profile" "${options[@]}"
  local choice="$REPLY"

  if [[ "$choice" -eq 0 ]]; then
    wizard_reset_config
    wizard_load_config
    WIZ_PROFILE="sandbox"
    WIZ_SANDBOX_DISPOSABLE="true"
    printf '\n  Sandbox defaults come from config/enterprise.env — confirm or enter your project.\n'
    prompt_gcp_project "sandbox"
  elif [[ "$choice" -eq 1 ]]; then
    WIZ_PROFILE="sandbox"
    WIZ_SANDBOX_DISPOSABLE="true"
    printf '\n  Pick a globally unique GCP project ID (6–30 chars, lowercase).\n'
    printf '  Example: gp-demo-yourname\n'
    printf '  This project will be yours alone — delete it anytime via menu 13.\n\n'
    local suggested="gp-sandbox-$(date +%Y%m%d)"
    prompt_gcp_project "new self-contained sandbox" "$suggested"
    WIZ_PROJECT_DISPLAY_NAME="$(wizard_normalize_display_name "$(read_input "Project display name (max 30 chars)" "${WIZ_GCP_PROJECT}")")"
    WIZ_GCP_REGION="$(read_input "GCP region" "$WIZ_GCP_REGION")"
    WIZ_GITHUB_ORG="$(read_input "GitHub org or username" "$WIZ_GITHUB_ORG")"
    WIZ_GITHUB_PLATFORM_REPO="$(read_input "Platform repo name" "$WIZ_GITHUB_PLATFORM_REPO")"
  else
    WIZ_PROFILE="custom"
    WIZ_SANDBOX_DISPOSABLE="false"
    prompt_gcp_project "existing GCP project"
    WIZ_PROJECT_DISPLAY_NAME="$(wizard_normalize_display_name "$(read_input "Project display name (max 30 chars)" "$WIZ_GCP_PROJECT")")"
    WIZ_GCP_REGION="$(read_input "GCP region" "$WIZ_GCP_REGION")"
    WIZ_GITHUB_ORG="$(read_input "GitHub org or username" "$WIZ_GITHUB_ORG")"
    WIZ_GITHUB_PLATFORM_REPO="$(read_input "Platform repo name" "$WIZ_GITHUB_PLATFORM_REPO")"
  fi

  wizard_save_config
  wizard_ok "Settings saved to .goldenpath-setup.local.json"
  printf '\n  Your settings:\n'
  printf '    Profile:        %s\n' "$WIZ_PROFILE"
  printf '    GCP project:    %s\n' "$WIZ_GCP_PROJECT"
  printf '    Region:         %s\n' "$WIZ_GCP_REGION"
  printf '    GitHub:         %s/%s\n' "$WIZ_GITHUB_ORG" "$WIZ_GITHUB_PLATFORM_REPO"
  [[ "$WIZ_SANDBOX_DISPOSABLE" == "true" ]] && \
    printf '    Disposable:     yes — tear down with menu option 13\n'
  printf '\n'
}

test_prerequisites() {
  write_step 1 1 "Checking prerequisites"
  local all_ok=true
  local tool url
  for tool in gcloud terraform git gh; do
    case "$tool" in
      gcloud) url="https://cloud.google.com/sdk/docs/install" ;;
      terraform) url="https://developer.hashicorp.com/terraform/install" ;;
      git) url="https://git-scm.com/" ;;
      gh) url="https://cli.github.com/" ;;
    esac
    if wizard_cmd_available "$tool"; then
      wizard_ok "${tool} found"
    else
      wizard_err "${tool} missing — install: ${url}"
      all_ok=false
    fi
  done
  for tool in python3 docker pwsh; do
    if wizard_cmd_available "$tool"; then
      wizard_ok "${tool} found (optional)"
    else
      wizard_warn "${tool} not found (optional — needed for MCP / Docker)"
    fi
  done
  [[ "$all_ok" == "true" ]]
}

test_gcloud_auth() {
  local acct
  acct="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)"
  if [[ -z "$acct" ]]; then
    wizard_warn "Not logged in to gcloud."
    if confirm "Open browser for 'gcloud auth login' now?"; then
      gcloud auth login
    else
      return 1
    fi
  else
    wizard_ok "gcloud account: ${acct}"
  fi

  if ! gcloud auth application-default print-access-token >/dev/null 2>&1; then
    wizard_warn "Application Default Credentials not set (Terraform needs these)."
    if confirm "Run 'gcloud auth application-default login' now?"; then
      gcloud auth application-default login
    else
      return 1
    fi
  else
    wizard_ok "Application Default Credentials OK"
  fi
  return 0
}

invoke_bootstrap_standup() {
  prompt_gcp_project "bootstrap"
  wizard_validate_project_id "$WIZ_GCP_PROJECT" || return 1

  printf '\n  Project:  %s\n' "$WIZ_GCP_PROJECT"
  printf '  Profile:  %s\n' "$WIZ_PROFILE"
  [[ "$WIZ_SANDBOX_DISPOSABLE" == "true" ]] && \
    printf '  Teardown: menu option 13 can delete this project when you are done\n'
  printf '\n'

  if ! confirm "Run bootstrap in project '${WIZ_GCP_PROJECT}'? (gcloud + terraform)"; then
    wizard_warn "Skipped bootstrap."
    return 1
  fi

  printf '\n  Bootstrap via bash (gcloud + terraform)...\n'
  wizard_log
  if wizard_bootstrap; then
    wizard_ok "Bootstrap complete"
    wizard_show_wif_secrets || true
    return 0
  fi
  wizard_err "Bootstrap failed"
  return 1
}

invoke_scaffold_service() {
  local outcome_name="" outcome_dir="" outcome_template=""
  local outcome_published=false

  printf '\n'
  local name
  while true; do
    name="$(read_input "Service name (e.g. demo-streamlit)")"
    if wizard_validate_service_name "$name"; then
      break
    fi
  done

  if [[ -n "${WIZ_GCP_DEV_PROJECT:-}" ]]; then
    printf '  Using project: %s\n' "$WIZ_GCP_DEV_PROJECT"
    if ! confirm "Scaffold into project '${WIZ_GCP_DEV_PROJECT}'?"; then
      prompt_gcp_project "scaffold + deploy"
    fi
  else
    prompt_gcp_project "scaffold + deploy"
  fi

  wizard_show_template_list
  local template
  while true; do
    template="$(read_input "Template (nextjs, fastapi, streamlit, ...)" "nextjs")"
    if python3 -c "import json; json.load(open('${CATALOG}'))['${template}']" 2>/dev/null; then
      break
    fi
    wizard_err "Unknown template '${template}'"
  done

  local target
  target="$(wizard_scaffold "$name" "$template" || true)"
  [[ -n "$target" && -d "$target" ]] || return 1

  outcome_name="$name"
  outcome_dir="$target"
  outcome_template="$template"
  test_scaffold_project_match "$target"

  if confirm "Publish to GitHub now? (creates repo, secrets, WIF trust, deploy)"; then
    if wizard_publish "$target"; then
      outcome_published=true
    fi
  else
    printf '  When ready: menu option 7 → Publish service to GitHub\n\n'
  fi

  printf 'OUTCOME_NAME=%s\nOUTCOME_DIR=%s\nOUTCOME_TEMPLATE=%s\nOUTCOME_PUBLISHED=%s\n' \
    "$outcome_name" "$outcome_dir" "$outcome_template" "$outcome_published"
}

invoke_publish_service() {
  local service_dir="${1:-}"
  if [[ -z "$service_dir" ]]; then
    local default
    default="$(wizard_service_dir 2>/dev/null || true)"
    [[ -z "$default" ]] && default="$SCAFFOLD_OUTPUT"
    service_dir="$(read_input "Service directory" "$default")"
  fi
  wizard_publish "$service_dir"
}

invoke_service_doctor() {
  local default
  default="$(wizard_service_dir 2>/dev/null || true)"
  [[ -z "$default" ]] && default="$SCAFFOLD_OUTPUT"
  local service_dir
  service_dir="$(read_input "Service directory" "$default")"
  wizard_doctor "$service_dir"
}

test_deployment() {
  local default_svc="my-service-dev"
  [[ -n "${WIZ_LAST_SERVICE:-}" ]] && default_svc="${WIZ_LAST_SERVICE}-dev"
  local service
  service="$(read_input "Cloud Run service name" "$default_svc")"
  local service_dir
  service_dir="$(wizard_service_dir 2>/dev/null || true)"
  if ! wizard_verify "$service" "$service_dir"; then
    wizard_err "No health endpoint responded."
    if [[ -n "${WIZ_LAST_SERVICE:-}" && -n "${WIZ_GITHUB_ORG:-}" ]]; then
      printf '  Deploy logs: https://github.com/%s/%s/actions\n' \
        "$WIZ_GITHUB_ORG" "$WIZ_LAST_SERVICE"
    fi
  fi
}

show_status() {
  printf '\n  ┌─ Current configuration ─────────────────────────────────┐\n'
  local disposable="no"
  [[ "$WIZ_SANDBOX_DISPOSABLE" == "true" ]] && disposable="yes (option 13)"
  local last_svc="${WIZ_LAST_SERVICE:-(none)}"
  [[ -z "$WIZ_LAST_SERVICE" ]] && last_svc="(none)"
  printf '  │  %-55s│\n' "Profile         ${WIZ_PROFILE}"
  printf '  │  %-55s│\n' "GCP project     ${WIZ_GCP_PROJECT}"
  printf '  │  %-55s│\n' "Region          ${WIZ_GCP_REGION}"
  printf '  │  %-55s│\n' "GitHub org      ${WIZ_GITHUB_ORG}"
  printf '  │  %-55s│\n' "Platform repo   ${WIZ_GITHUB_PLATFORM_REPO}"
  printf '  │  %-55s│\n' "Disposable      ${disposable}"
  printf '  │  %-55s│\n' "Last service    ${last_svc}"
  printf '  │  %-55s│\n' "Config file     ${CONFIG_PATH}"
  printf '  └───────────────────────────────────────────────────────────┘\n'

  if gcloud projects describe "$WIZ_GCP_PROJECT" --format='value(lifecycleState)' >/dev/null 2>&1; then
    local state
    state="$(gcloud projects describe "$WIZ_GCP_PROJECT" --format='value(lifecycleState)')"
    wizard_ok "GCP project exists (${state})"
  else
    wizard_warn "GCP project not found — run bootstrap (option 3)"
  fi

  local ar
  ar="$(gcloud artifacts repositories list --project="$WIZ_GCP_PROJECT" \
    --format='value(name)' 2>/dev/null || true)"
  if [[ -n "$ar" ]]; then
    wizard_ok "Artifact Registry configured"
  else
    wizard_warn "No Artifact Registry — bootstrap may not have run"
  fi

  local wif_lines
  if wif_lines="$(wizard_get_wif_credentials "$WIZ_GCP_PROJECT" 2>/dev/null)"; then
    local source
    source="$(printf '%s\n' "$wif_lines" | sed -n '3p')"
    wizard_ok "WIF credentials available (via ${source})"
  else
    wizard_warn "WIF credentials not found"
  fi

  local services
  services="$(gcloud run services list --project="$WIZ_GCP_PROJECT" \
    --region="$WIZ_GCP_REGION" --format='table(SERVICE,REGION,URL)' 2>/dev/null || true)"
  if [[ -n "$services" ]]; then
    printf '\n%s\n' "$services"
  fi
  printf '\n'
}

new_mcp_claude_config() {
  local mcp_dir="${REPO_ROOT}/mcp"
  local venv_python="${mcp_dir}/.venv/bin/python"
  if [[ ! -x "$venv_python" ]]; then
    wizard_warn "MCP venv not found at ${venv_python}"
    if confirm "Create venv and install MCP dependencies now?"; then
      wizard_cmd_available python3 || { wizard_err "python3 required"; return 1; }
      python3 -m venv "${mcp_dir}/.venv"
      "${mcp_dir}/.venv/bin/pip" install -r "${mcp_dir}/requirements.txt"
      wizard_ok "MCP venv created"
    else
      return 0
    fi
  fi
  wizard_generate_mcp_config
}

reset_wizard_state() {
  printf '\n  Resets .goldenpath-setup.local.json to defaults.\n'
  printf '  Does NOT delete GCP projects, GitHub repos, or Cloud Run services.\n'
  printf '  Use menu 13 to tear down the GCP sandbox if you want that too.\n\n'
  if ! confirm "Reset local wizard state for a fresh start?"; then
    return 1
  fi
  wizard_reset_config
  wizard_load_config
  wizard_ok "Wizard state reset — profile: sandbox, project: ${WIZ_GCP_PROJECT}"
  printf '\n  Next: option 1 (full guided setup) or --wizard\n\n'
}

invoke_dryrun() {
  if ! command -v python3 >/dev/null 2>&1; then
    wizard_err "python3 required for dry run"
    return 1
  fi
  printf '\n  Running read-only wizard audit (no GCP/GitHub changes)...\n\n'
  if ! python3 "${SCRIPT_DIR}/goldenpath_dryrun.py"; then
    wizard_warn "Dry run reported blockers — review output before bootstrap or publish"
  fi
}

invoke_teardown_sandbox() {
  wizard_validate_project_id "$WIZ_GCP_PROJECT" || return 1

  if [[ "$WIZ_SANDBOX_DISPOSABLE" != "true" && "$WIZ_PROFILE" != "sandbox" ]]; then
    wizard_warn "Current profile '${WIZ_PROFILE}' is not marked disposable."
    confirm "Continue teardown anyway?" || return 0
  fi

  printf '\n  This will DESTROY all Golden Path resources in:\n'
  printf '    %s\n\n' "$WIZ_GCP_PROJECT"
  printf '  Steps: terraform destroy → delete GCP project (irreversible)\n'
  printf '  Protected projects (PROTECTED_PROJECTS in enterprise.env) cannot be deleted.\n\n'

  confirm "Destroy bootstrap resources in '${WIZ_GCP_PROJECT}'?" || return 0
  local delete_project=false
  confirm "DELETE entire GCP project '${WIZ_GCP_PROJECT}'?" && delete_project=true

  if wizard_teardown "$delete_project"; then
    wizard_ok "Sandbox '${WIZ_GCP_PROJECT}' torn down."
    printf '  Pick a new project in menu option 12 to stand up again.\n'
  else
    wizard_err "Teardown failed"
  fi
}

show_wizard_completion() {
  local bootstrap_ran="$1"
  printf '\n'
  printf '  ╔══════════════════════════════════════════════════════════╗\n'
  printf '  ║                    Setup wizard complete!                ║\n'
  printf '  ╚══════════════════════════════════════════════════════════╝\n\n'
  printf '  What you set up:\n'
  printf '    Profile        %s → %s (%s)\n' "$WIZ_PROFILE" "$WIZ_GCP_PROJECT" "$WIZ_GCP_REGION"
  if [[ "$bootstrap_ran" == "true" ]]; then
    printf '    Bootstrap      ✓ GCP project + Terraform + Artifact Registry\n'
  else
    printf '    Bootstrap      skipped — run menu 3 when ready\n'
  fi
  [[ -n "${WIZ_WIF_PROVIDER:-}" ]] && \
    printf '    WIF secrets    ✓ ready for GitHub Actions deploys\n'
  printf '\n  Wizard menu:  ./scripts/goldenpath-setup-bash.sh\n'
  printf '  All services: menu 11  |  Tear down sandbox: menu 13\n\n'
}

start_full_wizard() {
  write_banner
  printf '  This wizard walks you through Golden Path setup one step at a time.\n'
  printf '  You can stop anytime and resume from the main menu.\n\n'

  wizard_load_config
  local bootstrap_ran=false

  write_step 1 6 "Choose your profile"
  edit_config

  write_step 2 6 "Check tools & login"
  if ! test_prerequisites; then
    wizard_err "Fix missing tools, then run the wizard again."
    press_enter
    return 0
  fi
  if ! test_gcloud_auth; then
    wizard_err "GCP auth required before continuing."
    press_enter
    return 0
  fi
  press_enter

  write_step 3 6 "Bootstrap GCP (one-time)"
  printf '  Creates the project (if needed) and runs Terraform bootstrap.\n'
  printf '  Project: %s (%s)\n' "$WIZ_GCP_PROJECT" "$WIZ_PROFILE"
  [[ "$WIZ_SANDBOX_DISPOSABLE" == "true" ]] && \
    printf '  Disposable — tear down later with menu option 13.\n'
  printf '  Does not modify protected projects listed in config/enterprise.env.\n\n'
  if confirm "Run bootstrap now?"; then
    invoke_bootstrap_standup && bootstrap_ran=true
  else
    wizard_warn "Skipped — you can run it later from the main menu (option 3)."
  fi
  wizard_load_config
  press_enter

  write_step 4 6 "GitHub deploy credentials"
  wizard_show_wif_secrets || true
  if confirm "Set WIF secrets on platform repo '${WIZ_GITHUB_PLATFORM_REPO}' via gh?"; then
    wizard_set_github_secrets "$WIZ_GITHUB_PLATFORM_REPO" || true
  fi
  wizard_load_config
  press_enter

  write_step 5 6 "Scaffold + publish your first service"
  printf '  Creates a service folder, copies a template, publishes to GitHub,\n'
  printf '  watches the deploy workflow, then verifies Cloud Run + health.\n\n'
  if confirm "Scaffold and publish a service now?"; then
    invoke_scaffold_service || true
  else
    printf '  Skip for now — menu 6 (scaffold) and menu 7 (publish) later.\n'
  fi
  press_enter

  write_step 6 6 "MCP for Claude (optional)"
  if confirm "Generate Claude MCP config?"; then
    new_mcp_claude_config || true
  else
    printf '  Skipped — menu 10 anytime.\n'
  fi

  show_wizard_completion "$bootstrap_ran"
  press_enter "Press Enter to return to the main menu..."
}

show_main_menu() {
  wizard_load_config

  while true; do
    write_banner
    printf '  GCP: %s  |  GitHub: %s/%s\n' \
      "$WIZ_GCP_PROJECT" "$WIZ_GITHUB_ORG" "$WIZ_GITHUB_PLATFORM_REPO"
    printf '\n  What would you like to do?\n\n'
    printf '    1) Full guided setup (recommended for new users)\n'
    printf '    2) Check prerequisites\n'
    printf '    3) Bootstrap GCP (stand up / terraform apply)\n'
    printf '    4) Show GitHub WIF secrets\n'
    printf '    5) Set GitHub WIF secrets on a repo\n'
    printf '    6) Scaffold a new service (bash — not shop CLI)\n'
    printf '    7) Publish service to GitHub (repo + secrets + deploy)\n'
    printf '    8) Verify a deployment (health check)\n'
    printf '    9) Doctor — diagnose deploy blockers\n'
    printf '   10) Generate Claude MCP config\n'
    printf '   11) Show current status\n'
    printf '   12) Edit settings (project, org, region)\n'
    printf '   13) Tear down current sandbox project\n'
    printf '   14) Fresh start (reset local wizard state)\n'
    printf '   15) Dry run — audit wizard (no deploy / no changes)\n'
    printf '    h) Help / usage\n'
    printf '    0) Exit\n\n'

    local pick
    pick="$(read_input "Choice" "1")"

    case "$pick" in
      1) start_full_wizard ;;
      2) test_prerequisites || true; press_enter ;;
      3)
        if test_prerequisites && test_gcloud_auth; then invoke_bootstrap_standup || true; fi
        press_enter
        ;;
      4) wizard_show_wif_secrets || true; press_enter ;;
      5)
        local repo
        repo="$(read_input "Repo (name or org/name)" "$WIZ_GITHUB_PLATFORM_REPO")"
        wizard_set_github_secrets "$repo" || true
        press_enter
        ;;
      6) invoke_scaffold_service || true; press_enter ;;
      7) invoke_publish_service "" || true; press_enter ;;
      8) test_deployment; press_enter ;;
      9) invoke_service_doctor; press_enter ;;
      10) new_mcp_claude_config || true; press_enter ;;
      11) show_status; press_enter ;;
      12) edit_config; press_enter ;;
      13) invoke_teardown_sandbox || true; press_enter ;;
      14) reset_wizard_state || true; press_enter ;;
      15) invoke_dryrun || true; press_enter ;;
      h|H|help|\?) show_usage; press_enter ;;
      0) printf '  Bye!\n'; return 0 ;;
      *) wizard_warn "Unknown option — type h for help"; sleep 1 ;;
    esac

    wizard_load_config
    clear 2>/dev/null || true
  done
}

main() {
  cd "$REPO_ROOT"
  case "${1:-}" in
    --help|-h|-\?) show_usage ;;
    --wizard) start_full_wizard ;;
    "") show_main_menu ;;
    *) wizard_err "Unknown argument: $1 (try --help)"; exit 1 ;;
  esac
}

main "$@"
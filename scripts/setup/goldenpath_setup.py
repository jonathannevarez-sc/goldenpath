#!/usr/bin/env python3
"""Golden Path — Interactive Setup Wizard (Python CLI).

Pure-Python equivalent of scripts/setup/goldenpath-setup.ps1 — no PowerShell required.

Usage:
  python3 ./scripts/setup/goldenpath_setup.py [--wizard|--help]
  ./scripts/goldenpath-setup-py.sh

Docs:
  docs/getting-started/07-setup-wizard-usage.md
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Allow running as script from repo root or scripts/setup/
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import goldenpath_ops as ops  # noqa: E402

REPO_ROOT = ops.REPO_ROOT
CONFIG_PATH = ops.CONFIG_PATH


# ── UI helpers ────────────────────────────────────────────────────────────────


def write_banner() -> None:
    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║       Golden Path — Python Wizard (not shop CLI)         ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print()


def write_step(number: int, total: int, title: str) -> None:
    print()
    print(f"  ── Step {number} of {total} : {title} ──")
    print()


def write_ok(message: str) -> None:
    print(f"  ✓ {message}")


def write_warn(message: str) -> None:
    print(f"  ! {message}")


def write_err(message: str) -> None:
    print(f"  ✗ {message}")


def read_choice(prompt: str, options: list[str], default: int = 0) -> int:
    for i, opt in enumerate(options):
        mark = "*" if i == default else " "
        print(f"  [{mark}] {i + 1}) {opt}")
    raw = input(f"  {prompt} [default={default + 1}]: ").strip()
    if not raw:
        return default
    try:
        n = int(raw)
        if 1 <= n <= len(options):
            return n - 1
    except ValueError:
        pass
    write_warn("Invalid choice — using default.")
    return default


def read_input(prompt: str, default: str = "") -> str:
    if default:
        raw = input(f"  {prompt} [{default}]: ").strip()
        return default if not raw else raw
    while True:
        raw = input(f"  {prompt}: ").strip()
        if raw:
            return raw


def confirm(prompt: str, default_yes: bool = True) -> bool:
    hint = "Y/n" if default_yes else "y/N"
    raw = input(f"  {prompt} [{hint}]: ").strip()
    if not raw:
        return default_yes
    return raw.lower().startswith("y")


def press_enter(message: str = "Press Enter to continue...") -> None:
    input(f"  {message}")


def show_usage() -> None:
    print(
        """
  Golden Path — Python Wizard (separate from shop CLI)

  QUICK START
    cd goldenpath
    cp config/enterprise.env.example config/enterprise.env
    ./scripts/goldenpath-setup-py.sh

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
"""
    )


# ── Config & project prompts ──────────────────────────────────────────────────


def read_validated_project_id(prompt: str, default: str = "") -> str:
    while True:
        pid = read_input(prompt, default).lower()
        err = ops.validate_project_id(pid)
        if not err:
            return pid
        write_err(err)


def prompt_gcp_project(cfg: dict, purpose: str, default_project: str = "") -> dict:
    previous = str(cfg.get("gcp_dev_project") or cfg.get("gcp_project") or "")
    print()
    print(f"  ┌─ GCP project: {purpose} ──────────────────────────────────┐")
    print("  │  Bootstrap, WIF secrets, and scaffold MUST use the same     │")
    print("  │  same project ID — or deploy will fail.                  │")
    print("  └───────────────────────────────────────────────────────────┘")
    print()
    if previous:
        print(f"  Saved project: {previous}")
    defaults = ops.default_config()
    default = default_project or previous or defaults.get("gcp_project", "")
    project = read_validated_project_id("GCP project ID", default)

    if previous and previous != project:
        cfg["wif_provider"] = ""
        cfg["wif_service_account"] = ""
        write_warn("Project changed — WIF credentials cleared (use menu 4 after bootstrap)")

    cfg["gcp_project"] = project
    cfg["gcp_dev_project"] = project
    if confirm(f"Use '{project}' for both dev and prod deploys?"):
        cfg["gcp_prod_project"] = project
    else:
        cfg["gcp_prod_project"] = read_validated_project_id(
            "GCP prod project ID", project
        )

    ops.save_config(cfg)
    write_ok(f"Locked in: bootstrap + scaffold → {cfg['gcp_dev_project']}")
    return cfg


def test_scaffold_project_match(cfg: dict, service_dir: Path) -> None:
    dev_tf = service_dir / "infra/dev.tfvars"
    if not dev_tf.exists():
        return
    m = re.search(r'project_id\s*=\s*"([^"]+)"', dev_tf.read_text())
    if not m:
        return
    found = m.group(1)
    if found != cfg["gcp_dev_project"]:
        write_err(
            f"Scaffold project_id is '{found}' but wizard has "
            f"'{cfg['gcp_dev_project']}'"
        )
        write_warn(
            "Re-run scaffold after setting the correct project in menu 12 or 6."
        )
    else:
        write_ok(f"infra/dev.tfvars project_id matches wizard ({found})")


def edit_config(cfg: dict) -> dict:
    print()
    choice = read_choice(
        "Choose setup profile",
        [
            "Sandbox — defaults from config/enterprise.env",
            "New self-contained sandbox — pick a project name, tear down later",
            "Custom existing project — use a GCP project you already have",
        ],
        0,
    )

    if choice == 0:
        defaults = ops.default_config()
        cfg.update(defaults)
        cfg["profile"] = "sandbox"
        cfg["sandbox_disposable"] = True
        print()
        print(
            "  Sandbox defaults come from config/enterprise.env — confirm or enter your project."
        )
        cfg = prompt_gcp_project(cfg, "sandbox")
    elif choice == 1:
        cfg["profile"] = "sandbox"
        cfg["sandbox_disposable"] = True
        print()
        print("  Pick a globally unique GCP project ID (6–30 chars, lowercase).")
        print("  Example: gp-demo-yourname")
        print(
            "  This project will be yours alone — delete it anytime via menu 13."
        )
        print()
        suggested = f"gp-sandbox-{datetime.now().strftime('%Y%m%d')}"
        cfg = prompt_gcp_project(cfg, "new self-contained sandbox", suggested)
        cfg["project_display_name"] = ops.normalize_project_display_name(
            read_input("Project display name (max 30 chars)", cfg["gcp_project"]),
            fallback=cfg["gcp_project"],
        )
        cfg["gcp_region"] = read_input("GCP region", cfg["gcp_region"])
        cfg["github_org"] = read_input("GitHub org or username", cfg["github_org"])
        cfg["github_platform_repo"] = read_input(
            "Platform repo name", cfg["github_platform_repo"]
        )
    else:
        cfg["profile"] = "custom"
        cfg["sandbox_disposable"] = False
        cfg = prompt_gcp_project(cfg, "existing GCP project")
        cfg["project_display_name"] = ops.normalize_project_display_name(
            read_input("Project display name (max 30 chars)", cfg["gcp_project"]),
            fallback=cfg["gcp_project"],
        )
        cfg["gcp_region"] = read_input("GCP region", cfg["gcp_region"])
        cfg["github_org"] = read_input("GitHub org or username", cfg["github_org"])
        cfg["github_platform_repo"] = read_input(
            "Platform repo name", cfg["github_platform_repo"]
        )

    ops.save_config(cfg)
    write_ok("Settings saved to .goldenpath-setup.local.json")
    print()
    print("  Your settings:")
    print(f"    Profile:        {cfg['profile']}")
    print(f"    GCP project:    {cfg['gcp_project']}")
    print(f"    Region:         {cfg['gcp_region']}")
    print(f"    GitHub:         {cfg['github_org']}/{cfg['github_platform_repo']}")
    if cfg.get("sandbox_disposable"):
        print("    Disposable:     yes — tear down with menu option 13")
    print()
    return cfg


# ── Prerequisites & auth ──────────────────────────────────────────────────────


def test_prerequisites() -> bool:
    write_step(1, 1, "Checking prerequisites")
    required = {
        "gcloud": "https://cloud.google.com/sdk/docs/install",
        "terraform": "https://developer.hashicorp.com/terraform/install",
        "git": "https://git-scm.com/",
        "gh": "https://cli.github.com/",
    }
    optional = ["python3", "docker", "pwsh"]
    all_ok = True
    for tool, url in required.items():
        if ops.cmd_available(tool):
            write_ok(f"{tool} found")
        else:
            write_err(f"{tool} missing — install: {url}")
            all_ok = False
    for tool in optional:
        if ops.cmd_available(tool):
            write_ok(f"{tool} found (optional)")
        else:
            write_warn(f"{tool} not found (optional — needed for MCP / Docker)")
    return all_ok


def test_gcloud_auth() -> bool:
    acct = ops.run_cmd(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
    )
    if acct.exit_code != 0 or not acct.stdout:
        write_warn("Not logged in to gcloud.")
        if confirm("Open browser for 'gcloud auth login' now?"):
            ops.run_cmd_live(["gcloud", "auth", "login"])
        else:
            return False
    else:
        write_ok(f"gcloud account: {acct.stdout}")

    adc = ops.run_cmd(["gcloud", "auth", "application-default", "print-access-token"])
    if adc.exit_code != 0:
        write_warn("Application Default Credentials not set (Terraform needs these).")
        if confirm("Run 'gcloud auth application-default login' now?"):
            ops.run_cmd_live(["gcloud", "auth", "application-default", "login"])
        else:
            return False
    else:
        write_ok("Application Default Credentials OK")
    return True


# ── WIF ───────────────────────────────────────────────────────────────────────


def ensure_wif_credentials(cfg: dict) -> dict:
    if ops.wif_credentials_stale(cfg):
        write_warn("WIF credentials are for a different project — clearing")
        cfg["wif_provider"] = ""
        cfg["wif_service_account"] = ""
        ops.save_config(cfg)
    if not cfg.get("wif_provider") or not cfg.get("wif_service_account"):
        show_wif_secrets(cfg)
    return cfg


def show_wif_secrets(cfg: dict) -> bool:
    print(
        f"  Looking up GitHub deploy credentials for project: "
        f"{cfg['gcp_dev_project']}"
    )
    wif = ops.get_wif_credentials(cfg["gcp_dev_project"])
    if not wif:
        write_err("Could not find WIF credentials. Run bootstrap first (menu 3).")
        return False

    write_ok(f"Found via {wif['source']}")
    cfg["wif_provider"] = wif["provider"]
    cfg["wif_service_account"] = wif["service_account"]
    ops.save_config(cfg)
    write_ok("Settings saved to .goldenpath-setup.local.json")

    print()
    print("  ┌─────────────────────────────────────────────────────────┐")
    print("  │  GitHub secrets — add these to your repos               │")
    print("  └─────────────────────────────────────────────────────────┘")
    print()
    print("  Secret name                  Value")
    print("  ─────────────────────────────────────────────────────────")
    print(f"  GCP_WIF_PROVIDER             {wif['provider']}")
    print(f"  GCP_WIF_SERVICE_ACCOUNT      {wif['service_account']}")
    print()
    print(f"  Source: {wif['source']}  |  Project: {cfg['gcp_project']}")
    print()
    print("  Add to:")
    print(f"    • Platform repo:  {cfg['github_org']}/{cfg['github_platform_repo']}")
    print("    • Each service repo you scaffold")
    print()
    print("  Also enable reusable workflows on the platform repo:")
    print(f"    GitHub → {cfg['github_platform_repo']} → Settings → Actions → General")
    print("    → Allow reusable workflows from this repository")
    print()
    return True


def set_github_secrets(cfg: dict, repo: str) -> None:
    if not ops.cmd_available("gh"):
        write_err("gh CLI required. Install: https://cli.github.com/")
        return
    cfg = ensure_wif_credentials(cfg)
    if not cfg.get("wif_provider") or not cfg.get("wif_service_account"):
        return
    full_repo = repo if "/" in repo else f"{cfg['github_org']}/{repo}"
    print(f"  Setting secrets on {full_repo} ...")
    try:
        ops.set_github_secrets(cfg, repo)
        write_ok(f"Secrets set on {full_repo}")
    except RuntimeError as exc:
        write_err(str(exc))


# ── Bootstrap ─────────────────────────────────────────────────────────────────


def invoke_bootstrap_standup(cfg: dict) -> bool:
    cfg = prompt_gcp_project(cfg, "bootstrap")
    err = ops.validate_project_id(cfg["gcp_project"])
    if err:
        write_err(err)
        return False

    print()
    print(f"  Project:  {cfg['gcp_project']}")
    print(f"  Profile:  {cfg['profile']}")
    if cfg.get("sandbox_disposable"):
        print("  Teardown: menu option 13 can delete this project when you are done")
    print()

    if not confirm(
        f"Run bootstrap in project '{cfg['gcp_project']}'? (gcloud + terraform)"
    ):
        write_warn("Skipped bootstrap.")
        return False

    print()
    print("  Bootstrap via Python (gcloud + terraform)...")
    print("  (live output below)")
    print()
    try:
        ops.bootstrap(cfg)
    except Exception as exc:
        write_err(f"Bootstrap failed: {exc}")
        return False

    write_ok("Bootstrap complete")
    show_wif_secrets(cfg)
    return True


# ── Scaffold & publish ────────────────────────────────────────────────────────


def show_template_list() -> None:
    try:
        catalog = ops.load_catalog()
        print("  Template       Runtime  Port   Health")
        print("  ────────────────────────────────────────")
        for name, meta in catalog.items():
            default = " (default)" if meta.get("default") else ""
            print(
                f"  {name:<14} {meta.get('app_runtime', ''):<8} "
                f"{str(meta.get('container_port', '')):<6} "
                f"{meta.get('health_check_path', '')}{default}"
            )
        print()
    except Exception as exc:
        write_warn(f"Could not load template catalog: {exc}")


def invoke_scaffold_service(cfg: dict) -> dict:
    outcome = {
        "service_name": "",
        "service_dir": "",
        "template": "",
        "published": False,
        "publish": None,
        "verify": None,
    }

    print()
    while True:
        name = read_input("Service name (e.g. demo-streamlit)")
        name_err = ops.validate_service_name(name)
        if not name_err:
            break
        write_err(name_err)

    scaffold_parent = ops.get_scaffold_output_dir()
    target_dir = scaffold_parent / name
    if target_dir.exists() and any(target_dir.iterdir()):
        write_err(f"Folder already exists and is not empty: {target_dir}")
        return outcome

    target_dir.mkdir(parents=True, exist_ok=True)
    cfg["last_service"] = name
    cfg["last_service_dir"] = str(target_dir)
    ops.save_config(cfg)
    write_ok(f"Folder created: {target_dir}")
    print(f"  (outside platform repo: {scaffold_parent})")
    print("  (open in Finder/VS Code now — template files copy next)")
    print()

    if cfg.get("gcp_dev_project"):
        print(f"  Using project: {cfg['gcp_dev_project']}")
        if not confirm(
            f"Scaffold into project '{cfg['gcp_dev_project']}'?", default_yes=True
        ):
            cfg = prompt_gcp_project(cfg, "scaffold + deploy")
    else:
        cfg = prompt_gcp_project(cfg, "scaffold + deploy")

    show_template_list()
    catalog = ops.load_catalog()
    template = ""
    while True:
        template = read_input("Template (nextjs, fastapi, streamlit, ...)", "nextjs")
        if template in catalog:
            break
        write_err(
            f"Unknown template '{template}'. "
            f"Available: {', '.join(catalog.keys())}"
        )

    print()
    print(f"  Scaffolding {template} into {name} ...")
    try:
        result = ops.scaffold(name, template, scaffold_parent, cfg)
    except Exception as exc:
        write_err(f"Scaffold failed: {exc}")
        return outcome

    cfg["last_service"] = name
    cfg["last_service_dir"] = str(result.service_dir)
    ops.save_config(cfg)
    outcome["service_name"] = name
    outcome["service_dir"] = str(result.service_dir)
    outcome["template"] = template

    write_ok(f"Scaffolded: {result.service_dir} (branch: main)")
    test_scaffold_project_match(cfg, result.service_dir)
    print()
    print(f"  project_id = {cfg['gcp_dev_project']} in infra/*.tfvars")
    print(f"  health path  = {result.health_check_path}")
    print()

    if confirm("Publish to GitHub now? (creates repo, secrets, WIF trust, deploy)"):
        pub = invoke_publish_service(cfg, str(result.service_dir))
        if pub:
            outcome["published"] = True
            outcome["publish"] = pub
            outcome["verify"] = pub.get("verify")
    else:
        print("  When ready: menu option 7 → Publish service to GitHub")
        print()
    return outcome


def invoke_publish_service(cfg: dict, service_dir: str = "") -> dict | None:
    if not service_dir:
        default = ops.service_dir_for(cfg)
        default_str = str(default) if default else str(ops.get_scaffold_output_dir())
        service_dir = read_input("Service directory", default_str)

    cfg = ensure_wif_credentials(cfg)
    if not cfg.get("wif_provider") or not cfg.get("wif_service_account"):
        write_err(
            f"WIF credentials missing — bootstrap project "
            f"{cfg['gcp_dev_project']} first (menu 3), then menu 4"
        )
        return None

    service_path = Path(service_dir).resolve()
    service_name = service_path.name
    cloud_run_svc = f"{service_name}-dev"

    try:
        print()
        print(
            f"  Publishing {service_name} "
            "(GitHub → secrets → WIF → push → deploy watch)..."
        )
        print()

        def on_step(msg: str) -> None:
            print(f"  {msg}")

        pub = ops.publish(
            service_path,
            cfg,
            cfg["wif_provider"],
            cfg["wif_service_account"],
            watch_deploy=True,
            on_step=on_step,
        )
        write_ok(f"Published: {pub.repo}")
        print(f"  https://github.com/{pub.repo}")

        verify = None
        if pub.deploy_ok is False:
            write_err(
                "GitHub deploy workflow failed — repo was created but "
                "Cloud Run is not live yet."
            )
            print(f"  Actions: https://github.com/{pub.repo}/actions")
            print(
                "  Retry:   menu 7 (Publish) — WIF trust + deploy rerun are automatic."
            )
            print("  Doctor:  menu 9 to list blockers")
        else:
            if pub.deploy_ok:
                write_ok("Deploy workflow succeeded")
            else:
                write_warn("Deploy watch skipped — checking Cloud Run directly")
            print()
            print("  Verifying Cloud Run + health (may take ~1 min on cold start)...")
            verify = ops.verify_deployment(
                cloud_run_svc,
                cfg,
                service_path,
            )
            ops.show_deployment_result(verify, pub.repo, verbose=True)
            if verify.health_ok:
                write_ok("Service is live and healthy")
            elif verify.url:
                write_warn(
                    "Service URL exists but health check not ready — "
                    "wait 30s and run menu 8"
                )
            else:
                write_warn(
                    "Cloud Run service not visible yet — check Actions or run menu 8"
                )

        cfg["last_service"] = service_name
        cfg["last_service_dir"] = str(service_path)
        ops.save_config(cfg)

        return {
            "repo": pub.repo,
            "service_dir": str(service_path),
            "service_name": service_name,
            "cloud_run_svc": cloud_run_svc,
            "deploy_ok": pub.deploy_ok,
            "verify": verify,
        }
    except Exception as exc:
        write_err(f"Publish failed: {exc}")
        print("  Run menu option 9 (Doctor) to diagnose.")
        return None


def invoke_service_doctor(cfg: dict) -> None:
    default = ops.service_dir_for(cfg)
    default_str = str(default) if default else str(ops.get_scaffold_output_dir())
    service_dir = read_input("Service directory", default_str)
    issues = ops.service_doctor(Path(service_dir), cfg)
    print()
    if not issues:
        write_ok("No issues found")
    else:
        print("  Issues:")
        for issue in issues:
            print(f"    • {issue}")
        print()
        print("  Fix with menu option 7 (Publish service)")
    print()


def test_deployment(cfg: dict) -> None:
    default_svc = (
        f"{cfg['last_service']}-dev" if cfg.get("last_service") else "my-service-dev"
    )
    service = read_input("Cloud Run service name", default_svc)
    service_path = ops.service_dir_for(cfg)
    verify = ops.verify_deployment(
        service,
        cfg,
        service_path,
    )
    if verify.error and not verify.url:
        write_err(verify.error)
        print("  List services: menu 11 (Show status)")
        return

    repo = (
        f"{cfg['github_org']}/{cfg['last_service']}"
        if cfg.get("last_service") and cfg.get("github_org")
        else ""
    )
    ops.show_deployment_result(verify, repo, verbose=True)
    if not verify.health_ok:
        write_err("No health endpoint responded.")
        if repo:
            print(f"  Deploy logs: https://github.com/{repo}/actions")


def show_status(cfg: dict) -> None:
    print()
    print("  ┌─ Current configuration ─────────────────────────────────┐")
    disposable = (
        "yes (option 13)" if cfg.get("sandbox_disposable") else "no"
    )
    last_svc = cfg.get("last_service") or "(none)"
    lines = [
        f"Profile         {cfg.get('profile', '')}",
        f"GCP project     {cfg.get('gcp_project', '')}",
        f"Region          {cfg.get('gcp_region', '')}",
        f"GitHub org      {cfg.get('github_org', '')}",
        f"Platform repo   {cfg.get('github_platform_repo', '')}",
        f"Disposable      {disposable}",
        f"Last service    {last_svc}",
        f"Config file     {CONFIG_PATH}",
    ]
    for line in lines:
        print(f"  │  {line:<55}│")
    print("  └───────────────────────────────────────────────────────────┘")

    proj = ops.run_cmd(
        [
            "gcloud",
            "projects",
            "describe",
            cfg["gcp_project"],
            "--format=value(lifecycleState)",
        ]
    )
    if proj.exit_code == 0:
        write_ok(f"GCP project exists ({proj.stdout})")
    else:
        write_warn("GCP project not found — run bootstrap (option 3)")

    ar = ops.run_cmd(
        [
            "gcloud",
            "artifacts",
            "repositories",
            "list",
            f"--project={cfg['gcp_project']}",
            "--format=value(name)",
        ]
    )
    if ar.exit_code == 0 and ar.stdout:
        write_ok("Artifact Registry configured")
    else:
        write_warn("No Artifact Registry — bootstrap may not have run")

    wif = ops.get_wif_credentials(cfg["gcp_project"])
    if wif:
        write_ok(f"WIF credentials available (via {wif['source']})")
    else:
        write_warn("WIF credentials not found")

    services = ops.run_cmd(
        [
            "gcloud",
            "run",
            "services",
            "list",
            f"--project={cfg['gcp_project']}",
            f"--region={cfg['gcp_region']}",
            "--format=table(SERVICE,REGION,URL)",
        ]
    )
    if services.exit_code == 0 and services.stdout:
        print()
        print(services.stdout)
    print()


def new_mcp_claude_config(cfg: dict) -> None:
    mcp_dir = REPO_ROOT / "mcp"
    venv_python = mcp_dir / ".venv/bin/python"
    if sys.platform == "win32":
        venv_python = mcp_dir / ".venv/Scripts/python.exe"

    if not venv_python.exists():
        write_warn(f"MCP venv not found at {venv_python}")
        if confirm("Create venv and install MCP dependencies now?"):
            try:
                ops.generate_mcp_config(cfg)
                write_ok("MCP venv created")
            except RuntimeError as exc:
                write_err(str(exc))
                return
        else:
            return

    try:
        out_path = ops.generate_mcp_config(cfg)
    except RuntimeError as exc:
        write_err(str(exc))
        return

    write_ok(f"Wrote {out_path}")
    print()
    print("  Paste the contents into Claude Desktop → Settings → Developer → MCP")
    print("  Or merge 'goldenpath-local' into your existing MCP config.")
    print()
    print(out_path.read_text())
    print()


def reset_wizard_state() -> dict | None:
    print()
    print("  Resets .goldenpath-setup.local.json to defaults.")
    print("  Does NOT delete GCP projects, GitHub repos, or Cloud Run services.")
    print("  Use menu 13 to tear down the GCP sandbox if you want that too.")
    print()
    if not confirm("Reset local wizard state for a fresh start?"):
        return None
    fresh = ops.default_config()
    ops.save_config(fresh)
    write_ok(f"Wizard state reset — profile: sandbox, project: {fresh['gcp_project']}")
    print()
    print("  Next: option 1 (full guided setup) or --wizard")
    print()
    return fresh


def invoke_dryrun(cfg: dict) -> None:
    import goldenpath_dryrun as dryrun

    print()
    print("  Running read-only wizard audit (no GCP/GitHub changes)...")
    print()
    report = dryrun.run_dryrun(cfg)
    dryrun.print_dryrun_report(report)
    if report.blockers:
        write_warn("Dry run reported blockers — review before bootstrap or publish")


def invoke_teardown_sandbox(cfg: dict) -> None:
    err = ops.validate_project_id(cfg["gcp_project"])
    if err:
        write_err(f"Cannot tear down: {err}")
        return

    if not cfg.get("sandbox_disposable") and cfg.get("profile") != "sandbox":
        write_warn(f"Current profile '{cfg['profile']}' is not marked disposable.")
        if not confirm("Continue teardown anyway?"):
            return

    print()
    print("  This will DESTROY all Golden Path resources in:")
    print(f"    {cfg['gcp_project']}")
    print()
    print("  Steps: terraform destroy → delete GCP project (irreversible)")
    print("  Protected projects (PROTECTED_PROJECTS in enterprise.env) cannot be deleted.")
    print()

    if not confirm(f"Destroy bootstrap resources in '{cfg['gcp_project']}'?"):
        return
    delete_project = confirm(f"DELETE entire GCP project '{cfg['gcp_project']}'?")

    try:
        ops.teardown(delete_project)
    except Exception as exc:
        write_err(f"Teardown failed: {exc}")
        return

    write_ok(f"Sandbox '{cfg['gcp_project']}' torn down.")
    print("  Pick a new project in menu option 12 to stand up again.")


# ── Full wizard ───────────────────────────────────────────────────────────────


def show_wizard_completion(cfg: dict, state: dict) -> None:
    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║                    Setup wizard complete!                ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print()
    print("  What you set up:")
    print(
        f"    Profile        {cfg['profile']} → {cfg['gcp_project']} "
        f"({cfg['gcp_region']})"
    )
    if state.get("bootstrap_ran"):
        print("    Bootstrap      ✓ GCP project + Terraform + Artifact Registry")
    else:
        print("    Bootstrap      skipped — run menu 3 when ready")
    if cfg.get("wif_provider"):
        print("    WIF secrets    ✓ ready for GitHub Actions deploys")

    if state.get("service_name"):
        print(f"    Service        {state['service_name']} ({state['template']})")
        pub = state.get("publish")
        if state.get("published") and pub:
            print(f"    GitHub         https://github.com/{pub['repo']}")
            verify = state.get("verify")
            if verify and verify.url:
                print(f"    Cloud Run      {verify.url}")
                if verify.health_ok:
                    print(
                        f"    Health         {verify.health_path} → "
                        f"HTTP {verify.status_code}"
                    )
            elif pub.get("deploy_ok") is False:
                print("    Deploy         ✗ workflow failed — see Actions tab")
        elif not state.get("published"):
            print("    Publish        not yet — menu 7 when ready")
    else:
        print("    Service        none yet — menu 6 to scaffold")

    print()
    verify = state.get("verify")
    pub = state.get("publish")
    if verify and verify.url and verify.health_ok:
        print("  Your app is live. Open it now:")
        print(f"    {verify.url}")
        print()
        print("  To ship changes:")
        print(f"    cd {state['service_dir']}")
        print("    # edit your code, then:")
        print('    git add . && git commit -m "your change" && git push')
        print(
            f"    → GitHub Actions deploys to {pub['cloud_run_svc']} automatically"
        )
    elif pub and pub.get("deploy_ok") is False:
        print("  Next steps (deploy failed):")
        print(f"    1. Open https://github.com/{pub['repo']}/actions")
        print("    2. Fix the error, or run menu 9 (Doctor)")
        print("    3. Re-run menu 7 (Publish) to retry deploy + verify")
    elif state.get("service_name") and not state.get("published"):
        print("  Next step:")
        print(
            f"    Menu 7 — Publish {state['service_name']} to GitHub "
            "(repo + deploy + verify)"
        )
    elif not state.get("service_name"):
        print("  Next step:")
        print("    Menu 6 — Scaffold your first service, then menu 7 to publish")
    else:
        print("  Next step:")
        print("    Menu 8 — Verify deployment, or wait a minute and re-run publish")

    print()
    print("  Wizard menu:  python3 ./scripts/setup/goldenpath_setup.py")
    print("  All services: menu 11  |  Tear down sandbox: menu 13")
    print()


def start_full_wizard() -> None:
    write_banner()
    print("  This wizard walks you through Golden Path setup one step at a time.")
    print("  You can stop anytime and resume from the main menu.")
    print()

    cfg = ops.load_config()
    total = 6
    state: dict = {
        "bootstrap_ran": False,
        "service_name": "",
        "service_dir": "",
        "template": "",
        "published": False,
        "publish": None,
        "verify": None,
    }

    write_step(1, total, "Choose your profile")
    cfg = edit_config(cfg)

    write_step(2, total, "Check tools & login")
    if not test_prerequisites():
        write_err("Fix missing tools, then run the wizard again.")
        press_enter()
        return
    if not test_gcloud_auth():
        write_err("GCP auth required before continuing.")
        press_enter()
        return
    press_enter()

    write_step(3, total, "Bootstrap GCP (one-time)")
    print("  Creates the project (if needed) and runs Terraform bootstrap.")
    print(f"  Project: {cfg['gcp_project']} ({cfg['profile']})")
    if cfg.get("sandbox_disposable"):
        print("  Disposable — tear down later with menu option 13.")
    print("  Does not modify protected projects listed in config/enterprise.env.")
    print()
    if confirm("Run bootstrap now?"):
        state["bootstrap_ran"] = invoke_bootstrap_standup(cfg)
    else:
        write_warn("Skipped — you can run it later from the main menu (option 3).")
    cfg = ops.load_config()
    press_enter()

    write_step(4, total, "GitHub deploy credentials")
    show_wif_secrets(cfg)
    if confirm(
        f"Set WIF secrets on platform repo '{cfg['github_platform_repo']}' via gh?"
    ):
        set_github_secrets(cfg, cfg["github_platform_repo"])
    cfg = ops.load_config()
    press_enter()

    write_step(5, total, "Scaffold + publish your first service")
    print("  Creates a service folder, copies a template, publishes to GitHub,")
    print("  watches the deploy workflow, then verifies Cloud Run + health.")
    print()
    if confirm("Scaffold and publish a service now?"):
        scaffold = invoke_scaffold_service(cfg)
        if scaffold.get("service_name"):
            state.update(
                {
                    "service_name": scaffold["service_name"],
                    "service_dir": scaffold["service_dir"],
                    "template": scaffold["template"],
                    "published": scaffold["published"],
                    "publish": scaffold["publish"],
                    "verify": scaffold["verify"],
                }
            )
    else:
        print("  Skip for now — menu 6 (scaffold) and menu 7 (publish) later.")
    press_enter()

    write_step(6, total, "MCP for Claude (optional)")
    if confirm("Generate Claude MCP config?"):
        new_mcp_claude_config(cfg)
    else:
        print("  Skipped — menu 10 anytime.")

    show_wizard_completion(cfg, state)
    press_enter("Press Enter to return to the main menu...")


def show_main_menu() -> None:
    cfg = ops.load_config()

    while True:
        write_banner()
        print(
            f"  GCP: {cfg['gcp_project']}  |  "
            f"GitHub: {cfg['github_org']}/{cfg['github_platform_repo']}"
        )
        print()
        print("  What would you like to do?")
        print()
        print("    1) Full guided setup (recommended for new users)")
        print("    2) Check prerequisites")
        print("    3) Bootstrap GCP (stand up / terraform apply)")
        print("    4) Show GitHub WIF secrets")
        print("    5) Set GitHub WIF secrets on a repo")
        print("    6) Scaffold a new service (Python — not shop CLI)")
        print("    7) Publish service to GitHub (repo + secrets + deploy)")
        print("    8) Verify a deployment (health check)")
        print("    9) Doctor — diagnose deploy blockers")
        print("   10) Generate Claude MCP config")
        print("   11) Show current status")
        print("   12) Edit settings (project, org, region)")
        print("   13) Tear down current sandbox project")
        print("   14) Fresh start (reset local wizard state)")
        print("   15) Dry run — audit wizard (no deploy / no changes)")
        print("    h) Help / usage")
        print("    0) Exit")
        print()

        pick = read_input("Choice", "1").lower()

        if pick == "1":
            start_full_wizard()
        elif pick == "2":
            test_prerequisites()
            press_enter()
        elif pick == "3":
            if test_prerequisites() and test_gcloud_auth():
                invoke_bootstrap_standup(cfg)
            press_enter()
        elif pick == "4":
            show_wif_secrets(cfg)
            press_enter()
        elif pick == "5":
            repo = read_input("Repo (name or org/name)", cfg["github_platform_repo"])
            set_github_secrets(cfg, repo)
            press_enter()
        elif pick == "6":
            invoke_scaffold_service(cfg)
            press_enter()
        elif pick == "7":
            invoke_publish_service(cfg)
            press_enter()
        elif pick == "8":
            test_deployment(cfg)
            press_enter()
        elif pick == "9":
            invoke_service_doctor(cfg)
            press_enter()
        elif pick == "10":
            new_mcp_claude_config(cfg)
            press_enter()
        elif pick == "11":
            show_status(cfg)
            press_enter()
        elif pick == "12":
            cfg = edit_config(cfg)
            press_enter()
        elif pick == "13":
            invoke_teardown_sandbox(cfg)
            press_enter()
        elif pick == "14":
            reset = reset_wizard_state()
            if reset:
                cfg = reset
            press_enter()
        elif pick == "15":
            invoke_dryrun(cfg)
            press_enter()
        elif pick in ("h", "help", "?"):
            show_usage()
            press_enter()
        elif pick == "0":
            print("  Bye!")
            return
        else:
            write_warn("Unknown option — type h for help")

        cfg = ops.load_config()


def main() -> None:
    os.chdir(REPO_ROOT)
    args = sys.argv[1:]
    if "--help" in args or "-h" in args or "-?" in args:
        show_usage()
    elif "--wizard" in args:
        start_full_wizard()
    else:
        show_main_menu()


if __name__ == "__main__":
    main()
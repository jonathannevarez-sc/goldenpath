#!/usr/bin/env python3
"""Golden Path wizard dry-run — read-only audit of what each menu step would do.

No projects are created, terraform is not applied, and nothing is deployed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import goldenpath_ops as ops

REPO_ROOT = ops.REPO_ROOT
BOOTSTRAP_DIR = ops.BOOTSTRAP_DIR
ENTERPRISE_ENV = ops.ENTERPRISE_ENV


@dataclass
class DryRunFinding:
    level: str  # ok | warn | block
    message: str


@dataclass
class DryRunStep:
    menu: str
    title: str
    would_do: list[str] = field(default_factory=list)
    findings: list[DryRunFinding] = field(default_factory=list)


@dataclass
class DryRunReport:
    steps: list[DryRunStep] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ready_summary: list[str] = field(default_factory=list)
    next_menu: str = ""

    def add_finding(self, step: DryRunStep, level: str, message: str) -> None:
        step.findings.append(DryRunFinding(level=level, message=message))
        if level == "block":
            if message not in self.blockers:
                self.blockers.append(message)
        elif level == "warn":
            if message not in self.warnings:
                self.warnings.append(message)


def _parse_tfvars_project() -> str | None:
    tfvars = BOOTSTRAP_DIR / "terraform.tfvars"
    if not tfvars.exists():
        return None
    m = re.search(r'test_project_id\s*=\s*"([^"]+)"', tfvars.read_text())
    return m.group(1) if m else None


def _read_wif_from_state_files(project_id: str) -> dict | None:
    for name in ("terraform.tfstate", ".terraform/terraform.tfstate"):
        path = BOOTSTRAP_DIR / name
        if not path.exists():
            continue
        try:
            state = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        outputs = state.get("outputs") or {}
        provider = (outputs.get("dev_github_wif_provider_name") or {}).get("value")
        sa = (outputs.get("dev_github_actions_sa_email") or {}).get("value")
        if (
            provider
            and sa
            and ops.is_valid_wif_provider(str(provider))
            and ops.is_valid_wif_service_account(str(sa))
        ):
            return {
                "provider": str(provider).strip(),
                "service_account": str(sa).strip(),
                "source": f"state:{name}",
            }
    return None


def _gcloud_project_state(project_id: str) -> tuple[bool, str]:
    r = ops.run_cmd(
        [
            "gcloud",
            "projects",
            "describe",
            project_id,
            "--format=value(lifecycleState)",
        ]
    )
    if r.exit_code == 0 and r.stdout:
        return True, r.stdout.strip()
    return False, r.stderr or "not found"


def _gcloud_billing_enabled(project_id: str) -> bool | None:
    r = ops.run_cmd(
        [
            "gcloud",
            "billing",
            "projects",
            "describe",
            project_id,
            "--format=value(billingEnabled)",
        ]
    )
    if r.exit_code != 0:
        return None
    return r.stdout.strip() == "True"


def _gh_authenticated() -> bool:
    if not ops.cmd_available("gh"):
        return False
    r = ops.run_cmd(["gh", "auth", "status"])
    return r.exit_code == 0


def _gh_repo_exists(full_repo: str) -> bool | None:
    if not ops.cmd_available("gh"):
        return None
    r = ops.run_cmd(["gh", "api", f"repos/{full_repo}", "--jq", ".name"])
    return r.exit_code == 0 and bool(r.stdout.strip())


def run_dryrun(cfg: dict | None = None) -> DryRunReport:
    cfg = cfg or ops.load_config()
    report = DryRunReport()

    _LIB = REPO_ROOT / "scripts" / "lib"
    if str(_LIB) not in sys.path:
        sys.path.insert(0, str(_LIB))
    import wizard_defaults as wd  # noqa: E402

    env = wd.merged_enterprise_env(REPO_ROOT)
    project = cfg.get("gcp_dev_project") or cfg.get("gcp_project") or ""
    display = ops.normalize_project_display_name(
        cfg.get("project_display_name", ""),
        fallback=project or "Golden Path Sandbox",
    )

    # ── Menu 2: Prerequisites ─────────────────────────────────────────────
    prereq = DryRunStep("2", "Prerequisites (read-only check)")
    required = {
        "gcloud": "https://cloud.google.com/sdk/docs/install",
        "terraform": "https://developer.hashicorp.com/terraform/install",
        "git": "https://git-scm.com/",
        "gh": "https://cli.github.com/",
    }
    for tool, url in required.items():
        if ops.cmd_available(tool):
            prereq.findings.append(DryRunFinding("ok", f"{tool} found"))
        else:
            report.add_finding(
                prereq,
                "block",
                f"{tool} missing — install: {url}",
            )
    for opt in ("python3", "pwsh", "docker"):
        if ops.cmd_available(opt):
            prereq.findings.append(DryRunFinding("ok", f"{opt} found (optional)"))
    report.steps.append(prereq)

    # ── Config / enterprise.env ───────────────────────────────────────────
    config_step = DryRunStep("—", "Configuration")
    if ENTERPRISE_ENV.exists():
        config_step.findings.append(
            DryRunFinding("ok", f"enterprise.env present ({ENTERPRISE_ENV})")
        )
    else:
        report.add_finding(
            config_step,
            "block",
            "config/enterprise.env missing — copy config/enterprise.env.example",
        )

    for key in ("PARENT_PROJECT_ID", "BILLING_ACCOUNT_ID", "GITHUB_ORG"):
        if env.get(key):
            config_step.findings.append(DryRunFinding("ok", f"{key} set"))
        else:
            report.add_finding(config_step, "block", f"{key} not set in enterprise.env")

    if not env.get("ARTIFACT_REGISTRY_REPO"):
        report.add_finding(
            config_step,
            "block",
            "ARTIFACT_REGISTRY_REPO not set (required for bootstrap tfvars)",
        )
    else:
        config_step.findings.append(
            DryRunFinding("ok", f"ARTIFACT_REGISTRY_REPO={env['ARTIFACT_REGISTRY_REPO']}")
        )

    pid_err = ops.validate_project_id(project) if project else "No GCP project in wizard config"
    if pid_err:
        report.add_finding(config_step, "block", f"Project ID '{project}': {pid_err}")
    else:
        config_step.findings.append(DryRunFinding("ok", f"Project ID valid: {project}"))

    if len(display) > ops.GCP_PROJECT_DISPLAY_NAME_MAX:
        report.add_finding(
            config_step,
            "block",
            f"Display name too long ({len(display)} chars, max 30): {display}",
        )
    else:
        config_step.findings.append(
            DryRunFinding("ok", f"Display name OK ({len(display)} chars): {display}")
        )

    if project and project == env.get("PARENT_PROJECT_ID"):
        report.add_finding(
            config_step,
            "block",
            f"Sandbox project cannot equal PARENT_PROJECT_ID ({project})",
        )

    tfvars_project = _parse_tfvars_project()
    if tfvars_project and project and tfvars_project != project:
        report.add_finding(
            config_step,
            "warn",
            f"terraform.tfvars test_project_id='{tfvars_project}' "
            f"≠ wizard project '{project}' — re-bootstrap (menu 3) or edit menu 12",
        )
    report.steps.append(config_step)

    # ── GCP auth ──────────────────────────────────────────────────────────
    auth_step = DryRunStep("—", "GCP authentication (read-only)")
    if ops.cmd_available("gcloud"):
        acct = ops.run_cmd(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
        )
        if acct.exit_code == 0 and acct.stdout:
            auth_step.findings.append(DryRunFinding("ok", f"gcloud account: {acct.stdout}"))
        else:
            report.add_finding(auth_step, "block", "Not logged in to gcloud — run: gcloud auth login")

        adc = ops.run_cmd(["gcloud", "auth", "application-default", "print-access-token"])
        if adc.exit_code == 0:
            auth_step.findings.append(DryRunFinding("ok", "Application Default Credentials configured"))
        else:
            report.add_finding(
                auth_step,
                "warn",
                "ADC not configured — run: gcloud auth application-default login",
            )
    report.steps.append(auth_step)

    # ── Menu 3: Bootstrap ─────────────────────────────────────────────────
    boot = DryRunStep("3", "Bootstrap GCP (DRY RUN — would execute)")
    boot.would_do = [
        f"gcloud projects create {project} --name={display!r} (if project missing)",
        f"gcloud billing projects link {project} → billingAccounts/{env.get('BILLING_ACCOUNT_ID', '?')}",
        f"Write {BOOTSTRAP_DIR / 'terraform.tfvars'} (personal_test=true)",
        f"terraform init + apply in {BOOTSTRAP_DIR}",
        f"gcloud config set project {project}",
        "gcloud auth application-default set-quota-project",
    ]
    if project:
        exists, state = _gcloud_project_state(project)
        if exists:
            boot.findings.append(DryRunFinding("ok", f"GCP project exists ({state})"))
            boot.would_do[0] = f"Skip project create — {project} already exists"
            billing = _gcloud_billing_enabled(project)
            if billing is True:
                boot.findings.append(DryRunFinding("ok", "Billing already linked"))
                boot.would_do[1] = "Skip billing link — already enabled"
            elif billing is False:
                report.add_finding(boot, "warn", "Billing not linked — bootstrap would link billing")
            else:
                report.add_finding(boot, "warn", "Could not read billing state")
        else:
            report.add_finding(
                boot,
                "warn",
                f"GCP project '{project}' not found — bootstrap would create it",
            )

        ar = ops.run_cmd(
            [
                "gcloud",
                "artifacts",
                "repositories",
                "list",
                f"--project={project}",
                "--format=value(name)",
            ]
        )
        if ar.exit_code == 0 and ar.stdout.strip():
            boot.findings.append(DryRunFinding("ok", "Artifact Registry already present"))
            boot.would_do[-2] = "terraform apply (may update existing bootstrap resources)"
        else:
            report.add_finding(
                boot,
                "warn",
                "No Artifact Registry — bootstrap terraform apply would create it",
            )
    report.steps.append(boot)

    # ── Menu 4/5: WIF ─────────────────────────────────────────────────────
    wif_step = DryRunStep("4/5", "WIF secrets (DRY RUN — would set on GitHub repo)")
    wif_step.would_do = [
        "gh secret set GCP_WIF_PROVIDER on target repo",
        "gh secret set GCP_WIF_SERVICE_ACCOUNT on target repo",
        "On publish: add WIF trust binding for service repo",
    ]
    wif = _read_wif_from_state_files(project)
    if not wif and cfg.get("wif_provider") and cfg.get("wif_service_account"):
        if ops.is_valid_wif_provider(cfg["wif_provider"]) and ops.is_valid_wif_service_account(
            cfg["wif_service_account"]
        ):
            wif = {
                "provider": cfg["wif_provider"],
                "service_account": cfg["wif_service_account"],
                "source": "wizard-config",
            }
    if wif:
        wif_step.findings.append(
            DryRunFinding("ok", f"WIF available via {wif['source']}")
        )
        wif_step.findings.append(
            DryRunFinding("ok", f"Provider: {wif['provider'][:60]}...")
        )
    else:
        report.add_finding(
            wif_step,
            "block",
            "WIF credentials not found — run bootstrap (menu 3) then menu 4",
        )
    if not _gh_authenticated():
        report.add_finding(wif_step, "block", "gh not authenticated — run: gh auth login")
    report.steps.append(wif_step)

    # ── Menu 6: Scaffold ──────────────────────────────────────────────────
    scaffold = DryRunStep("6", "Scaffold service (DRY RUN — would execute)")
    out_dir = ops.get_scaffold_output_dir()
    svc_name = cfg.get("last_service") or "<service-name-you-enter>"
    scaffold.would_do = [
        f"Copy templates/<template>/ → {out_dir / svc_name}",
        "Replace {{TOKEN}} placeholders in all files",
        "Verify deploy.yml has no leftover {{TOKENS}}",
        "git init -b main && git add . && git commit (if git available)",
    ]
    if out_dir.exists() and out_dir.is_dir():
        scaffold.findings.append(DryRunFinding("ok", f"Scaffold parent writable: {out_dir}"))
    else:
        report.add_finding(scaffold, "block", f"Scaffold output parent missing: {out_dir}")

    svc_dir = ops.service_dir_for(cfg)
    if svc_dir and svc_dir.exists():
        scaffold.findings.append(DryRunFinding("ok", f"Last service dir: {svc_dir}"))
        broken = ops.test_deploy_workflow(svc_dir)
        if broken:
            report.add_finding(
                scaffold,
                "warn",
                f"deploy.yml has unreplaced tokens in {svc_dir.name} — publish would repair",
            )
        else:
            scaffold.findings.append(DryRunFinding("ok", "Last service deploy.yml tokens OK"))
    else:
        report.add_finding(
            scaffold,
            "warn",
            "No scaffolded service yet — menu 6 would create one",
        )
    report.steps.append(scaffold)

    # ── Menu 7: Publish ───────────────────────────────────────────────────
    publish = DryRunStep("7", "Publish service (DRY RUN — would execute)")
    if svc_dir and svc_dir.exists():
        svc_name = svc_dir.name
        full_repo = f"{cfg.get('github_org')}/{svc_name}"
        publish.would_do = [
            f"Repair scaffold tokens if deploy.yml broken",
            f"gh repo create {full_repo} (if missing)",
            f"Add WIF trust for {full_repo} on project {project}",
            f"git push origin main from {svc_dir}",
            "Trigger .github/workflows/deploy.yml (GitHub Actions → Cloud Run)",
            f"Cloud Run service name would be: {svc_name}-dev",
        ]
        if not (svc_dir / ".git").exists():
            report.add_finding(publish, "block", f"Not a git repo: {svc_dir} — run scaffold first")
        else:
            publish.findings.append(DryRunFinding("ok", "Service directory is a git repo"))

        repo_exists = _gh_repo_exists(full_repo)
        if repo_exists is True:
            publish.findings.append(DryRunFinding("ok", f"GitHub repo exists: {full_repo}"))
            publish.would_do[1] = f"Skip repo create — {full_repo} exists"
        elif repo_exists is False:
            report.add_finding(
                publish,
                "warn",
                f"GitHub repo {full_repo} not found — publish would create it",
            )

        if wif:
            publish.findings.append(DryRunFinding("ok", "WIF credentials ready for publish"))
        else:
            report.add_finding(publish, "block", "Publish blocked — WIF credentials missing")

        doctor_issues = []
        if svc_dir:
            try:
                doctor_issues = ops.service_doctor(svc_dir, cfg)
            except Exception as exc:
                report.add_finding(publish, "warn", f"Doctor check skipped: {exc}")
        hard = [
            i
            for i in doctor_issues
            if "Missing GitHub secret" not in i and "default branch" not in i
        ]
        for issue in hard:
            report.add_finding(publish, "warn", issue)
    else:
        publish.would_do = ["(no service directory — run menu 6 first)"]
        report.add_finding(publish, "warn", "No service to publish — scaffold first (menu 6)")
    report.steps.append(publish)

    # ── Menu 8: Verify ────────────────────────────────────────────────────
    verify = DryRunStep("8", "Verify deployment (DRY RUN — read-only)")
    cloud_run = f"{svc_name}-dev" if svc_name != "<service-name-you-enter>" else "<service>-dev"
    verify.would_do = [
        f"gcloud run services describe {cloud_run} --project={project}",
        "HTTP GET health endpoint on service URL",
    ]
    if project and ops.cmd_available("gcloud"):
        cr = ops.run_cmd(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                cloud_run,
                f"--project={project}",
                f"--region={cfg.get('gcp_region', 'us-central1')}",
                "--format=value(status.url)",
            ]
        )
        if cr.exit_code == 0 and cr.stdout:
            verify.findings.append(DryRunFinding("ok", f"Cloud Run URL: {cr.stdout}"))
        else:
            report.add_finding(
                verify,
                "warn",
                f"Cloud Run service '{cloud_run}' not found yet (normal before first deploy)",
            )
    report.steps.append(verify)

    # ── Menu 13: Teardown ─────────────────────────────────────────────────
    tear = DryRunStep("13", "Teardown sandbox (DRY RUN — would execute)")
    tear.would_do = [
        f"terraform destroy in {BOOTSTRAP_DIR}",
        f"Optionally: gcloud projects delete {tfvars_project or project}",
    ]
    if tfvars_project and project and tfvars_project != project:
        report.add_finding(
            tear,
            "block",
            f"Teardown would destroy '{tfvars_project}' but config says '{project}'",
        )
    if tfvars_project and tfvars_project in ops.protected_projects():
        report.add_finding(
            tear,
            "block",
            f"Refusing teardown — '{tfvars_project}' is in PROTECTED_PROJECTS",
        )
    if (BOOTSTRAP_DIR / "terraform.tfvars").exists():
        tear.findings.append(DryRunFinding("ok", "terraform.tfvars present for destroy"))
    else:
        report.add_finding(tear, "warn", "No terraform.tfvars — bootstrap never ran")
    report.steps.append(tear)

    # ── Summary ───────────────────────────────────────────────────────────
    if not report.blockers:
        report.ready_summary.append("No hard blockers — wizard can proceed step by step")
    if project and not _gcloud_project_state(project)[0]:
        report.next_menu = "3 (Bootstrap GCP)"
    elif not wif:
        report.next_menu = "3 then 4 (Bootstrap + WIF secrets)"
    elif not (svc_dir and svc_dir.exists()):
        report.next_menu = "6 (Scaffold a service)"
    elif _gh_repo_exists(f"{cfg.get('github_org')}/{svc_dir.name}") is False:
        report.next_menu = "7 (Publish service)"
    else:
        report.next_menu = "8 (Verify deployment) or 9 (Doctor)"

    return report


def print_dryrun_report(report: DryRunReport) -> None:
    icons = {"ok": "✓", "warn": "!", "block": "✗"}

    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║              Wizard dry run (no changes made)             ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print()
    print("  Read-only audit of prerequisites, config, and what each menu")
    print("  step WOULD do. Nothing is created, deployed, or deleted.")
    print()

    for step in report.steps:
        print(f"  ── Menu {step.menu}: {step.title} ──")
        for line in step.would_do:
            print(f"    → {line}")
        for f in step.findings:
            mark = icons.get(f.level, "·")
            color = {"ok": "", "warn": "!", "block": "✗"}.get(f.level, "")
            prefix = f"  {mark} " if mark else "    "
            print(f"{prefix}{f.message}")
        print()

    print("  ── Summary ──")
    if report.blockers:
        print("  ✗ Blockers (fix before running):")
        for b in report.blockers:
            print(f"      • {b}")
    else:
        print("  ✓ No hard blockers detected")
    if report.warnings:
        print("  ! Warnings:")
        for w in report.warnings:
            print(f"      • {w}")
    if report.next_menu:
        print(f"  → Suggested next step: menu {report.next_menu}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Golden Path wizard dry-run audit")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()
    cfg = ops.load_config()
    report = run_dryrun(cfg)

    if args.json:
        payload = {
            "blockers": report.blockers,
            "warnings": report.warnings,
            "next_menu": report.next_menu,
            "steps": [
                {
                    "menu": s.menu,
                    "title": s.title,
                    "would_do": s.would_do,
                    "findings": [{"level": f.level, "message": f.message} for f in s.findings],
                }
                for s in report.steps
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print_dryrun_report(report)

    return 1 if report.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""Reset local Golden Path wizard config (WIF cache, session state, optional tfvars)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wizard_defaults import (
    apply_enterprise_env_overrides,
    default_wizard_config,
    enterprise_env_path,
    find_repo_root,
    merged_enterprise_env,
)

WIZARD_CONFIG_NAME = ".goldenpath-setup.local.json"
BOOTSTRAP_TFVARS_PLACEHOLDER = """\
# Reset by scripts/reset-local-config.sh — set test_project_id before menu 3 bootstrap.
# Pick a globally unique ID in wizard menu 12 profile 2, then run menu 3.

personal_test        = true
test_project_id      = "REPLACE-ME-before-bootstrap"
region               = "{region}"
github_org           = "{github_org}"
github_repo          = "{platform_repo}"
artifact_registry_id = "{artifact_registry_repo}"
"""

SANDBOX_ENV_KEYS = (
    "GCP_SANDBOX_PROJECT",
    "GCP_DEV_PROJECT",
)


def _write_json(path: Path, data: dict, dry_run: bool) -> None:
    text = json.dumps(data, indent=2) + "\n"
    if dry_run:
        print(f"  would write {path}")
        return
    path.write_text(text)


def _clear_wif_in_config(cfg: dict) -> dict:
    cfg = dict(cfg)
    cfg["wif_provider"] = ""
    cfg["wif_service_account"] = ""
    return cfg


def _reset_wizard_config(repo_root: Path, dry_run: bool) -> Path:
    path = repo_root / WIZARD_CONFIG_NAME
    fresh = default_wizard_config(repo_root)
    apply_enterprise_env_overrides(fresh, repo_root)
    _write_json(path, fresh, dry_run)
    return path


def _wif_only(repo_root: Path, dry_run: bool) -> Path:
    path = repo_root / WIZARD_CONFIG_NAME
    if path.is_file():
        try:
            cfg = json.loads(path.read_text())
        except json.JSONDecodeError:
            cfg = default_wizard_config(repo_root)
    else:
        cfg = default_wizard_config(repo_root)
    cfg = _clear_wif_in_config(cfg)
    apply_enterprise_env_overrides(cfg, repo_root)
    _write_json(path, cfg, dry_run)
    return path


def _reset_tfvars(repo_root: Path, dry_run: bool) -> Path:
    env = merged_enterprise_env(repo_root)
    content = BOOTSTRAP_TFVARS_PLACEHOLDER.format(
        region=env.get("GCP_REGION", "us-central1"),
        github_org=env.get("GITHUB_ORG", "your-github-org"),
        platform_repo=env.get("PLATFORM_REPO", "goldenpath"),
        artifact_registry_repo=env.get("ARTIFACT_REGISTRY_REPO", "shop-services"),
    )
    path = repo_root / "platform/bootstrap/terraform.tfvars"
    if dry_run:
        print(f"  would write {path}")
        return path
    path.write_text(content)
    return path


def _clear_sandbox_in_enterprise_env(repo_root: Path, dry_run: bool) -> Path:
    path = enterprise_env_path(repo_root)
    if not path.is_file():
        raise FileNotFoundError(f"missing {path}")

    lines = path.read_text().splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        cleared = False
        for key in SANDBOX_ENV_KEYS:
            if re.match(rf"^\s*{re.escape(key)}=", line):
                out.append(f"{key}=\n")
                cleared = True
                break
        if not cleared:
            out.append(line)

    if dry_run:
        print(f"  would clear {', '.join(SANDBOX_ENV_KEYS)} in {path}")
        return path
    path.write_text("".join(out))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reset local Golden Path config (WIF cache, wizard JSON, optional bootstrap tfvars).",
        epilog="Does NOT delete GCP projects or run terraform destroy — use scripts/teardown-personal-test.sh for that.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--wif-only",
        action="store_true",
        help="Clear only wif_provider and wif_service_account in .goldenpath-setup.local.json",
    )
    mode.add_argument(
        "--full",
        action="store_true",
        help="Reset entire .goldenpath-setup.local.json to defaults (wizard menu 14 equivalent)",
    )
    parser.add_argument(
        "--tfvars",
        action="store_true",
        help="Reset platform/bootstrap/terraform.tfvars to a placeholder (stale bootstrap project ID)",
    )
    parser.add_argument(
        "--clear-sandbox-env",
        action="store_true",
        help="Clear GCP_SANDBOX_PROJECT and GCP_DEV_PROJECT in config/enterprise.env",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="--full + --tfvars + --clear-sandbox-env",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would change")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    args = parser.parse_args()

    repo_root = find_repo_root()
    do_full = args.full or args.all or (not args.wif_only and not args.tfvars and not args.clear_sandbox_env)
    do_tfvars = args.tfvars or args.all
    do_clear_env = args.clear_sandbox_env or args.all
    do_wif_only = args.wif_only and not args.all

    if not args.yes and not args.dry_run:
        print("This resets LOCAL files only (no GCP teardown).")
        if do_wif_only:
            print("  · Clear WIF cache in .goldenpath-setup.local.json")
        elif do_full:
            print("  · Reset .goldenpath-setup.local.json to defaults")
        if do_tfvars:
            print("  · Reset platform/bootstrap/terraform.tfvars placeholder")
        if do_clear_env:
            print("  · Clear sandbox project IDs in config/enterprise.env")
        try:
            ans = input("Continue? [y/N] ").strip().lower()
        except EOFError:
            ans = "n"
        if ans not in ("y", "yes"):
            print("Aborted.")
            return 0

    print(f"Repo: {repo_root}")
    changed: list[str] = []

    if do_wif_only:
        p = _wif_only(repo_root, args.dry_run)
        changed.append(f"WIF cache cleared → {p.name}")
    elif do_full:
        p = _reset_wizard_config(repo_root, args.dry_run)
        changed.append(f"Wizard config reset → {p.name}")

    if do_tfvars:
        p = _reset_tfvars(repo_root, args.dry_run)
        changed.append(f"Bootstrap tfvars placeholder → {p.relative_to(repo_root)}")

    if do_clear_env:
        p = _clear_sandbox_in_enterprise_env(repo_root, args.dry_run)
        changed.append(f"Sandbox env cleared → {p.relative_to(repo_root)}")

    if not changed:
        print("Nothing to do.")
        return 0

    prefix = "Would reset:" if args.dry_run else "Reset:"
    for line in changed:
        print(f"  ✓ {prefix} {line}")

    if not args.dry_run:
        print()
        print("Next: wizard menu 12 (pick project) → menu 3 bootstrap → menu 4 WIF secrets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
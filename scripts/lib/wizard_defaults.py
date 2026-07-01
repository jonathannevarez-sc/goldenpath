#!/usr/bin/env python3
"""Wizard and platform defaults from config/enterprise.env (+ example fallbacks)."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__).resolve()).parent
    for _ in range(8):
        if (current / "templates" / "catalog.json").is_file():
            return current
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path(__file__).resolve().parent.parent.parent


def parse_env_file(path: Path) -> dict[str, str]:
    profile: dict[str, str] = {}
    if not path.is_file():
        return profile
    for line in path.read_text().splitlines():
        m = re.match(r"^\s*([A-Z_]+)=(.*)$", line)
        if m:
            profile[m.group(1)] = m.group(2).strip().strip('"')
    return profile


def enterprise_env_path(repo_root: Path) -> Path:
    override = os.environ.get("GOLDENPATH_CONFIG")
    if override:
        return Path(override)
    return repo_root / "config" / "enterprise.env"


def enterprise_example_path(repo_root: Path) -> Path:
    return repo_root / "config" / "enterprise.env.example"


def merged_enterprise_env(repo_root: Path | None = None) -> dict[str, str]:
    """Example defaults overlaid by enterprise.env when present."""
    root = repo_root or find_repo_root()
    merged = parse_env_file(enterprise_example_path(root))
    local = parse_env_file(enterprise_env_path(root))
    merged.update(local)
    return merged


def platform_default(key: str, repo_root: Path | None = None) -> str:
    return merged_enterprise_env(repo_root).get(key, "")


def resolve_goldenpath_version(repo_root: Path | None = None) -> str:
    """Canonical platform tag for workflow/module pins — always from enterprise.env."""
    return platform_default("GOLDENPATH_VERSION", repo_root)


# Keys owned by enterprise.env — stale wizard JSON must never override these.
_ENTERPRISE_OWNED_KEYS = (
    "goldenpath_version",
    "github_org",
    "github_platform_repo",
    "gcp_dev_project",
    "gcp_prod_project",
    "gcp_region",
)


def apply_enterprise_env_overrides(cfg: dict, repo_root: Path | None = None) -> dict:
    """Force team-owned settings from enterprise.env (single source of truth)."""
    env = merged_enterprise_env(repo_root)
    mapping = {
        "goldenpath_version": "GOLDENPATH_VERSION",
        "github_org": "GITHUB_ORG",
        "github_platform_repo": "PLATFORM_REPO",
        "gcp_dev_project": "GCP_DEV_PROJECT",
        "gcp_prod_project": "GCP_PROD_PROJECT",
        "gcp_region": "GCP_REGION",
    }
    for cfg_key, env_key in mapping.items():
        val = env.get(env_key, "")
        if val:
            cfg[cfg_key] = val
    sandbox = env.get("GCP_SANDBOX_PROJECT") or cfg.get("gcp_dev_project", "")
    if sandbox and cfg.get("profile") == "sandbox":
        cfg["gcp_project"] = sandbox
    return cfg


def protected_project_ids(repo_root: Path | None = None) -> frozenset[str]:
    root = repo_root or find_repo_root()
    csv = merged_enterprise_env(root).get("PROTECTED_PROJECTS", "")
    return frozenset(p.strip() for p in csv.split(",") if p.strip())


def default_wizard_config(repo_root: Path | None = None) -> dict:
    root = repo_root or find_repo_root()
    env = merged_enterprise_env(root)

    sandbox = env.get("GCP_SANDBOX_PROJECT") or env.get("GCP_DEV_PROJECT") or ""
    dev = env.get("GCP_DEV_PROJECT") or sandbox
    prod = env.get("GCP_PROD_PROJECT") or dev

    return {
        "profile": "sandbox",
        "gcp_project": sandbox,
        "project_display_name": env.get("SANDBOX_PROJECT_NAME", ""),
        "gcp_region": env.get("GCP_REGION", ""),
        "github_org": env.get("GITHUB_ORG", ""),
        "github_platform_repo": env.get("PLATFORM_REPO", ""),
        "goldenpath_version": env.get("GOLDENPATH_VERSION", ""),
        "gcp_dev_project": dev,
        "gcp_prod_project": prod,
        "sandbox_disposable": True,
        "wif_provider": "",
        "wif_service_account": "",
        "last_service": "",
        "last_service_dir": "",
    }


def _valid_wif_provider(value: str) -> bool:
    if not value or "Warning:" in value:
        return False
    return bool(
        re.match(
            r"^projects/\d+/locations/global/workloadIdentityPools/[^/]+/providers/",
            value.strip(),
        )
    )


def _valid_wif_service_account(value: str) -> bool:
    if not value or "Warning:" in value:
        return False
    return bool(
        re.match(
            r"^github-actions@[a-z][a-z0-9-]+\.iam\.gserviceaccount\.com$",
            value.strip(),
        )
    )


def merge_saved_config(
    config_path: Path,
    repo_root: Path | None = None,
) -> dict:
    defaults = default_wizard_config(repo_root)
    if not config_path.is_file():
        return defaults
    try:
        saved = json.loads(config_path.read_text())
        for key in defaults:
            val = saved.get(key)
            if val is None:
                continue
            if isinstance(defaults[key], bool):
                defaults[key] = bool(val)
            elif str(val):
                defaults[key] = val
    except Exception:
        pass

    provider = defaults.get("wif_provider", "")
    sa = defaults.get("wif_service_account", "")
    if (provider and not _valid_wif_provider(provider)) or (
        sa and not _valid_wif_service_account(sa)
    ):
        defaults["wif_provider"] = ""
        defaults["wif_service_account"] = ""
        config_path.write_text(json.dumps(defaults, indent=2))

    apply_enterprise_env_overrides(defaults, repo_root)
    return defaults


def _sh_escape(value: str) -> str:
    return str(value).replace("'", "'\"'\"'")


def shell_exports(cfg: dict) -> None:
    for key, val in cfg.items():
        env_key = f"WIZ_{key.upper()}"
        if isinstance(val, bool):
            print(f"export {env_key}={'true' if val else 'false'}")
        else:
            print(f"export {env_key}='{_sh_escape(val)}'")


def main() -> None:
    root = find_repo_root()
    config_path = root / ".goldenpath-setup.local.json"

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--protected":
            print(json.dumps(sorted(protected_project_ids(root))))
            return
        if arg == "--platform-default":
            print(platform_default(sys.argv[2], root) if len(sys.argv) > 2 else "")
            return
        if arg == "--shell-exports":
            shell_exports(default_wizard_config(root))
            return
        if arg == "--merge-shell":
            shell_exports(merge_saved_config(config_path, root))
            return
        if arg == "--merge":
            print(json.dumps(merge_saved_config(config_path, root), indent=2))
            return
        if arg == "--merged-env":
            print(json.dumps(merged_enterprise_env(root), indent=2))
            return

    print(json.dumps(default_wizard_config(root), indent=2))


if __name__ == "__main__":
    main()
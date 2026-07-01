"""Cross-check validators shared between Python wizard and bash CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import goldenpath_ops as ops

REPO_ROOT = Path(__file__).resolve().parent.parent


def _bash_validate_project_id(
    project_id: str, *, protected: str = "", config_dir: Path | None = None
) -> int:
    env = {"REPO_ROOT": str(REPO_ROOT)}
    if protected:
        base = config_dir or REPO_ROOT / "tests"
        base.mkdir(parents=True, exist_ok=True)
        config = base / ".tmp-enterprise.env"
        config.write_text(
            "\n".join(
                [
                    "PARENT_PROJECT_ID=billing-anchor-test",
                    "BILLING_ACCOUNT_ID=000000-000000-000000",
                    "GITHUB_ORG=test-org",
                    f"PROTECTED_PROJECTS={protected}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        env["GOLDENPATH_CONFIG"] = str(config)
    script = f"""
source "{REPO_ROOT}/scripts/lib/scaffold-tokens.sh"
validate_gcp_project_id "{project_id}"
"""
    result = subprocess.run(["bash", "-c", script], env={**dict(__import__("os").environ), **env})
    return result.returncode


def test_valid_project_ids_agree() -> None:
    for project_id in ("my-valid-project", "sandbox-test-01"):
        assert ops.validate_project_id(project_id) is None
        assert _bash_validate_project_id(project_id) == 0


def test_invalid_project_ids_agree() -> None:
    for project_id in ("abc", "1bad-project", "valid-project-", "my--bad"):
        assert ops.validate_project_id(project_id) is not None
        assert _bash_validate_project_id(project_id) != 0


def test_protected_project_ids_agree(tmp_path: Path) -> None:
    # Bash path with explicit protected list must reject
    assert _bash_validate_project_id("protected-a", protected="protected-a", config_dir=tmp_path) != 0
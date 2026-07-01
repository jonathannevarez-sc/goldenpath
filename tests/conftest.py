"""Shared pytest fixtures for Golden Path platform tests."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_LIB = REPO_ROOT / "scripts" / "lib"
SCRIPTS_SETUP = REPO_ROOT / "scripts" / "setup"
MCP_ROOT = REPO_ROOT / "mcp"

for path in (SCRIPTS_LIB, SCRIPTS_SETUP, MCP_ROOT):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Minimal fake repo layout for isolated config/script tests."""
    root = tmp_path / "goldenpath"
    (root / "templates").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "docs" / "getting-started").mkdir(parents=True)
    (root / "skills" / "test-skill").mkdir(parents=True)
    (root / "scripts" / "lib").mkdir(parents=True)

    shutil.copy(REPO_ROOT / "templates" / "catalog.json", root / "templates" / "catalog.json")
    shutil.copy(
        REPO_ROOT / "config" / "enterprise.env.example",
        root / "config" / "enterprise.env.example",
    )
    shutil.copy(REPO_ROOT / "scripts" / "lib" / "wizard_defaults.py", root / "scripts" / "lib" / "wizard_defaults.py")
    shutil.copy(
        REPO_ROOT / "docs" / "getting-started" / "01-start-here.md",
        root / "docs" / "getting-started" / "01-start-here.md",
    )
    (root / "skills" / "test-skill" / "SKILL.md").write_text("# Test skill\n", encoding="utf-8")

    return root


@pytest.fixture
def sample_enterprise_env(temp_repo: Path) -> Path:
    path = temp_repo / "config" / "enterprise.env"
    path.write_text(
        "\n".join(
            [
                "PARENT_PROJECT_ID=billing-anchor-test",
                "BILLING_ACCOUNT_ID=000000-000000-000000",
                "GCP_DEV_PROJECT=my-gp-dev-test",
                "GCP_PROD_PROJECT=my-gp-prod-test",
                "GCP_SANDBOX_PROJECT=my-gp-sandbox-test",
                "GCP_REGION=us-central1",
                "GITHUB_ORG=my-github-org",
                "PLATFORM_REPO=goldenpath",
                "GOLDENPATH_VERSION=v0.3.7",
                "PROTECTED_PROJECTS=protected-name-test,billing-anchor-test",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _replace_scaffold_tokens(
    dest: Path,
    *,
    service: str = "my-fastapi-service",
    org: str = "test-org",
    platform_repo: str = "goldenpath",
    dev_project: str = "my-valid-project",
    prod_project: str = "my-valid-project",
    region: str = "us-central1",
    app_runtime: str = "python",
    health_path: str = "/api/health",
    container_port: str = "8000",
    goldenpath_version: str = "v0.3.7",
    artifact_registry_repo: str = "shop-services",
) -> None:
    """Mirror scripts/lib/scaffold-tokens.sh replace_tokens for test fixtures."""
    import re

    replacements = {
        "{{SERVICE_NAME}}": service,
        "{{GITHUB_ORG}}": org,
        "{{PLATFORM_REPO}}": platform_repo,
        "{{GOLDENPATH_VERSION}}": goldenpath_version,
        "{{GCP_DEV_PROJECT}}": dev_project,
        "{{GCP_PROD_PROJECT}}": prod_project,
        "{{GCP_REGION}}": region,
        "{{APP_RUNTIME}}": app_runtime,
        "{{HEALTH_CHECK_PATH}}": health_path,
        "{{CONTAINER_PORT}}": container_port,
        "{{ARTIFACT_REGISTRY_REPO}}": artifact_registry_repo,
    }
    skip_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache"}
    token_re = re.compile(r"\{\{[A-Z_]+\}\}")
    for path in dest.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not token_re.search(text):
            continue
        for token, value in replacements.items():
            text = text.replace(token, value)
        path.write_text(text, encoding="utf-8")


@pytest.fixture
def valid_service_dir(tmp_path: Path) -> Path:
    """Copy fastapi template with scaffold tokens fully replaced."""
    src = REPO_ROOT / "templates" / "fastapi"
    dest = tmp_path / "my-fastapi-service"
    shutil.copytree(src, dest)
    _replace_scaffold_tokens(dest)
    return dest


@pytest.fixture
def wizard_config_path(temp_repo: Path) -> Path:
    return temp_repo / ".goldenpath-setup.local.json"
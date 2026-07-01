"""Tier 2: live sandbox deploy-spine acceptance (GitHub + GCP).

Required for enterprise release gates. CI provides secrets via
.github/workflows/integration-tests.yml — not optional for production promotion.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SHOP = REPO_ROOT / "cli" / "shop"

REQUIRED_ENV = (
    "INTEGRATION_TEST_ENABLED",
    "SHOP_GITHUB_ORG",
    "SHOP_GCP_DEV_PROJECT",
    "GCP_REGION",
    "GH_TOKEN",
)


def _integration_ready() -> bool:
    if os.getenv("INTEGRATION_TEST_ENABLED", "").lower() not in ("1", "true", "yes"):
        return False
    for key in REQUIRED_ENV[1:]:
        if not os.getenv(key):
            return False
    return shutil.which("gh") is not None and shutil.which("gcloud") is not None


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def require_integration() -> None:
    missing = [k for k in REQUIRED_ENV if k != "INTEGRATION_TEST_ENABLED" and not os.getenv(k)]
    if os.getenv("INTEGRATION_TEST_ENABLED", "").lower() not in ("1", "true", "yes"):
        pytest.fail(
            "Tier 2 integration tests require INTEGRATION_TEST_ENABLED=1 in enterprise CI. "
            "See tests/README.md § Release acceptance."
        )
    if missing:
        pytest.fail(f"Tier 2 integration missing required env: {', '.join(missing)}")
    if not shutil.which("gh") or not shutil.which("gcloud"):
        pytest.fail("Tier 2 integration requires gh and gcloud on PATH")


def test_sandbox_publish_verify_smoke(require_integration: None, tmp_path_factory: pytest.TempPathFactory) -> None:
    """End-to-end: scaffold → publish → verify on enterprise sandbox project."""
    work = tmp_path_factory.mktemp("integration")
    service = "gp-integ-smoke"
    env = os.environ.copy()
    env.setdefault("SHOP_GCP_PROD_PROJECT", env["SHOP_GCP_DEV_PROJECT"])
    env.setdefault("SHOP_GCP_REGION", env.get("GCP_REGION", "us-central1"))
    env.setdefault("SHOP_GOLDENPATH_REPO", "goldenpath")
    env.setdefault("SHOP_GOLDENPATH_VERSION", "v0.3.7")

    subprocess.run(
        [str(SHOP), "new", service, "--template", "fastapi", "--output", str(work)],
        check=True,
        env=env,
        cwd=REPO_ROOT,
    )
    svc_dir = work / service
    assert (svc_dir / ".github/workflows/deploy.yml").is_file()

    subprocess.run(
        [str(SHOP), "doctor", str(svc_dir)],
        check=True,
        env=env,
        cwd=REPO_ROOT,
    )

    # Publish + verify exercise live GitHub and Cloud Run — enterprise CI only.
    subprocess.run(
        [str(SHOP), "publish", str(svc_dir), "--no-watch"],
        check=True,
        env=env,
        cwd=REPO_ROOT,
        timeout=600,
    )
    subprocess.run(
        [str(SHOP), "verify", str(svc_dir)],
        check=True,
        env=env,
        cwd=REPO_ROOT,
        timeout=300,
    )
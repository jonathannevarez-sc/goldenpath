"""Tests for scripts/setup/goldenpath_ops.py pure functions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import goldenpath_ops as ops
from helpers import write_json

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestValidateProjectId:
    def test_rejects_protected_project(
        self,
        temp_repo: Path,
        sample_enterprise_env: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(ops, "REPO_ROOT", temp_repo)
        monkeypatch.setenv("GOLDENPATH_CONFIG", str(sample_enterprise_env))
        err = ops.validate_project_id("protected-name-test")
        assert err is not None
        assert "protected" in err.lower()

    @pytest.mark.parametrize(
        "project_id",
        ["my-valid-project", "my-gp-sandbox-test"],
    )
    def test_accepts_valid_ids(self, project_id: str) -> None:
        assert ops.validate_project_id(project_id) is None

    @pytest.mark.parametrize(
        ("project_id", "fragment"),
        [
            ("abc", "6–30"),
            ("a" * 31, "6–30"),
            ("1myproject", "letter"),
            ("valid-project-", "hyphen"),
            ("my--bad", "consecutive"),
        ],
    )
    def test_rejects_invalid_ids(self, project_id: str, fragment: str) -> None:
        err = ops.validate_project_id(project_id)
        assert err is not None
        assert fragment in err


class TestValidateServiceName:
    def test_accepts_valid_names(self) -> None:
        assert ops.validate_service_name("my-streamlit-app") is None
        assert ops.validate_service_name("fastapi-backend") is None

    def test_rejects_invalid_names(self) -> None:
        assert ops.validate_service_name("ab") is not None
        assert ops.validate_service_name("a" * 41) is not None
        assert ops.validate_service_name("my--app") is not None
        assert ops.validate_service_name("123-service") is not None


class TestWifValidation:
    def test_valid_wif_provider(self) -> None:
        provider = (
            "projects/123456789/locations/global/workloadIdentityPools/"
            "github-pool/providers/github"
        )
        assert ops.is_valid_wif_provider(provider) is True

    def test_invalid_wif_provider(self) -> None:
        assert ops.is_valid_wif_provider("Warning: No outputs found") is False
        assert ops.is_valid_wif_provider("") is False

    def test_valid_wif_service_account(self) -> None:
        sa = "github-actions@my-gp-sandbox-test.iam.gserviceaccount.com"
        assert ops.is_valid_wif_service_account(sa) is True

    def test_wif_credentials_stale(self) -> None:
        cfg = {
            "gcp_dev_project": "new-project-123",
            "wif_service_account": "github-actions@old-project-999.iam.gserviceaccount.com",
        }
        assert ops.wif_credentials_stale(cfg) is True

        cfg["wif_service_account"] = "github-actions@new-project-123.iam.gserviceaccount.com"
        assert ops.wif_credentials_stale(cfg) is False

        cfg = {
            "gcp_dev_project": "my-project",
            "wif_provider": "Warning: No outputs found",
            "wif_service_account": "",
        }
        assert ops.wif_credentials_stale(cfg) is True


class TestConfigPersistence:
    def test_load_and_save_config(
        self,
        temp_repo: Path,
        sample_enterprise_env: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config_path = temp_repo / ".goldenpath-setup.local.json"
        monkeypatch.setattr(ops, "REPO_ROOT", temp_repo)
        monkeypatch.setattr(ops, "CONFIG_PATH", config_path)
        monkeypatch.setenv("GOLDENPATH_CONFIG", str(sample_enterprise_env))

        defaults = ops.default_config()
        assert defaults["gcp_project"] == "my-gp-sandbox-test"

        defaults["last_service"] = "demo-service"
        defaults["sandbox_disposable"] = False
        ops.save_config(defaults)

        loaded = ops.load_config()
        assert loaded["last_service"] == "demo-service"
        assert loaded["sandbox_disposable"] is False


class TestWizardCli:
    def test_python_wizard_help(self) -> None:
        script = REPO_ROOT / "scripts" / "setup" / "goldenpath_setup.py"
        out = subprocess.check_output(
            [sys.executable, str(script), "--help"],
            text=True,
            stderr=subprocess.STDOUT,
        )
        assert "Python Wizard" in out
        assert "--wizard" in out
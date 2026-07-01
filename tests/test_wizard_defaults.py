"""Tests for scripts/lib/wizard_defaults.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import wizard_defaults as wd
from helpers import write_json


class TestParseEnvFile:
    def test_parses_key_value_pairs(self, tmp_path: Path) -> None:
        env = tmp_path / "test.env"
        env.write_text(
            'FOO=bar\n# comment\nBAR="quoted"\n',
            encoding="utf-8",
        )
        assert wd.parse_env_file(env) == {"FOO": "bar", "BAR": "quoted"}

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert wd.parse_env_file(tmp_path / "missing.env") == {}


class TestMergedEnterpriseEnv:
    def test_example_only_when_no_local(self, temp_repo: Path) -> None:
        merged = wd.merged_enterprise_env(temp_repo)
        assert merged["GITHUB_ORG"] == "your-github-org"
        assert merged["GCP_REGION"] == "us-central1"

    def test_local_overrides_example(
        self, temp_repo: Path, sample_enterprise_env: Path
    ) -> None:
        merged = wd.merged_enterprise_env(temp_repo)
        assert merged["GITHUB_ORG"] == "my-github-org"
        assert merged["GCP_SANDBOX_PROJECT"] == "my-gp-sandbox-test"


class TestProtectedProjects:
    def test_returns_frozenset_from_csv(
        self, temp_repo: Path, sample_enterprise_env: Path
    ) -> None:
        protected = wd.protected_project_ids(temp_repo)
        assert protected == frozenset({"protected-name-test", "billing-anchor-test"})


class TestDefaultWizardConfig:
    def test_sandbox_defaults(
        self, temp_repo: Path, sample_enterprise_env: Path
    ) -> None:
        cfg = wd.default_wizard_config(temp_repo)
        assert cfg["profile"] == "sandbox"
        assert cfg["gcp_project"] == "my-gp-sandbox-test"
        assert cfg["gcp_dev_project"] == "my-gp-dev-test"
        assert cfg["gcp_prod_project"] == "my-gp-prod-test"
        assert cfg["sandbox_disposable"] is True


class TestMergeSavedConfig:
    def test_returns_defaults_when_missing(
        self, temp_repo: Path, sample_enterprise_env: Path, wizard_config_path: Path
    ) -> None:
        cfg = wd.merge_saved_config(wizard_config_path, temp_repo)
        assert cfg["gcp_project"] == "my-gp-sandbox-test"

    def test_roundtrips_saved_values(
        self, temp_repo: Path, sample_enterprise_env: Path, wizard_config_path: Path
    ) -> None:
        write_json(
            wizard_config_path,
            {
                "profile": "sandbox",
                "gcp_dev_project": "saved-dev-project",
                "sandbox_disposable": False,
                "last_service": "my-service",
            },
        )
        cfg = wd.merge_saved_config(wizard_config_path, temp_repo)
        assert cfg["gcp_dev_project"] == "my-gp-dev-test"
        assert cfg["sandbox_disposable"] is False
        assert cfg["last_service"] == "my-service"

    def test_resolve_goldenpath_version_from_enterprise_env(
        self, temp_repo: Path, sample_enterprise_env: Path
    ) -> None:
        assert wd.resolve_goldenpath_version(temp_repo) == "v0.3.8"

    def test_apply_enterprise_env_overrides_github_org(
        self, temp_repo: Path, sample_enterprise_env: Path
    ) -> None:
        cfg = {"github_org": "stale-org", "goldenpath_version": "v0.3.0"}
        wd.apply_enterprise_env_overrides(cfg, temp_repo)
        assert cfg["github_org"] == "my-github-org"
        assert cfg["goldenpath_version"] == "v0.3.8"

    def test_enterprise_env_wins_for_goldenpath_version(
        self, temp_repo: Path, sample_enterprise_env: Path, wizard_config_path: Path
    ) -> None:
        # enterprise.env already pins v0.3.8 via conftest fixture
        write_json(
            wizard_config_path,
            {"goldenpath_version": "v0.3.0", "last_service": "stale"},
        )
        cfg = wd.merge_saved_config(wizard_config_path, temp_repo)
        assert cfg["goldenpath_version"] == "v0.3.8"
        assert cfg["last_service"] == "stale"

    def test_strips_invalid_wif_values(
        self, temp_repo: Path, sample_enterprise_env: Path, wizard_config_path: Path
    ) -> None:
        write_json(
            wizard_config_path,
            {
                "wif_provider": "Warning: No outputs found",
                "wif_service_account": "github-actions@my-gp-dev-test.iam.gserviceaccount.com",
            },
        )
        cfg = wd.merge_saved_config(wizard_config_path, temp_repo)
        assert cfg["wif_provider"] == ""
        assert cfg["wif_service_account"] == ""
        saved = json.loads(wizard_config_path.read_text())
        assert saved["wif_provider"] == ""
        assert saved["wif_service_account"] == ""


class TestCli:
    def test_platform_default_flag(
        self, temp_repo: Path, sample_enterprise_env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(temp_repo)
        monkeypatch.setenv("GOLDENPATH_CONFIG", str(sample_enterprise_env))
        script = REPO_ROOT / "scripts" / "lib" / "wizard_defaults.py"
        out = subprocess.check_output(
            [sys.executable, str(script), "--platform-default", "GITHUB_ORG"],
            text=True,
        ).strip()
        assert out == "my-github-org"

    def test_protected_flag(
        self, temp_repo: Path, sample_enterprise_env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(temp_repo)
        monkeypatch.setenv("GOLDENPATH_CONFIG", str(sample_enterprise_env))
        script = REPO_ROOT / "scripts" / "lib" / "wizard_defaults.py"
        out = subprocess.check_output(
            [sys.executable, str(script), "--protected"],
            text=True,
        )
        data = json.loads(out)
        assert data == ["billing-anchor-test", "protected-name-test"]

    def test_shell_exports(
        self, temp_repo: Path, sample_enterprise_env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(temp_repo)
        monkeypatch.setenv("GOLDENPATH_CONFIG", str(sample_enterprise_env))
        script = REPO_ROOT / "scripts" / "lib" / "wizard_defaults.py"
        out = subprocess.check_output(
            [sys.executable, str(script), "--shell-exports"],
            text=True,
        )
        assert "export WIZ_PROFILE='sandbox'" in out
        assert "export WIZ_GCP_PROJECT='my-gp-sandbox-test'" in out
        assert "export WIZ_SANDBOX_DISPOSABLE=true" in out


REPO_ROOT = Path(__file__).resolve().parent.parent
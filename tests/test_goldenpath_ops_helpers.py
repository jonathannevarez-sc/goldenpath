"""Tests for additional pure helpers in scripts/setup/goldenpath_ops.py."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import goldenpath_ops as ops


class TestNormalizeProjectDisplayName:
    def test_short_name_unchanged(self) -> None:
        assert ops.normalize_project_display_name("Golden Path Sandbox") == (
            "Golden Path Sandbox"
        )

    def test_truncates_long_default(self) -> None:
        long_name = "Golden Path Sandbox gp-sandbox-20260624"
        assert len(ops.normalize_project_display_name(long_name)) == 30
        assert ops.normalize_project_display_name(long_name) == long_name[:30]

    def test_falls_back_to_project_id(self) -> None:
        assert ops.normalize_project_display_name("", fallback="gp-sandbox-20260624") == (
            "gp-sandbox-20260624"
        )


class TestRepairScaffoldTokens:
    def test_repairs_broken_deploy_yml(
        self, temp_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        shutil.copytree(
            ops.REPO_ROOT / "templates" / "express",
            temp_repo / "templates" / "express",
        )
        monkeypatch.setattr(ops, "REPO_ROOT", temp_repo)
        cfg = ops.default_config()
        cfg.update(
            {
                "github_org": "test-org",
                "github_platform_repo": "goldenpath",
                "gcp_dev_project": "gp-test-repair",
                "gcp_prod_project": "gp-test-repair",
                "gcp_region": "us-central1",
            }
        )
        result = ops.scaffold(
            "repair-svc", "express", temp_repo / "out", cfg
        )
        deploy = result.service_dir / ".github/workflows/deploy.yml"
        deploy.write_text(
            deploy.read_text().replace("repair-svc", "{{SERVICE_NAME}}")
        )
        ops.repair_scaffold_tokens(result.service_dir, "express", cfg)
        text = deploy.read_text()
        assert "{{SERVICE_NAME}}" not in text
        assert "uses:" in text


class TestUpgradePlatformPins:
    def test_bumps_stale_workflow_tag(
        self, temp_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        shutil.copytree(
            ops.REPO_ROOT / "templates" / "fastapi",
            temp_repo / "templates" / "fastapi",
        )
        monkeypatch.setattr(ops, "REPO_ROOT", temp_repo)
        cfg = ops.default_config()
        cfg.update(
            {
                "github_org": "test-org",
                "github_platform_repo": "goldenpath",
                "gcp_dev_project": "gp-test",
                "gcp_prod_project": "gp-test",
            }
        )
        result = ops.scaffold("pin-svc", "fastapi", temp_repo / "out", cfg)
        deploy = result.service_dir / ".github/workflows/deploy.yml"
        stale = deploy.read_text().replace("v0.3.7", "v0.3.0")
        deploy.write_text(stale)
        ops.upgrade_platform_pins(result.service_dir, cfg)
        text = deploy.read_text()
        assert "@v0.3.7" in text
        assert "test-org/goldenpath" in text
        assert "@v0.3.0" not in text


class TestLoadCatalog:
    def test_loads_templates(self, repo_root: Path) -> None:
        catalog = ops.load_catalog()
        assert "fastapi" in catalog
        assert catalog["nextjs"]["default"] is True


class TestGetServiceTemplateHint:
    def test_detects_fastapi(self, valid_service_dir: Path) -> None:
        assert ops.get_service_template_hint(valid_service_dir) == "fastapi"

    def test_returns_none_for_unknown(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        assert ops.get_service_template_hint(empty) is None


class TestServiceDirFor:
    def test_prefers_last_service_dir(
        self, temp_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        svc_dir = temp_repo / "services" / "demo-svc"
        svc_dir.mkdir(parents=True)
        cfg = {
            "last_service": "demo-svc",
            "last_service_dir": str(svc_dir),
        }
        monkeypatch.setattr(ops, "REPO_ROOT", temp_repo)
        assert ops.service_dir_for(cfg) == svc_dir

    def test_falls_back_to_scaffold_output(
        self, temp_repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        outside = tmp_path / "outside-svc"
        outside.mkdir()
        monkeypatch.setattr(ops, "REPO_ROOT", temp_repo)
        monkeypatch.setattr(ops, "DEFAULT_SCAFFOLD_OUTPUT", tmp_path)
        cfg = {"last_service": "outside-svc"}
        assert ops.service_dir_for(cfg) == outside


class TestResolvePlatformRepo:
    def test_defaults_to_goldenpath(self, repo_root: Path) -> None:
        cfg = ops.default_config()
        cfg["github_platform_repo"] = ""
        assert ops.resolve_platform_repo(cfg, "my-service") == "goldenpath"

    def test_rejects_service_name_as_platform_repo(self) -> None:
        cfg = {"github_platform_repo": "my-service"}
        assert ops.resolve_platform_repo(cfg, "my-service") == "goldenpath"


class TestCheckDeployPlatformRepo:
    def test_detects_wrong_uses_reference(
        self, temp_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        shutil.copytree(
            ops.REPO_ROOT / "templates" / "express",
            temp_repo / "templates" / "express",
        )
        monkeypatch.setattr(ops, "REPO_ROOT", temp_repo)
        cfg = ops.default_config()
        cfg.update(
            {
                "github_org": "test-org",
                "github_platform_repo": "goldenpath",
                "gcp_dev_project": "gp-test",
                "gcp_prod_project": "gp-test",
                "gcp_region": "us-central1",
            }
        )
        result = ops.scaffold("bad-svc", "express", temp_repo / "out", cfg)
        deploy = result.service_dir / ".github/workflows/deploy.yml"
        deploy.write_text(
            deploy.read_text().replace(
                "test-org/goldenpath/",
                "test-org/bad-svc/",
            )
        )
        issue = ops.check_deploy_platform_repo(result.service_dir, cfg)
        assert issue is not None
        assert "bad-svc" in issue


class TestDeployWorkflow:
    def test_detects_unreplaced_tokens(self, valid_service_dir: Path) -> None:
        deploy = valid_service_dir / ".github/workflows/deploy.yml"
        deploy.write_text("service: {{SERVICE_NAME}}\n", encoding="utf-8")
        broken = ops.test_deploy_workflow(valid_service_dir)
        assert broken == deploy

    def test_returns_none_when_tokens_replaced(self, valid_service_dir: Path) -> None:
        deploy = valid_service_dir / ".github/workflows/deploy.yml"
        deploy.write_text(
            "uses: org/repo/.github/workflows/deploy.yml@v1\n",
            encoding="utf-8",
        )
        assert ops.test_deploy_workflow(valid_service_dir) is None
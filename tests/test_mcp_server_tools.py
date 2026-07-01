"""Tests for audited MCP write tools in goldenpath_mcp/server.py."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

for _mod in ("google", "google.cloud", "google.cloud.run_v2"):
    sys.modules.setdefault(_mod, MagicMock())

import goldenpath_mcp.server as server
from goldenpath_mcp.config import Settings


def _settings(**overrides: object) -> Settings:
    base = server.settings
    return replace(base, **overrides)


def test_scaffold_service_requires_params() -> None:
    out = json.loads(server.scaffold_service(name="demo"))
    assert "error" in out
    assert "github_org" in out["error"]


def test_scaffold_service_requires_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "settings", _settings(gcp_region=""))
    out = json.loads(
        server.scaffold_service(
            name="demo",
            github_org="org",
            gcp_dev_project="my-valid-project",
            gcp_prod_project="my-valid-project",
            region="",
        )
    )
    assert out["error"] == "region is required"


def test_scaffold_service_missing_shop_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(server, "settings", _settings(gcp_region="us-central1", shop_cli=tmp_path / "missing-shop"))
    out = json.loads(
        server.scaffold_service(
            name="demo",
            github_org="org",
            gcp_dev_project="my-valid-project",
            gcp_prod_project="my-valid-project",
        )
    )
    assert "shop CLI not found" in out["error"]


def test_scaffold_service_success_outside_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "goldenpath"
    repo.mkdir()
    shop = repo / "shop"
    shop.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    shop.chmod(0o755)
    monkeypatch.setattr(
        server,
        "settings",
        _settings(gcp_region="us-central1", shop_cli=shop, repo_root=repo),
    )

    with patch("goldenpath_mcp.server.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="scaffolded", stderr="")
        out = json.loads(
            server.scaffold_service(
                name="demo",
                github_org="org",
                gcp_dev_project="my-valid-project",
                gcp_prod_project="my-valid-project",
                output_dir=str(tmp_path),
            )
        )
    assert out["status"] == "ok"
    assert str(tmp_path / "demo") in out["path"]
    assert "warnings" not in out


def test_scaffold_service_warns_when_inside_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "goldenpath"
    repo.mkdir()
    shop = repo / "shop"
    shop.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    shop.chmod(0o755)
    monkeypatch.setattr(
        server,
        "settings",
        _settings(gcp_region="us-central1", shop_cli=shop, repo_root=repo),
    )

    with patch("goldenpath_mcp.server.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="scaffolded", stderr="")
        out = json.loads(
            server.scaffold_service(
                name="demo",
                github_org="org",
                gcp_dev_project="my-valid-project",
                gcp_prod_project="my-valid-project",
                output_dir=str(repo),
            )
        )
    assert out["status"] == "ok"
    assert "warnings" in out
    assert "inside GOLDENPATH_ROOT" in out["warnings"][0]


def test_trigger_deploy_requires_confirm() -> None:
    out = json.loads(server.trigger_deploy("org/repo", confirm=False))
    assert out["error"] == "confirmation required"


def test_trigger_deploy_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "settings", _settings(github_token=""))
    out = json.loads(server.trigger_deploy("org/repo", confirm=True))
    assert "GITHUB_TOKEN" in out["error"]


def test_trigger_deploy_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "settings", _settings(github_token="gh-test"))
    with patch("goldenpath_mcp.server.gh_trigger_deploy", return_value={"status": "dispatched"}) as dispatch:
        out = json.loads(server.trigger_deploy("org/repo", confirm=True))
    assert out["status"] == "dispatched"
    dispatch.assert_called_once()


def test_trigger_deploy_maps_github_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from goldenpath_mcp.github_ops import GitHubError

    monkeypatch.setattr(server, "settings", _settings(github_token="gh-test"))
    with patch("goldenpath_mcp.server.gh_trigger_deploy", side_effect=GitHubError("boom")):
        out = json.loads(server.trigger_deploy("org/repo", confirm=True))
    assert out["error"] == "boom"


def test_require_network_api_key_exits_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "settings", _settings(api_key=""))
    with pytest.raises(SystemExit, match="MCP_API_KEY is required"):
        server._require_network_api_key("streamable-http")
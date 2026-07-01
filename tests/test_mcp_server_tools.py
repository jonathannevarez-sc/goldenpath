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


def test_check_data_store_permissions_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "gcp_test_iam_permissions", lambda project, permissions: [])
    out = json.loads(server.check_data_store_permissions("cloud_sql", project="p"))
    store = out["stores"]["cloud_sql"]
    assert store["can_create"] is False
    assert store["missing_roles"]


def test_check_data_store_permissions_all_granted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "gcp_test_iam_permissions", lambda project, permissions: list(permissions))
    out = json.loads(server.check_data_store_permissions("cloud_sql", project="p"))
    assert out["stores"]["cloud_sql"]["can_create"] is True


def test_check_data_store_permissions_disabled_store(monkeypatch: pytest.MonkeyPatch) -> None:
    out = json.loads(server.check_data_store_permissions("spanner", project="p"))
    assert out["stores"]["spanner"]["enabled"] is False


def test_scaffold_service_with_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import service_composer as sc

    svc = sc.ServiceConfig(
        service_name="cfg-demo", template="fastapi", runtime="python",
        deployment_mode="server",
        data_stores=[sc.DataStoreSpec("cloud_sql", {"engine": "postgresql"})],
    )
    with patch("goldenpath_mcp.server.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="scaffolded", stderr="")
        out = json.loads(
            server.scaffold_service(name="ignored", config=svc.to_json(), output_dir=str(tmp_path))
        )
        cmd = run.call_args.args[0]
    assert out["status"] == "ok"
    assert out["service"] == "cfg-demo"
    assert "--config" in cmd


def test_scaffold_service_invalid_config() -> None:
    out = json.loads(server.scaffold_service(name="x", config='{"template": "fastapi"}'))
    assert "error" in out


def test_scaffold_service_config_fails_validation() -> None:
    import service_composer as sc

    # SPA + data store is a capability violation → validation error, no scaffold.
    svc = sc.ServiceConfig(
        service_name="bad-spa", template="react-spa", runtime="node",
        deployment_mode="static",
        data_stores=[sc.DataStoreSpec("cloud_sql", {"engine": "postgresql"})],
    )
    out = json.loads(server.scaffold_service(name="x", config=svc.to_json()))
    assert "issues" in out


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
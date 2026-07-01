"""Tests for mcp/goldenpath_mcp/config.py and enterprise.py."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from goldenpath_mcp.config import Settings
from goldenpath_mcp.enterprise import merged_enterprise_env, platform_default


def test_merged_enterprise_env_from_example(repo_root: Path) -> None:
    merged = merged_enterprise_env(repo_root)
    assert merged["PLATFORM_REPO"] == "goldenpath"
    assert merged["GCP_REGION"] == "us-central1"


def test_platform_default(repo_root: Path) -> None:
    assert platform_default(repo_root, "MCP_SERVICE_NAME") == "goldenpath-mcp"


def test_settings_from_env_defaults(repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOLDENPATH_ROOT", raising=False)
    monkeypatch.delenv("GCP_PROJECT", raising=False)
    monkeypatch.delenv("MCP_API_KEY", raising=False)
    settings = Settings.from_env()
    assert settings.repo_root.resolve() == repo_root.resolve()
    assert settings.transport == "stdio"
    assert settings.port == 8080
    assert settings.channel == "stable"


def test_settings_gcp_project_from_enterprise(
    temp_repo: Path, sample_enterprise_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOLDENPATH_ROOT", str(temp_repo))
    monkeypatch.delenv("GCP_PROJECT", raising=False)
    settings = Settings.from_env()
    assert settings.gcp_project == "my-gp-sandbox-test"


def test_settings_from_env_overrides(repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOLDENPATH_ROOT", str(repo_root))
    monkeypatch.setenv("MCP_TRANSPORT", "sse")
    monkeypatch.setenv("MCP_PORT", "9090")
    monkeypatch.setenv("GCP_PROJECT", "my-test-project")
    monkeypatch.setenv("MCP_API_KEY", "secret-key")
    settings = Settings.from_env()
    assert settings.transport == "sse"
    assert settings.port == 9090
    assert settings.gcp_project == "my-test-project"
    assert settings.api_key == "secret-key"
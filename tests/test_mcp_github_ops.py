"""Tests for mcp/goldenpath_mcp/github_ops.py."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from goldenpath_mcp.github_ops import GitHubError, trigger_deploy


def test_trigger_deploy_success() -> None:
    with patch("goldenpath_mcp.github_ops.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        result = trigger_deploy("tok", "org/repo", "deploy.yml", "dev", "main")
    assert result["status"] == "dispatched"
    assert result["repo"] == "org/repo"
    assert result["environment"] == "dev"


def test_trigger_deploy_missing_gh() -> None:
    with patch("goldenpath_mcp.github_ops.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(GitHubError, match="gh CLI not found"):
            trigger_deploy("tok", "org/repo", "deploy.yml", "dev")


def test_trigger_deploy_gh_failure() -> None:
    err = subprocess.CalledProcessError(1, "gh", stderr="workflow not found")
    with patch("goldenpath_mcp.github_ops.subprocess.run", side_effect=err):
        with pytest.raises(GitHubError, match="workflow not found"):
            trigger_deploy("tok", "org/repo", "deploy.yml", "dev")
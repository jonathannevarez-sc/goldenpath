"""GitHub operations — uses caller GITHUB_TOKEN, no elevation."""

from __future__ import annotations

import json
import subprocess
from typing import Any


class GitHubError(Exception):
    pass


def trigger_deploy(
    token: str,
    repo: str,
    workflow: str,
    environment: str,
    ref: str = "main",
) -> dict[str, Any]:
    """Dispatch GitHub Actions workflow (Deploy)."""
    import os

    cmd = [
        "gh",
        "api",
        f"repos/{repo}/actions/workflows/{workflow}/dispatches",
        "-X",
        "POST",
        "-f",
        f"ref={ref}",
        "-f",
        f"inputs[environment]={environment}",
    ]
    env = {**os.environ, "GH_TOKEN": token, "GITHUB_TOKEN": token}
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
    except FileNotFoundError as exc:
        raise GitHubError("gh CLI not found; install GitHub CLI") from exc
    except subprocess.CalledProcessError as exc:
        raise GitHubError(exc.stderr.strip() or "workflow dispatch failed") from exc

    return {
        "repo": repo,
        "workflow": workflow,
        "environment": environment,
        "ref": ref,
        "status": "dispatched",
    }
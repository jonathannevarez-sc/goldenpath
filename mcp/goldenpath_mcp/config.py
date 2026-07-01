"""Golden Path MCP server configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from goldenpath_mcp.enterprise import merged_enterprise_env, platform_default


def _default_gcp_project(repo_root: Path) -> str | None:
    explicit = os.getenv("GCP_PROJECT")
    if explicit:
        return explicit
    env = merged_enterprise_env(repo_root)
    return env.get("GCP_SANDBOX_PROJECT") or env.get("GCP_DEV_PROJECT") or None


@dataclass(frozen=True)
class Settings:
    """Runtime settings from environment."""

    repo_root: Path
    channel: str
    version: str
    gcp_region: str
    gcp_project: str | None
    mcp_service_name: str
    shop_cli: Path
    transport: str
    host: str
    port: int
    api_key: str | None
    github_token: str | None

    @classmethod
    def from_env(cls) -> Settings:
        env_root = os.getenv("GOLDENPATH_ROOT")
        if env_root:
            repo_root = Path(env_root).resolve()
        else:
            # mcp/goldenpath_mcp -> repo root
            repo_root = Path(__file__).resolve().parents[2]

        shop_cli = Path(os.getenv("SHOP_CLI", repo_root / "cli" / "shop"))

        ent = platform_default(repo_root, "GOLDENPATH_VERSION")
        reg = platform_default(repo_root, "GCP_REGION")
        mcp_name = platform_default(repo_root, "MCP_SERVICE_NAME")

        return cls(
            repo_root=repo_root,
            channel=os.getenv("GOLDENPATH_CHANNEL", "stable"),
            version=os.getenv("GOLDENPATH_VERSION") or ent,
            gcp_region=os.getenv("GCP_REGION") or reg,
            gcp_project=_default_gcp_project(repo_root),
            mcp_service_name=os.getenv("MCP_SERVICE_NAME") or mcp_name,
            shop_cli=shop_cli,
            transport=os.getenv("MCP_TRANSPORT", "stdio"),
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", os.getenv("MCP_PORT", "8080"))),
            api_key=os.getenv("MCP_API_KEY") or None,
            github_token=os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or None,
        )
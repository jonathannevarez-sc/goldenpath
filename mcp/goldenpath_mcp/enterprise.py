"""Load merged enterprise config from GOLDENPATH_ROOT (no hardcoded org values)."""

from __future__ import annotations

import os
import re
from pathlib import Path


def _parse_env_file(path: Path) -> dict[str, str]:
    profile: dict[str, str] = {}
    if not path.is_file():
        return profile
    for line in path.read_text().splitlines():
        m = re.match(r"^\s*([A-Z_]+)=(.*)$", line)
        if m:
            profile[m.group(1)] = m.group(2).strip().strip('"')
    return profile


def merged_enterprise_env(repo_root: Path) -> dict[str, str]:
    example = repo_root / "config" / "enterprise.env.example"
    override = os.environ.get("GOLDENPATH_CONFIG")
    local_path = Path(override) if override else repo_root / "config" / "enterprise.env"
    merged = _parse_env_file(example)
    merged.update(_parse_env_file(local_path))
    return merged


def platform_default(repo_root: Path, key: str) -> str:
    return merged_enterprise_env(repo_root).get(key, "")
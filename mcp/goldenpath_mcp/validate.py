"""Validate a service repo matches Golden Path conventions."""

from __future__ import annotations

import re
from pathlib import Path


REQUIRED = [
    "Dockerfile",
    "infra/main.tf",
    "infra/dev.tfvars",
    ".github/workflows/deploy.yml",
]

SCAFFOLD_TOKEN_RE = re.compile(r"\{\{[A-Z_]+\}\}")


def _has_unreplaced_tokens(root: Path) -> list[str]:
    """Return relative paths that still contain scaffold placeholders."""
    stale: list[str] = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if SCAFFOLD_TOKEN_RE.search(text):
            stale.append(str(path.relative_to(root)))
    return sorted(stale)


def validate_service(path: str) -> dict:
    root = Path(path).resolve()
    if not root.is_dir():
        return {"valid": False, "errors": [f"not a directory: {path}"]}

    errors: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f"missing required file: {rel}")

    dockerfile = root / "Dockerfile"
    if dockerfile.is_file():
        text = dockerfile.read_text(encoding="utf-8", errors="ignore")
        if "docker.io" in text or "gcr.io" in text:
            warnings.append("Dockerfile should not reference external registries (use Artifact Registry via CI)")

    stale_tokens = _has_unreplaced_tokens(root)
    for rel in stale_tokens:
        errors.append(f"unreplaced template tokens in: {rel}")

    return {
        "valid": len(errors) == 0,
        "path": str(root),
        "errors": errors,
        "warnings": warnings,
    }
"""Schema contract for templates/catalog.json — every template must be deployable."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "templates" / "catalog.json"
TEMPLATES_DIR = REPO_ROOT / "templates"

REQUIRED_FIELDS = ("description", "app_runtime", "container_port", "health_check_path")
ALLOWED_RUNTIMES = {"node", "python", "docker"}


@pytest.fixture
def catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def test_catalog_has_exactly_one_default(catalog: dict) -> None:
    defaults = [name for name, meta in catalog.items() if meta.get("default")]
    assert defaults == ["nextjs"]


def test_catalog_entries_are_complete_and_backed_by_templates(catalog: dict) -> None:
    assert catalog, "catalog must not be empty"
    for name, meta in catalog.items():
        for field in REQUIRED_FIELDS:
            assert field in meta, f"{name} missing {field}"
        assert meta["app_runtime"] in ALLOWED_RUNTIMES, f"{name} has invalid app_runtime"
        assert isinstance(meta["container_port"], int) and meta["container_port"] > 0
        assert meta["health_check_path"].startswith("/")
        template_dir = TEMPLATES_DIR / name
        assert template_dir.is_dir(), f"missing template directory for {name}"
        assert (template_dir / "infra" / "main.tf").is_file()
        assert (template_dir / ".github" / "workflows" / "deploy.yml").is_file()
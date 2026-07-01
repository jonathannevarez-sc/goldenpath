"""Tests for mcp/goldenpath_mcp/content.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from goldenpath_mcp.content import ContentStore, DOC_ALIASES


def test_read_doc_via_alias(temp_repo: Path) -> None:
    store = ContentStore(temp_repo)
    text = store.read_doc("start-here.md")
    assert "Golden Path is **enterprise-agnostic**" in text


def test_read_doc_canonical_path(temp_repo: Path) -> None:
    store = ContentStore(temp_repo)
    text = store.read_doc("getting-started/01-start-here.md")
    assert len(text) > 0


def test_read_skill(temp_repo: Path) -> None:
    store = ContentStore(temp_repo)
    text = store.read_skill("test-skill")
    assert "Test skill" in text


def test_list_skills_and_docs(temp_repo: Path) -> None:
    store = ContentStore(temp_repo)
    assert "test-skill" in store.list_skills()
    assert any(p.endswith("01-start-here.md") for p in store.list_docs())


def test_read_catalog(temp_repo: Path) -> None:
    store = ContentStore(temp_repo)
    catalog = store.read_catalog()
    assert "fastapi" in catalog
    assert catalog["nextjs"]["default"] is True


def test_meta_version(temp_repo: Path) -> None:
    store = ContentStore(temp_repo)
    meta = store.meta_version("stable", "v0.3.8")
    assert meta["channel"] == "stable"
    assert meta["version"] == "v0.3.8"
    assert meta["skills_count"] >= 1
    assert meta["docs_count"] >= 1


def test_path_traversal_blocked(temp_repo: Path) -> None:
    store = ContentStore(temp_repo)
    with pytest.raises(ValueError, match="path traversal blocked"):
        store.read_doc("../../etc/passwd")


def test_missing_doc_raises(temp_repo: Path) -> None:
    store = ContentStore(temp_repo)
    with pytest.raises(FileNotFoundError, match="doc not found"):
        store.read_doc("does-not-exist.md")


def test_doc_aliases_cover_legacy_names() -> None:
    assert DOC_ALIASES["quickstart.md"] == "getting-started/03-quickstart.md"
    assert DOC_ALIASES["JOURNEY-CLI.md"] == "getting-started/04-journey-cli.md"
    assert DOC_ALIASES["architecture.md"] == "platform/architecture.md"


@pytest.mark.parametrize("bad_name", ["..", "../secrets", ".hidden", "a/b", "a\\b"])
def test_read_skill_blocks_traversal(temp_repo: Path, bad_name: str) -> None:
    store = ContentStore(temp_repo)
    with pytest.raises(ValueError, match="invalid skill name"):
        store.read_skill(bad_name)
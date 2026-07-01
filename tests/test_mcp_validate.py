"""Tests for mcp/goldenpath_mcp/validate.py."""

from __future__ import annotations

from pathlib import Path

from goldenpath_mcp.validate import validate_service


def test_valid_service_dir(valid_service_dir: Path) -> None:
    result = validate_service(str(valid_service_dir))
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["path"] == str(valid_service_dir.resolve())


def test_missing_directory(tmp_path: Path) -> None:
    result = validate_service(str(tmp_path / "missing"))
    assert result["valid"] is False
    assert "not a directory" in result["errors"][0]


def test_missing_required_files(tmp_path: Path) -> None:
    service = tmp_path / "incomplete"
    service.mkdir()
    result = validate_service(str(service))
    assert result["valid"] is False
    assert any("missing required file" in e for e in result["errors"])


def test_warns_on_external_registry(tmp_path: Path, valid_service_dir: Path) -> None:
    dockerfile = valid_service_dir / "Dockerfile"
    dockerfile.write_text("FROM docker.io/library/python:3.12\n", encoding="utf-8")
    result = validate_service(str(valid_service_dir))
    assert result["valid"] is True
    assert any("external registries" in w for w in result["warnings"])


def test_rejects_unreplaced_tokens(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parent.parent / "templates" / "fastapi"
    dest = tmp_path / "stale-tokens"
    import shutil

    shutil.copytree(src, dest)
    result = validate_service(str(dest))
    assert result["valid"] is False
    assert any("unreplaced template tokens" in e for e in result["errors"])
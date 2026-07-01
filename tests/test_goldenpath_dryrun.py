"""Tests for scripts/setup/goldenpath_dryrun.py (offline structure checks)."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts" / "setup"
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import goldenpath_dryrun as dryrun  # noqa: E402
import goldenpath_ops as ops  # noqa: E402


def test_dryrun_returns_steps() -> None:
    cfg = ops.default_config()
    report = dryrun.run_dryrun(cfg)
    menus = {s.menu for s in report.steps}
    assert "2" in menus
    assert "3" in menus
    assert "6" in menus
    assert "7" in menus
    assert len(report.steps) >= 7


def test_dryrun_flags_missing_enterprise_env(
    monkeypatch, tmp_path: Path
) -> None:
    cfg = ops.default_config()
    monkeypatch.setattr(dryrun, "ENTERPRISE_ENV", tmp_path / "missing.env")
    report = dryrun.run_dryrun(cfg)
    assert any("enterprise.env missing" in b for b in report.blockers)


def test_dryrun_json_main_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["goldenpath_dryrun.py", "--json"],
    )
    # main should not crash
    code = dryrun.main()
    assert code in (0, 1)
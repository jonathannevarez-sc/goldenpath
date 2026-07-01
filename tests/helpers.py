"""Shared non-fixture helpers for platform tests."""

from __future__ import annotations

import json
from pathlib import Path


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
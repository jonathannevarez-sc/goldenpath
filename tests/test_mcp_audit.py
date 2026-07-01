"""Tests for mcp/goldenpath_mcp/audit.py."""

from __future__ import annotations

import json

from goldenpath_mcp.audit import audit


def test_audit_writes_json_to_stderr(capsys) -> None:
    audit("test_event", user="alice", action="deploy")
    captured = capsys.readouterr()
    record = json.loads(captured.err.strip())
    assert record["event"] == "test_event"
    assert record["user"] == "alice"
    assert record["action"] == "deploy"
    assert "ts" in record
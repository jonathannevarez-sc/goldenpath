"""Tests for data-store IAM permission gating (mocked gcloud)."""

from __future__ import annotations

import json

import goldenpath_ops as ops
import service_composer as sc


def test_probe_reports_missing_and_roles(monkeypatch):
    # Caller holds only 2 of the required Cloud SQL permissions.
    granted = ["cloudsql.instances.create", "serviceusage.services.enable"]

    monkeypatch.setattr(ops, "cmd_available", lambda name: True)
    monkeypatch.setattr(ops, "_PERM_PROBE_CACHE", {})

    def fake_run_cmd(cmd, cwd=None, timeout=300):
        assert "test-iam-permissions" in cmd
        return ops.CmdResult(0, json.dumps({"permissions": granted}), "")

    monkeypatch.setattr(ops, "run_cmd", fake_run_cmd)

    report = ops.probe_data_store_permissions("acme-dev", ["cloud_sql"], "public")
    entry = report["cloud_sql"]
    assert entry["unknown"] is False
    assert set(entry["granted"]) == set(granted)
    # Everything else is missing, including SA + IAM + secret perms.
    assert "iam.serviceAccounts.create" in entry["missing"]
    assert "roles/iam.serviceAccountAdmin" in entry["missing_roles"]
    assert "roles/secretmanager.admin" in entry["missing_roles"]


def test_probe_all_granted_no_missing(monkeypatch):
    perms = sc.data_store_permissions("cloud_sql", "public")
    monkeypatch.setattr(ops, "cmd_available", lambda name: True)
    monkeypatch.setattr(ops, "_PERM_PROBE_CACHE", {})
    monkeypatch.setattr(
        ops, "run_cmd",
        lambda cmd, cwd=None, timeout=300: ops.CmdResult(0, json.dumps({"permissions": perms}), ""),
    )
    report = ops.probe_data_store_permissions("acme-dev", ["cloud_sql"], "public")
    assert report["cloud_sql"]["missing"] == []
    assert report["cloud_sql"]["unknown"] is False


def test_probe_unknown_when_no_gcloud(monkeypatch):
    monkeypatch.setattr(ops, "cmd_available", lambda name: False)
    report = ops.probe_data_store_permissions("acme-dev", ["cloud_sql"], "public")
    assert report["cloud_sql"]["unknown"] is True


def test_probe_unknown_on_gcloud_error(monkeypatch):
    monkeypatch.setattr(ops, "cmd_available", lambda name: True)
    monkeypatch.setattr(ops, "_PERM_PROBE_CACHE", {})
    monkeypatch.setattr(
        ops, "run_cmd",
        lambda cmd, cwd=None, timeout=300: ops.CmdResult(1, "", "PERMISSION_DENIED"),
    )
    report = ops.probe_data_store_permissions("acme-dev", ["cloud_sql"], "public")
    assert report["cloud_sql"]["unknown"] is True

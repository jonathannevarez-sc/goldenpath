"""Contract tests for the service composer: constraint matrix + serialization.

conftest.py puts scripts/setup on sys.path.
"""

from __future__ import annotations

import pytest
import service_composer as sc


# ── Catalog capability overlay ────────────────────────────────────────────────


def test_every_template_has_capabilities():
    catalog = sc.load_catalog()
    for name in catalog:
        caps = sc.template_capabilities(name, catalog)
        assert caps["runtimes"], f"{name} has no runtimes"
        assert caps["deployment_modes"], f"{name} has no modes"
        for m in caps["deployment_modes"]:
            assert m in (sc.MODE_SERVER, sc.MODE_STATIC)


@pytest.mark.parametrize(
    "template,expected_modes",
    [
        ("nextjs", {sc.MODE_SERVER, sc.MODE_STATIC}),
        ("fastapi", {sc.MODE_SERVER}),
        ("streamlit", {sc.MODE_SERVER}),
        ("express", {sc.MODE_SERVER}),
        ("react-spa", {sc.MODE_STATIC}),
        ("svelte-spa", {sc.MODE_STATIC}),
    ],
)
def test_template_modes(template, expected_modes):
    caps = sc.template_capabilities(template)
    assert set(caps["deployment_modes"]) == expected_modes


# ── Runtime/mode capability gate ──────────────────────────────────────────────


def _cfg(**kw):
    base = dict(service_name="demo-svc", template="fastapi", runtime="python", deployment_mode="server")
    base.update(kw)
    return sc.ServiceConfig(**base)


def test_valid_server_config_ok():
    assert sc.validate_config(_cfg()).ok


def test_bad_runtime_is_capability_gated():
    res = sc.validate_config(_cfg(template="fastapi", runtime="node"))
    assert not res.ok
    assert any(i.field == "runtime" and i.gate == sc.GATE_CAPABILITY for i in res.errors)


def test_bad_mode_is_capability_gated():
    res = sc.validate_config(_cfg(template="fastapi", deployment_mode="static"))
    assert not res.ok
    assert any(i.field == "deployment_mode" and i.gate == sc.GATE_CAPABILITY for i in res.errors)


def test_nextjs_allows_both_modes():
    assert sc.validate_config(_cfg(template="nextjs", runtime="node", deployment_mode="server")).ok
    assert sc.validate_config(_cfg(template="nextjs", runtime="node", deployment_mode="static")).ok


# ── Deployment mode ↔ data-store attachment ───────────────────────────────────


def test_static_cannot_attach_store():
    res = sc.validate_config(
        _cfg(template="react-spa", runtime="node", deployment_mode="static",
             data_stores=[sc.DataStoreSpec("cloud_sql", {})])
    )
    assert not res.ok
    assert any(i.gate == sc.GATE_CAPABILITY for i in res.errors)


def test_server_attaches_cloud_sql():
    res = sc.validate_config(
        _cfg(data_stores=[sc.DataStoreSpec("cloud_sql", {"engine": "postgresql"})])
    )
    assert res.ok, [i.message for i in res.errors]


# ── Data-store constraints ────────────────────────────────────────────────────


def test_disabled_store_is_capability_gated():
    res = sc.validate_config(_cfg(data_stores=[sc.DataStoreSpec("spanner", {})]))
    assert not res.ok
    assert any("later release" in i.message.lower() for i in res.errors)


def test_mysql_engine_not_yet_supported():
    res = sc.validate_config(
        _cfg(data_stores=[sc.DataStoreSpec("cloud_sql", {"engine": "mysql"})])
    )
    assert not res.ok
    assert any(i.field.endswith("engine") for i in res.errors)


def test_private_ip_without_network_is_blocked():
    res = sc.validate_config(
        _cfg(data_stores=[sc.DataStoreSpec("cloud_sql", {"engine": "postgresql", "ip_mode": "private"})]),
        vpc_network=None,
    )
    assert not res.ok
    assert any("private ip" in i.message.lower() for i in res.errors)


def test_private_ip_with_network_ok():
    res = sc.validate_config(
        _cfg(data_stores=[sc.DataStoreSpec("cloud_sql", {"engine": "postgresql", "ip_mode": "private"})]),
        vpc_network="projects/p/global/networks/default",
    )
    assert res.ok, [i.message for i in res.errors]


def test_bad_version_is_config_gated():
    res = sc.validate_config(
        _cfg(data_stores=[sc.DataStoreSpec("cloud_sql", {"engine": "postgresql", "version": "POSTGRES_9"})])
    )
    assert not res.ok
    assert any(i.field.endswith("version") for i in res.errors)


# ── Permission gate (distinct from capability) ────────────────────────────────


def test_permission_gate_marks_missing():
    report = {"cloud_sql": {"missing": ["cloudsql.instances.create"]}}
    res = sc.validate_config(
        _cfg(data_stores=[sc.DataStoreSpec("cloud_sql", {"engine": "postgresql"})]),
        iam_report=report,
    )
    assert not res.ok
    perm_issues = [i for i in res.errors if i.gate == sc.GATE_PERMISSION]
    assert perm_issues
    assert "roles/cloudsql.admin" in perm_issues[0].message


# ── Environments ──────────────────────────────────────────────────────────────


def test_unknown_environment_blocked():
    res = sc.validate_config(_cfg(environments=["dev", "staging"]))
    assert not res.ok
    assert any(i.field == "environments" for i in res.errors)


def test_empty_environments_blocked():
    res = sc.validate_config(_cfg(environments=[]))
    assert not res.ok


# ── Permission catalog helpers ────────────────────────────────────────────────


def test_public_permissions_exclude_vpc():
    pub = sc.data_store_permissions("cloud_sql", "public")
    priv = sc.data_store_permissions("cloud_sql", "private")
    assert "vpcaccess.connectors.create" in priv
    assert "vpcaccess.connectors.create" not in pub


def test_role_for_permission():
    assert sc.role_for_permission("cloud_sql", "secretmanager.secrets.create") == "roles/secretmanager.admin"


# ── Serialization round-trip ──────────────────────────────────────────────────


def test_config_json_round_trip():
    cfg = _cfg(
        data_stores=[sc.DataStoreSpec("cloud_sql", {"engine": "postgresql", "tier": "db-f1-micro"})],
        environments=["dev", "prod"],
        labels={"team": "payments"},
    )
    restored = sc.ServiceConfig.from_json(cfg.to_json())
    assert restored.service_name == cfg.service_name
    assert restored.template == cfg.template
    assert restored.data_stores[0].id == "cloud_sql"
    assert restored.data_stores[0].config["tier"] == "db-f1-micro"
    assert restored.labels == {"team": "payments"}


# ── UI option helpers ─────────────────────────────────────────────────────────


def test_data_store_options_flag_disabled_and_permission():
    opts = {o["value"]: o for o in sc.data_store_options(sc.MODE_SERVER)}
    assert opts["spanner"]["enabled"] is False
    assert opts["cloud_sql"]["enabled"] is True

    gated = {o["value"]: o for o in sc.data_store_options(
        sc.MODE_SERVER, iam_report={"cloud_sql": {"missing": ["cloudsql.instances.create"]}}
    )}
    assert gated["cloud_sql"]["enabled"] is False
    assert gated["cloud_sql"]["gate"] == sc.GATE_PERMISSION


def test_data_store_options_static_disables_all():
    opts = sc.data_store_options(sc.MODE_STATIC)
    assert all(not o["enabled"] for o in opts)

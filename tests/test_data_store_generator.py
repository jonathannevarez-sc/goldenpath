"""Integration tests for data-store scaffold generation (Cloud SQL vertical slice).

Scaffolds real templates + Cloud SQL wiring into a temp dir and asserts the
generated Terraform, connection layer, deps, tfvars, and README are correct and
free of unreplaced tokens.
"""

from __future__ import annotations

import re
from pathlib import Path

import goldenpath_ops as ops
import service_composer as sc

_CFG = {
    "github_org": "acme-co",
    "github_platform_repo": "goldenpath",
    "gcp_dev_project": "acme-dev-123",
    "gcp_prod_project": "acme-prod-456",
    "gcp_region": "us-central1",
}

_TOKEN_RE = re.compile(r"\{\{[A-Z_]+\}\}")


def _scaffold(tmp_path: Path, svc: sc.ServiceConfig) -> Path:
    res = ops.scaffold(svc.service_name, svc.template, tmp_path, _CFG, service_config=svc)
    return res.service_dir


def test_fastapi_cloud_sql_public(tmp_path: Path):
    svc = sc.ServiceConfig(
        service_name="demo-api",
        template="fastapi",
        runtime="python",
        deployment_mode="server",
        data_stores=[sc.DataStoreSpec("cloud_sql", {
            "engine": "postgresql", "version": "POSTGRES_16",
            "tier": "db-f1-micro", "ip_mode": "public", "database_name": "appdb",
        })],
        environments=["dev", "prod"],
    )
    d = _scaffold(tmp_path, svc)

    ds = (d / "infra" / "data-stores.tf").read_text(encoding="utf-8")
    assert 'module "cloud_sql"' in ds
    assert "modules/cloud-sql?ref=" in ds
    assert 'module "vpc_connector"' not in ds  # public IP → no connector

    main_tf = (d / "infra" / "main.tf").read_text(encoding="utf-8")
    assert "INSTANCE_CONNECTION_NAME = module.cloud_sql.instance_connection_name" in main_tf
    assert 'DB_IP_TYPE               = "public"' in main_tf

    db = (d / "app" / "db.py").read_text(encoding="utf-8")
    assert "cloud.sql.connector" in db
    assert "check_connection" in db

    reqs = (d / "requirements.txt").read_text(encoding="utf-8")
    assert "cloud-sql-python-connector" in reqs
    assert "SQLAlchemy" in reqs

    mainpy = (d / "app" / "main.py").read_text(encoding="utf-8")
    assert "/api/db-health" in mainpy

    for env in ("dev", "prod"):
        tfvars = (d / "infra" / f"{env}.tfvars").read_text(encoding="utf-8")
        assert 'db_version             = "POSTGRES_16"' in tfvars

    assert "Cloud SQL" in (d / "README.md").read_text(encoding="utf-8")

    # No unreplaced tokens anywhere in generated infra/app code.
    for p in list((d / "infra").glob("*.tf")) + [d / "app" / "db.py"]:
        assert not _TOKEN_RE.search(p.read_text(encoding="utf-8")), f"tokens left in {p.name}"


def test_express_cloud_sql_private(tmp_path: Path):
    svc = sc.ServiceConfig(
        service_name="priv-api",
        template="express",
        runtime="node",
        deployment_mode="server",
        data_stores=[sc.DataStoreSpec("cloud_sql", {
            "engine": "postgresql", "ip_mode": "private", "high_availability": True,
            "network": "projects/acme-dev-123/global/networks/default",
        })],
        environments=["dev"],
    )
    d = _scaffold(tmp_path, svc)

    ds = (d / "infra" / "data-stores.tf").read_text(encoding="utf-8")
    assert 'module "vpc_connector"' in ds
    assert "var.db_network" in ds

    main_tf = (d / "infra" / "main.tf").read_text(encoding="utf-8")
    assert "vpc_connector = module.vpc_connector.id" in main_tf

    dbjs = (d / "src" / "db.js").read_text(encoding="utf-8")
    assert "cloud-sql-connector" in dbjs

    index = (d / "src" / "index.js").read_text(encoding="utf-8")
    assert "/api/db-health" in index
    assert 'import { checkConnection } from "./db.js";' in index

    import json
    pkg = json.loads((d / "package.json").read_text(encoding="utf-8"))
    assert "@google-cloud/cloud-sql-connector" in pkg["dependencies"]
    assert "pg" in pkg["dependencies"]

    # dev.tfvars gets private network; prod.tfvars is not selected → untouched.
    dev = (d / "infra" / "dev.tfvars").read_text(encoding="utf-8")
    assert "db_network" in dev


def test_no_data_stores_is_plain_scaffold(tmp_path: Path):
    svc = sc.ServiceConfig(
        service_name="plain-api", template="fastapi", runtime="python",
        deployment_mode="server", data_stores=[],
    )
    d = _scaffold(tmp_path, svc)
    assert not (d / "infra" / "data-stores.tf").exists()
    assert not (d / "app" / "db.py").exists()

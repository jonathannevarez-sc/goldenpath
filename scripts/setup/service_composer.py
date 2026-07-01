#!/usr/bin/env python3
"""Golden Path — service composition model, constraint matrix, and validation.

Single source of truth for the "Create Service" configurator. Pure Python
(stdlib only, no GCP or third-party deps) so it can be imported by:

  * the Streamlit wizard  (scripts/setup/goldenpath_setup_app.py)
  * the CLI ops layer      (scripts/setup/goldenpath_ops.py / _cli.py)
  * the MCP server         (mcp/goldenpath_mcp/server.py)

It encodes the config model (:class:`ServiceConfig`), the capability matrix
(template ↔ runtime ↔ deployment-mode ↔ data-store), the per-store IAM
permission catalog used for permission gating, and the validation that turns an
arbitrary partial config into either a green light or a list of clearly-worded
disabled reasons.

Two independent gates exist and every disabled option states which one applies:

  * ``capability`` — the template/mode/runtime combination is not supported.
  * ``permission`` — the caller lacks a required IAM permission (from a live
    ``testIamPermissions`` probe); the message names the permission, the role
    that grants it, and the resource.

This module is deliberately data-driven: adding a new data store or template
capability is an edit to :data:`DATA_STORES` / ``templates/catalog.json``, not
new control flow.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# ── Gate kinds ────────────────────────────────────────────────────────────────

GATE_CAPABILITY = "capability"
GATE_PERMISSION = "permission"
GATE_CONFIG = "config"

# Deployment modes
MODE_SERVER = "server"
MODE_STATIC = "static"

# SPA data-access strategies
SPA_NONE = "none"
SPA_BFF = "generate_bff"


# ── Template capability overlay ───────────────────────────────────────────────
#
# The catalog (templates/catalog.json) is the registry of templates and their
# runtime/port/health metadata. We extend each entry with two capability fields:
#   * runtimes         — the runtime selections the user may pick
#   * deployment_modes — server / static (Next.js exposes both)
# If an older catalog lacks these fields, DEFAULT_TEMPLATE_CAPS supplies them so
# the composer keeps working without a catalog migration.

DEFAULT_TEMPLATE_CAPS: dict[str, dict[str, list[str]]] = {
    "nextjs": {"runtimes": ["node", "docker"], "deployment_modes": [MODE_SERVER, MODE_STATIC]},
    "fastapi": {"runtimes": ["python", "docker"], "deployment_modes": [MODE_SERVER]},
    "streamlit": {"runtimes": ["python", "docker"], "deployment_modes": [MODE_SERVER]},
    "express": {"runtimes": ["node", "docker"], "deployment_modes": [MODE_SERVER]},
    "react-spa": {"runtimes": ["node"], "deployment_modes": [MODE_STATIC]},
    "svelte-spa": {"runtimes": ["node"], "deployment_modes": [MODE_STATIC]},
}

# Default BFF framework for a SPA, keyed by the SPA's build runtime.
BFF_FRAMEWORKS = {"node": "express", "python": "fastapi"}


def _catalog_path() -> Path:
    # scripts/setup/service_composer.py → repo root is two levels up.
    return Path(__file__).resolve().parent.parent.parent / "templates" / "catalog.json"


def load_catalog(catalog_path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Load templates/catalog.json (raw)."""
    path = Path(catalog_path) if catalog_path else _catalog_path()
    return json.loads(path.read_text(encoding="utf-8"))


def template_capabilities(
    template: str, catalog: dict[str, dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Return merged capability metadata for a template.

    Combines catalog metadata (description, app_runtime, port, health) with the
    capability overlay (runtimes, deployment_modes), falling back to
    DEFAULT_TEMPLATE_CAPS when the catalog entry omits the overlay fields.
    """
    catalog = catalog if catalog is not None else load_catalog()
    if template not in catalog:
        raise KeyError(f"Unknown template '{template}'")
    meta = dict(catalog[template])
    defaults = DEFAULT_TEMPLATE_CAPS.get(template, {})
    runtimes = meta.get("runtimes") or defaults.get("runtimes") or [meta.get("app_runtime", "node")]
    modes = meta.get("deployment_modes") or defaults.get("deployment_modes") or [MODE_SERVER]
    meta["runtimes"] = list(runtimes)
    meta["deployment_modes"] = list(modes)
    meta["is_spa"] = modes == [MODE_STATIC]
    return meta


# ── Data-store registry + IAM permission catalog ─────────────────────────────
#
# Each entry declares:
#   enabled          — implemented in this release (only cloud_sql for now)
#   runtime_roles    — least-privilege roles bound to the service's runtime SA
#   required_apis    — services enabled by the generated Terraform
#   permission_groups — logical operations the creator must be able to perform;
#                       each maps a human label + granting role to the concrete
#                       permissions probed via testIamPermissions. `vpc_only`
#                       groups are only relevant when a private-IP store is used.
#   engines          — allowed engine choices (with per-engine `enabled`)
#   subconfig        — declarative schema the UI renders for the store

_PG_ENGINE = {
    "value": "postgresql",
    "label": "PostgreSQL",
    "enabled": True,
    "versions": ["POSTGRES_16", "POSTGRES_15", "POSTGRES_14"],
    "default_version": "POSTGRES_16",
}
_MYSQL_ENGINE = {
    "value": "mysql",
    "label": "MySQL",
    "enabled": False,  # connection layer lands in a later pass
    "coming_soon": True,
    "versions": ["MYSQL_8_0"],
    "default_version": "MYSQL_8_0",
}

DATA_STORES: dict[str, dict[str, Any]] = {
    "cloud_sql": {
        "id": "cloud_sql",
        "display_name": "Cloud SQL",
        "enabled": True,
        "runtime_roles": ["roles/cloudsql.client", "roles/cloudsql.instanceUser"],
        "required_apis": [
            "sqladmin.googleapis.com",
            "secretmanager.googleapis.com",
        ],
        # Extra APIs only needed when a private-IP instance is provisioned.
        "vpc_apis": [
            "servicenetworking.googleapis.com",
            "vpcaccess.googleapis.com",
            "compute.googleapis.com",
        ],
        "engines": [_PG_ENGINE, _MYSQL_ENGINE],
        "tiers": ["db-f1-micro", "db-g1-small", "db-custom-1-3840", "db-custom-2-7680"],
        "default_tier": "db-f1-micro",
        "ip_modes": ["public", "private"],
        "default_ip_mode": "public",  # deployable without a preconfigured VPC network
        "permission_groups": [
            {
                "key": "instance",
                "label": "instance / database creation",
                "role": "roles/cloudsql.admin",
                "permissions": [
                    "cloudsql.instances.create",
                    "cloudsql.databases.create",
                    "cloudsql.users.create",
                ],
            },
            {
                "key": "service_account",
                "label": "service-account creation",
                "role": "roles/iam.serviceAccountAdmin",
                "permissions": ["iam.serviceAccounts.create"],
            },
            {
                "key": "iam_binding",
                "label": "IAM binding",
                "role": "roles/resourcemanager.projectIamAdmin",
                "permissions": ["resourcemanager.projects.setIamPolicy"],
            },
            {
                "key": "secret",
                "label": "secret creation",
                "role": "roles/secretmanager.admin",
                "permissions": ["secretmanager.secrets.create"],
            },
            {
                "key": "api_enablement",
                "label": "API enablement",
                "role": "roles/serviceusage.serviceUsageAdmin",
                "permissions": ["serviceusage.services.enable"],
            },
            {
                "key": "vpc",
                "label": "VPC / networking (private IP)",
                "role": "roles/compute.networkAdmin",
                "vpc_only": True,
                "permissions": [
                    "compute.networks.get",
                    "vpcaccess.connectors.create",
                ],
            },
        ],
    },
    # Present so the UI can list them as "coming soon"; not yet implemented.
    "alloydb": {
        "id": "alloydb",
        "display_name": "AlloyDB",
        "enabled": False,
        "coming_soon": True,
    },
    "spanner": {
        "id": "spanner",
        "display_name": "Cloud Spanner",
        "enabled": False,
        "coming_soon": True,
    },
    "firestore": {
        "id": "firestore",
        "display_name": "Firestore",
        "enabled": False,
        "coming_soon": True,
    },
}


def data_store_permissions(store_id: str, ip_mode: str = "public") -> list[str]:
    """Flat list of permissions to probe for a store, honoring VPC relevance."""
    store = DATA_STORES.get(store_id, {})
    perms: list[str] = []
    for group in store.get("permission_groups", []):
        if group.get("vpc_only") and ip_mode != "private":
            continue
        perms.extend(group["permissions"])
    return perms


def role_for_permission(store_id: str, permission: str) -> str:
    """Return the granting role for a probed permission (for gating messages)."""
    store = DATA_STORES.get(store_id, {})
    for group in store.get("permission_groups", []):
        if permission in group["permissions"]:
            return group["role"]
    return "the appropriate IAM role"


# ── Config model ──────────────────────────────────────────────────────────────


@dataclass
class DataStoreSpec:
    """A single attached data store and its sub-configuration."""

    id: str
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "config": dict(self.config)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataStoreSpec":
        return cls(id=data["id"], config=dict(data.get("config", {})))


@dataclass
class ServiceConfig:
    """A fully-composed service definition.

    Serializable to/from JSON so the CLI (``shop new --config``) and MCP
    (``scaffold_service(config=...)``) can pass the same object the UI builds.
    """

    service_name: str
    template: str
    runtime: str
    deployment_mode: str = MODE_SERVER
    data_stores: list[DataStoreSpec] = field(default_factory=list)
    spa_strategy: str = SPA_NONE
    bff: dict[str, Any] | None = None
    environments: list[str] = field(default_factory=lambda: ["dev", "prod"])
    region: str = ""
    name_prefix: str = ""
    labels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["data_stores"] = [s.to_dict() for s in self.data_stores]
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceConfig":
        stores = [DataStoreSpec.from_dict(s) for s in data.get("data_stores", [])]
        known = {f for f in ServiceConfig.__dataclass_fields__}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known and k != "data_stores"}
        kwargs["data_stores"] = stores
        return cls(**kwargs)

    @classmethod
    def from_json(cls, text: str) -> "ServiceConfig":
        return cls.from_dict(json.loads(text))

    def has_private_store(self) -> bool:
        return any(s.config.get("ip_mode") == "private" for s in self.data_stores)


# ── Validation ────────────────────────────────────────────────────────────────


@dataclass
class Issue:
    field: str
    message: str
    gate: str = GATE_CONFIG


@dataclass
class ValidationResult:
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, field_: str, message: str, gate: str = GATE_CONFIG) -> None:
        self.errors.append(Issue(field_, message, gate))

    def add_warning(self, field_: str, message: str, gate: str = GATE_CONFIG) -> None:
        self.warnings.append(Issue(field_, message, gate))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": [asdict(i) for i in self.errors],
            "warnings": [asdict(i) for i in self.warnings],
        }


# Service-name rule mirrors goldenpath_ops.validate_service_name (kept in sync).
_NAME_MIN, _NAME_MAX = 3, 40


def validate_service_name(name: str) -> str | None:
    if not name:
        return "Service name is required."
    if not (_NAME_MIN <= len(name) <= _NAME_MAX):
        return f"Service name must be {_NAME_MIN}–{_NAME_MAX} characters."
    if not all(c.islower() or c.isdigit() or c == "-" for c in name):
        return "Use lowercase letters, digits, and hyphens only."
    if name[0] == "-" or name[-1] == "-":
        return "Service name cannot start or end with a hyphen."
    if "--" in name:
        return "Service name cannot contain consecutive hyphens."
    return None


def validate_config(
    cfg: ServiceConfig,
    catalog: dict[str, dict[str, Any]] | None = None,
    iam_report: dict[str, Any] | None = None,
    vpc_network: str | None = None,
) -> ValidationResult:
    """Validate a composed config against the full constraint matrix.

    Args:
        cfg: the composed service config.
        catalog: optional preloaded catalog (avoids disk reads in a UI loop).
        iam_report: optional output of a permission probe, shaped as
            ``{store_id: {"missing": [perm, ...]}}``. When present, missing
            permissions become permission-gated errors.
        vpc_network: name of a VPC network available for private IP; when
            falsy, private-IP stores are capability-gated off.
    """
    catalog = catalog if catalog is not None else load_catalog()
    result = ValidationResult()

    # 1. Service name
    name_err = validate_service_name(cfg.service_name)
    if name_err:
        result.add_error("service_name", name_err, GATE_CONFIG)

    # 2. Template
    if cfg.template not in catalog:
        result.add_error("template", f"Unknown template '{cfg.template}'.", GATE_CAPABILITY)
        return result  # nothing else is meaningful without a valid template
    caps = template_capabilities(cfg.template, catalog)

    # 3. Runtime ↔ template
    if cfg.runtime not in caps["runtimes"]:
        allowed = ", ".join(caps["runtimes"])
        result.add_error(
            "runtime",
            f"{cfg.template} supports runtime(s): {allowed}. '{cfg.runtime}' is not compatible.",
            GATE_CAPABILITY,
        )

    # 4. Deployment mode ↔ template
    if cfg.deployment_mode not in caps["deployment_modes"]:
        allowed = ", ".join(caps["deployment_modes"])
        result.add_error(
            "deployment_mode",
            f"{cfg.template} supports mode(s): {allowed}. '{cfg.deployment_mode}' is not available.",
            GATE_CAPABILITY,
        )

    # 5. Deployment mode ↔ data-store attachment
    if cfg.deployment_mode == MODE_STATIC and cfg.data_stores:
        if cfg.spa_strategy == SPA_NONE:
            result.add_error(
                "data_stores",
                "Static/SPA services cannot hold a direct database connection "
                "(credentials in the browser is an anti-pattern). Choose the "
                "'generate BFF' data-access strategy instead.",
                GATE_CAPABILITY,
            )
        elif cfg.spa_strategy == SPA_BFF:
            # BFF generation is not implemented in this release.
            result.add_error(
                "spa_strategy",
                "BFF generation is coming in a later release. For now, SPAs "
                "cannot attach a data store.",
                GATE_CAPABILITY,
            )

    # 6. Per-data-store validation
    for spec in cfg.data_stores:
        store = DATA_STORES.get(spec.id)
        prefix = f"data_stores.{spec.id}"
        if store is None:
            result.add_error(prefix, f"Unknown data store '{spec.id}'.", GATE_CONFIG)
            continue
        if not store.get("enabled"):
            result.add_error(
                prefix,
                f"{store['display_name']} support is coming in a later release.",
                GATE_CAPABILITY,
            )
            continue

        _validate_cloud_sql(spec, result, prefix, vpc_network)

        # Permission gate (only meaningful for enabled stores)
        if iam_report and spec.id in iam_report:
            missing = iam_report[spec.id].get("missing", [])
            for perm in missing:
                role = role_for_permission(spec.id, perm)
                result.add_error(
                    prefix,
                    f"Missing permission '{perm}' on the target project "
                    f"(grant {role}).",
                    GATE_PERMISSION,
                )

    # 7. Environments
    valid_envs = {"dev", "prod"}
    if not cfg.environments:
        result.add_error("environments", "Select at least one environment.", GATE_CONFIG)
    for env in cfg.environments:
        if env not in valid_envs:
            result.add_error(
                "environments",
                f"Environment '{env}' is not supported yet (dev, prod only).",
                GATE_CAPABILITY,
            )

    return result


def _validate_cloud_sql(
    spec: DataStoreSpec,
    result: ValidationResult,
    prefix: str,
    vpc_network: str | None,
) -> None:
    store = DATA_STORES["cloud_sql"]
    conf = spec.config

    # Engine
    engine = conf.get("engine", "postgresql")
    engine_meta = next((e for e in store["engines"] if e["value"] == engine), None)
    if engine_meta is None:
        result.add_error(f"{prefix}.engine", f"Unknown engine '{engine}'.", GATE_CONFIG)
    elif not engine_meta.get("enabled"):
        result.add_error(
            f"{prefix}.engine",
            f"Cloud SQL {engine_meta['label']} support is coming in a later release; "
            "PostgreSQL is available now.",
            GATE_CAPABILITY,
        )
    elif conf.get("version") and conf["version"] not in engine_meta["versions"]:
        allowed = ", ".join(engine_meta["versions"])
        result.add_error(
            f"{prefix}.version",
            f"Version '{conf['version']}' is not valid for {engine_meta['label']}. "
            f"Allowed: {allowed}.",
            GATE_CONFIG,
        )

    # IP mode ↔ VPC availability
    ip_mode = conf.get("ip_mode", store["default_ip_mode"])
    if ip_mode == "private" and not vpc_network:
        result.add_error(
            f"{prefix}.ip_mode",
            "Private IP requires a VPC network, but none is configured "
            "(set GCP_VPC_NETWORK in config/enterprise.env). Use public IP, or "
            "configure a network to enable private IP.",
            GATE_CAPABILITY,
        )
    if ip_mode == "private" and conf.get("vpc_enabled") is False:
        result.add_error(
            f"{prefix}.ip_mode",
            "Private IP requires Serverless VPC Access, but VPC provisioning was "
            "disabled. Re-enable VPC access or switch to public IP.",
            GATE_CONFIG,
        )


# ── UI option helpers (capability + permission merged) ───────────────────────


def _option(value: str, label: str, enabled: bool = True, reason: str = "", gate: str = "") -> dict:
    return {"value": value, "label": label, "enabled": enabled, "reason": reason, "gate": gate}


def template_options(catalog: dict[str, dict[str, Any]] | None = None) -> list[dict]:
    catalog = catalog if catalog is not None else load_catalog()
    opts = []
    for name, meta in catalog.items():
        label = meta.get("description", name)
        opts.append(_option(name, f"{name} — {label}"))
    return opts


def runtime_options(template: str, catalog: dict[str, dict[str, Any]] | None = None) -> list[dict]:
    caps = template_capabilities(template, catalog)
    return [_option(r, r.capitalize()) for r in caps["runtimes"]]


def mode_options(template: str, catalog: dict[str, dict[str, Any]] | None = None) -> list[dict]:
    caps = template_capabilities(template, catalog)
    labels = {MODE_SERVER: "Server (can hold DB connections)", MODE_STATIC: "Static / SPA (client-only)"}
    all_modes = [MODE_SERVER, MODE_STATIC]
    opts = []
    for m in all_modes:
        if m in caps["deployment_modes"]:
            opts.append(_option(m, labels[m]))
        else:
            opts.append(
                _option(
                    m,
                    labels[m],
                    enabled=False,
                    reason=f"{template} does not support {m} mode.",
                    gate=GATE_CAPABILITY,
                )
            )
    return opts


def data_store_options(
    deployment_mode: str,
    iam_report: dict[str, Any] | None = None,
    vpc_network: str | None = None,
) -> list[dict]:
    """Options for the data-store multiselect, merging both gates.

    ``iam_report`` is ``{store_id: {"missing": [...]}}`` from a live probe.
    """
    opts = []
    for store_id, store in DATA_STORES.items():
        label = store["display_name"]
        # Capability: not implemented yet
        if not store.get("enabled"):
            opts.append(
                _option(store_id, label, enabled=False, reason="Coming in a later release.", gate=GATE_CAPABILITY)
            )
            continue
        # Capability: static/SPA cannot attach directly (BFF not yet available)
        if deployment_mode == MODE_STATIC:
            opts.append(
                _option(
                    store_id,
                    label,
                    enabled=False,
                    reason="Client-only services can't attach a DB directly; BFF generation is coming later.",
                    gate=GATE_CAPABILITY,
                )
            )
            continue
        # Permission gate
        if iam_report and store_id in iam_report:
            missing = iam_report[store_id].get("missing", [])
            if missing:
                perm = missing[0]
                role = role_for_permission(store_id, perm)
                opts.append(
                    _option(
                        store_id,
                        label,
                        enabled=False,
                        reason=f"Missing '{perm}' (grant {role}).",
                        gate=GATE_PERMISSION,
                    )
                )
                continue
        opts.append(_option(store_id, label))
    return opts


def default_bff_framework(runtime: str) -> str:
    return BFF_FRAMEWORKS.get(runtime, "fastapi")

"""Golden Path MCP server — resources (skills/docs) + platform tools."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from goldenpath_mcp.audit import audit
from goldenpath_mcp.auth import wrap_with_api_key
from goldenpath_mcp.config import Settings
from goldenpath_mcp.content import ContentStore
from goldenpath_mcp.gcp import GcpError
from goldenpath_mcp.gcp import get_cost_estimate as gcp_get_cost_estimate
from goldenpath_mcp.gcp import get_deploy_status as gcp_get_deploy_status
from goldenpath_mcp.gcp import get_service_config as gcp_get_service_config
from goldenpath_mcp.gcp import list_services as gcp_list_services
from goldenpath_mcp.gcp import test_iam_permissions as gcp_test_iam_permissions
from goldenpath_mcp.github_ops import GitHubError
from goldenpath_mcp.github_ops import trigger_deploy as gh_trigger_deploy
from goldenpath_mcp.validate import validate_service

settings = Settings.from_env()
store = ContentStore(settings.repo_root)


def _load_composer():
    """Import the shared service_composer module from the platform repo.

    It is pure-stdlib and lives under scripts/setup; loading it here keeps the
    data-store permission catalog a single source of truth shared with the
    wizard and CLI.
    """
    import importlib
    import sys

    setup_dir = str(settings.repo_root / "scripts" / "setup")
    if setup_dir not in sys.path:
        sys.path.insert(0, setup_dir)
    return importlib.import_module("service_composer")


def _is_hosted() -> bool:
    return os.getenv("K_SERVICE") is not None or settings.host == "0.0.0.0"


def _transport_security() -> TransportSecuritySettings | None:
    """FastMCP defaults host=127.0.0.1 and enables localhost DNS rebinding rules."""
    if settings.host in ("127.0.0.1", "localhost", "::1"):
        return None
    # Cloud Run / container bind: API key auth; allow LB-forwarded Host headers.
    return TransportSecuritySettings(enable_dns_rebinding_protection=False)


mcp = FastMCP(
    "goldenpath",
    instructions=(
        "Shop Golden Path MCP server. Resources provide official skills and docs. "
        "Tools perform scaffold, deploy, and GCP lookups using the caller's credentials."
    ),
    host=settings.host,
    port=settings.port,
    transport_security=_transport_security(),
    # Cloud Run: no sticky sessions — each MCP HTTP request must stand alone.
    stateless_http=_is_hosted(),
)


# --- Resources (read-only virtual filesystem) ---


@mcp.resource("goldenpath://meta/version")
def resource_meta_version() -> str:
    return json.dumps(store.meta_version(settings.channel, settings.version), indent=2)


@mcp.resource("goldenpath://docs/{path}")
def resource_doc(path: str) -> str:
    return store.read_doc(path)


@mcp.resource("goldenpath://skills/{name}/SKILL.md")
def resource_skill(name: str) -> str:
    return store.read_skill(name)


# --- Read tools ---


@mcp.tool()
def list_templates() -> str:
    """List available Golden Path service templates from catalog.json."""
    catalog = store.read_catalog()
    return json.dumps(catalog, indent=2)


@mcp.tool()
def list_skills() -> str:
    """List official Golden Path agent skills available via MCP resources."""
    skills = store.list_skills()
    return json.dumps({"skills": skills, "channel": settings.channel, "version": settings.version}, indent=2)


@mcp.tool()
def get_skill(name: str) -> str:
    """Return SKILL.md content for an official skill (same as goldenpath://skills/{name}/SKILL.md)."""
    return store.read_skill(name)


@mcp.tool()
def get_doc(path: str) -> str:
    """Return a documentation file (same as goldenpath://docs/{path})."""
    return store.read_doc(path)


@mcp.tool()
def list_docs() -> str:
    """List available documentation paths under goldenpath://docs/."""
    return json.dumps({"docs": store.list_docs()}, indent=2)


@mcp.tool()
def get_version() -> str:
    """Return Golden Path release channel and version metadata."""
    return json.dumps(store.meta_version(settings.channel, settings.version), indent=2)


@mcp.tool()
def list_services(project: str | None = None, region: str | None = None) -> str:
    """List Golden Path Cloud Run services in a GCP project (uses caller gcloud auth)."""
    project = project or settings.gcp_project
    region = region or settings.gcp_region
    if not project:
        return json.dumps({"error": "project required: pass project= or set GCP_PROJECT"})
    try:
        services = gcp_list_services(project, region)
        return json.dumps({"project": project, "region": region, "services": services}, indent=2)
    except GcpError as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def get_deploy_status(
    service_name: str,
    environment: str = "dev",
    project: str | None = None,
    region: str | None = None,
) -> str:
    """Get Cloud Run deploy status for a Golden Path service."""
    project = project or settings.gcp_project
    region = region or settings.gcp_region
    if not project:
        return json.dumps({"error": "project required: pass project= or set GCP_PROJECT"})
    try:
        status = gcp_get_deploy_status(project, region, service_name, environment)
        return json.dumps(status, indent=2)
    except GcpError as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def get_service_config(
    service_name: str,
    environment: str = "dev",
    project: str | None = None,
    region: str | None = None,
) -> str:
    """Get Cloud Run configuration for a Golden Path service."""
    project = project or settings.gcp_project
    region = region or settings.gcp_region
    if not project:
        return json.dumps({"error": "project required: pass project= or set GCP_PROJECT"})
    try:
        config = gcp_get_service_config(project, region, service_name, environment)
        return json.dumps(config, indent=2)
    except GcpError as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def get_cost_estimate(
    service_name: str,
    environment: str = "dev",
    project: str | None = None,
) -> str:
    """Cost visibility notes and console link for a service (uses caller permissions)."""
    project = project or settings.gcp_project
    if not project:
        return json.dumps({"error": "project required: pass project= or set GCP_PROJECT"})
    return json.dumps(gcp_get_cost_estimate(project, service_name, environment), indent=2)


@mcp.tool()
def check_data_store_permissions(
    stores: str,
    project: str | None = None,
    ip_mode: str = "public",
) -> str:
    """Check whether the caller can create the given managed data store(s).

    ``stores`` is a comma-separated list (e.g. "cloud_sql"). Runs
    testIamPermissions for each store's required permissions and reports, per
    store, which permissions are missing and which role grants them — the same
    permission catalog the setup wizard uses to gate options.
    """
    project = project or settings.gcp_project
    if not project:
        return json.dumps({"error": "project required: pass project= or set GCP_PROJECT"})

    sc = _load_composer()
    store_ids = [s.strip() for s in stores.split(",") if s.strip()]
    report: dict = {}
    for sid in store_ids:
        if sid not in sc.DATA_STORES:
            report[sid] = {"error": f"unknown data store '{sid}'"}
            continue
        if not sc.DATA_STORES[sid].get("enabled"):
            report[sid] = {"enabled": False, "reason": "coming in a later release"}
            continue
        perms = sc.data_store_permissions(sid, ip_mode)
        try:
            granted = set(gcp_test_iam_permissions(project, perms))
        except GcpError as exc:
            report[sid] = {"error": str(exc)}
            continue
        missing = [p for p in perms if p not in granted]
        report[sid] = {
            "can_create": not missing,
            "missing": missing,
            "missing_roles": sorted({sc.role_for_permission(sid, p) for p in missing}),
        }
    return json.dumps({"project": project, "ip_mode": ip_mode, "stores": report}, indent=2)


# --- Write tools (audited) ---


@mcp.tool()
def scaffold_service(
    name: str,
    template: str = "nextjs",
    github_org: str = "",
    gcp_dev_project: str = "",
    gcp_prod_project: str = "",
    region: str = "",
    output_dir: str = "..",
    config: str = "",
) -> str:
    """Scaffold a new Golden Path service repo using the shop CLI (audited write).

    Pass ``config`` (a ServiceConfig JSON string — see the composer model) to
    compose a service with managed data stores, deployment mode, etc.; it drives
    the template and service name, and org/project values come from
    config/enterprise.env. Otherwise the simple template path is used.
    """
    shop = settings.shop_cli
    if not shop.is_file():
        return json.dumps({"error": f"shop CLI not found at {shop}"})

    config_file = None
    if config:
        # Validate against the shared composer before writing anything.
        try:
            sc = _load_composer()
            svc = sc.ServiceConfig.from_json(config)
        except Exception as exc:
            return json.dumps({"error": f"invalid config JSON: {exc}"})
        result = sc.validate_config(svc)
        if not result.ok:
            return json.dumps(
                {
                    "error": "config failed validation",
                    "issues": [
                        {"field": i.field, "gate": i.gate, "message": i.message}
                        for i in result.errors
                    ],
                }
            )
        import tempfile

        fd = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        fd.write(config)
        fd.close()
        config_file = fd.name
        name = svc.service_name
        template = svc.template
        cmd = [str(shop), "new", "--config", config_file, "--output", output_dir]
        audit("scaffold_service", name=name, template=template, config=True)
        return _run_scaffold(cmd, name, template, output_dir, config_file)

    if not github_org or not gcp_dev_project or not gcp_prod_project:
        return json.dumps(
            {
                "error": "github_org, gcp_dev_project, and gcp_prod_project are required",
                "hint": "Load deploy-to-shop-gcp skill for full runbook",
            }
        )

    if not region:
        region = settings.gcp_region
    if not region:
        return json.dumps(
            {
                "error": "region is required",
                "hint": "Set GCP_REGION in config/enterprise.env or pass region=",
            }
        )

    cmd = [
        str(shop),
        "new",
        name,
        "--template",
        template,
        "--github-org",
        github_org,
        "--gcp-dev",
        gcp_dev_project,
        "--gcp-prod",
        gcp_prod_project,
        "--region",
        region,
        "--output",
        output_dir,
    ]

    audit("scaffold_service", name=name, template=template, github_org=github_org)
    return _run_scaffold(cmd, name, template, output_dir, None)


def _run_scaffold(cmd, name, template, output_dir, config_file):
    """Run the shop CLI scaffold command and shape the JSON response."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=settings.repo_root)
        target_path = (Path(output_dir).resolve() / name)
        target = str(target_path)
        warnings: list[str] = []
        try:
            target_path.relative_to(settings.repo_root.resolve())
            warnings.append(
                "scaffold path is inside GOLDENPATH_ROOT — prefer output_dir='..' "
                "(parent of platform repo)"
            )
        except ValueError:
            pass
        payload: dict = {
            "status": "ok",
            "service": name,
            "template": template,
            "path": target,
            "stdout": result.stdout,
            "next_step": f"shop publish {target}",
        }
        if warnings:
            payload["warnings"] = warnings
        return json.dumps(payload, indent=2)
    except subprocess.CalledProcessError as exc:
        return json.dumps({"error": exc.stderr or exc.stdout or "scaffold failed"})
    finally:
        if config_file:
            try:
                os.unlink(config_file)
            except OSError:
                pass


@mcp.tool()
def validate_service_repo(path: str) -> str:
    """Check whether a directory is a valid Golden Path service repository."""
    return json.dumps(validate_service(path), indent=2)


@mcp.tool()
def trigger_deploy(
    github_repo: str,
    environment: str = "dev",
    workflow_file: str = "deploy.yml",
    ref: str = "main",
    confirm: bool = False,
) -> str:
    """Dispatch the service Deploy workflow on GitHub (audited write; requires confirm=true)."""
    if not confirm:
        return json.dumps(
            {
                "error": "confirmation required",
                "message": "Re-run with confirm=true to dispatch deploy",
                "github_repo": github_repo,
                "environment": environment,
            }
        )

    token = settings.github_token
    if not token:
        return json.dumps({"error": "GITHUB_TOKEN or GH_TOKEN required for trigger_deploy"})

    audit("trigger_deploy", repo=github_repo, environment=environment, ref=ref)
    try:
        result = gh_trigger_deploy(token, github_repo, workflow_file, environment, ref)
        return json.dumps(result, indent=2)
    except GitHubError as exc:
        return json.dumps({"error": str(exc)})


def _require_network_api_key(transport: str) -> str:
    if transport not in ("sse", "streamable-http"):
        raise ValueError(f"unexpected transport: {transport}")
    if not settings.api_key:
        raise SystemExit(
            "MCP_API_KEY is required for hosted transports (sse, streamable-http). "
            "Set MCP_API_KEY before starting the server."
        )
    return settings.api_key


async def _health(_request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "service": settings.mcp_service_name,
            "transport": settings.transport,
            "channel": settings.channel,
            "version": settings.version,
        }
    )


def _hosted_app(core_app: Starlette, api_key: str) -> Starlette:
    """Public /health for Cloud Run probes; MCP routes require API key."""
    protected = wrap_with_api_key(core_app, api_key)
    return Starlette(
        routes=[
            Route("/health", endpoint=_health),
            Mount("/", app=protected),
        ],
        # streamable-http initializes its session manager in router lifespan.
        lifespan=core_app.router.lifespan_context,
    )


async def _run_sse_async() -> None:
    import uvicorn

    api_key = _require_network_api_key("sse")
    mcp.settings.host = settings.host
    mcp.settings.port = settings.port
    app = _hosted_app(mcp.sse_app(), api_key)
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
    await uvicorn.Server(config).serve()


async def _run_streamable_http_async() -> None:
    import uvicorn

    api_key = _require_network_api_key("streamable-http")
    mcp.settings.host = settings.host
    mcp.settings.port = settings.port
    app = _hosted_app(mcp.streamable_http_app(), api_key)
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
    await uvicorn.Server(config).serve()


def run() -> None:
    import anyio

    transport = settings.transport.lower()
    if transport == "sse":
        anyio.run(_run_sse_async)
    elif transport == "streamable-http":
        anyio.run(_run_streamable_http_async)
    else:
        mcp.run(transport="stdio")
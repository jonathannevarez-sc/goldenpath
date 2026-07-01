#!/usr/bin/env python3
"""CLI entry point for goldenpath_ops — shared by bash, shop, and PowerShell.

Keeps scaffold / publish / doctor / upgrade behavior identical across wizard
backends without duplicating logic in shell scripts.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import goldenpath_ops as ops  # noqa: E402


def _config_path(args: argparse.Namespace) -> Path | None:
    if getattr(args, "config", None):
        return Path(args.config)
    override = os.environ.get("GOLDENPATH_OPS_CONFIG")
    return Path(override) if override else None


def _load_cfg(args: argparse.Namespace) -> dict:
    return ops.load_config(_config_path(args))


def _cmd_scaffold(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args)
    output = Path(args.output).resolve() if args.output else ops.get_scaffold_output_dir()
    result = ops.scaffold(args.name, args.template, output, cfg)
    print(f"SERVICE_DIR={result.service_dir}")
    print(f"HEALTH_PATH={result.health_check_path}")
    return 0


def _cmd_compose(args: argparse.Namespace) -> int:
    """Scaffold from a full ServiceConfig JSON (template + runtime + data stores)."""
    import service_composer as sc

    cfg = _load_cfg(args)
    try:
        svc = sc.ServiceConfig.from_json(Path(args.service_config).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR=invalid service-config: {exc}", file=sys.stderr)
        return 1

    result = sc.validate_config(svc)
    if not result.ok:
        for issue in result.errors:
            print(f"INVALID[{issue.gate}] {issue.field}: {issue.message}", file=sys.stderr)
        return 1

    output = Path(args.output).resolve() if args.output else ops.get_scaffold_output_dir()
    try:
        res = ops.scaffold(svc.service_name, svc.template, output, cfg, service_config=svc)
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        return 1
    print(f"SERVICE_DIR={res.service_dir}")
    print(f"HEALTH_PATH={res.health_check_path}")
    for note in res.data_store_notes or []:
        print(f"GENERATED={note}")
    return 0


def _cmd_print_config(args: argparse.Namespace) -> int:
    """Emit a starter ServiceConfig JSON (edit, then `shop new --config`)."""
    import service_composer as sc

    svc = sc.ServiceConfig(
        service_name=args.name or "my-service",
        template=args.template or "fastapi",
        runtime=args.runtime or "python",
        deployment_mode="server",
        data_stores=[
            sc.DataStoreSpec(
                "cloud_sql",
                {
                    "engine": "postgresql",
                    "version": "POSTGRES_16",
                    "tier": "db-f1-micro",
                    "high_availability": False,
                    "ip_mode": "public",
                    "database_name": "appdb",
                },
            )
        ],
        environments=["dev", "prod"],
    )
    print(svc.to_json())
    return 0


def _cmd_custom_scaffold(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args)
    output = Path(args.output).resolve() if args.output else ops.get_scaffold_output_dir()
    try:
        result = ops.generate_custom_template(
            name=args.name,
            runtime=args.runtime,
            port=args.port,
            health_path=args.health_path,
            output_dir=output,
            cfg=cfg,
        )
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        return 1
    print(f"SERVICE_DIR={result.service_dir}")
    print(f"HEALTH_PATH={result.health_check_path}")
    print(f"BASE_TEMPLATE={result.template}")
    return 0


def _cmd_publish(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args)
    provider = args.wif_provider or cfg.get("wif_provider", "")
    sa = args.wif_service_account or cfg.get("wif_service_account", "")
    try:
        result = ops.publish(
            Path(args.service_dir).resolve(),
            cfg,
            provider,
            sa,
            watch_deploy=not args.no_watch,
            on_step=lambda msg: print(msg, flush=True),
        )
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        return 1
    print(f"REPO={result.repo}")
    deploy_ok = result.deploy_ok
    print(f"DEPLOY_OK={deploy_ok if deploy_ok is not None else 'unknown'}")
    return 0 if deploy_ok is not False else 1


def _cmd_doctor(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args)
    issues = ops.service_doctor(Path(args.service_dir).resolve(), cfg)
    for issue in issues:
        print(f"ISSUE={issue}")
    return 1 if issues else 0


def _cmd_upgrade(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args)
    try:
        ops.upgrade_service(Path(args.service_dir).resolve(), cfg)
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        return 1
    print("UPGRADE_OK")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    cfg = _load_cfg(args)
    service_dir = Path(args.service_dir).resolve() if args.service_dir else None
    verify_cfg = {
        **cfg,
        "gcp_project": args.project or cfg.get("gcp_dev_project", ""),
        "gcp_region": args.region or cfg.get("gcp_region", ""),
    }
    result = ops.verify_deployment(
        args.cloud_run_service,
        verify_cfg,
        service_dir,
        max_attempts=args.max_attempts,
        retry_delay=args.retry_delay,
    )
    print(f"URL={result.url or ''}")
    print(f"HEALTH_OK={result.health_ok}")
    print(f"HEALTH_PATH={result.health_path or ''}")
    print(f"STATUS_CODE={result.status_code or ''}")
    print(f"ERROR={result.error or ''}")
    return 0 if result.health_ok or result.url else 1


def main(argv: list[str] | None = None) -> int:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--config",
        help="Config JSON path (default: .goldenpath-setup.local.json or GOLDENPATH_OPS_CONFIG)",
    )

    parser = argparse.ArgumentParser(
        description="Golden Path wizard operations (scaffold, publish, doctor, upgrade)",
        parents=[parent],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scaffold = sub.add_parser(
        "scaffold",
        help="Scaffold a service from a template",
        parents=[parent],
    )
    p_scaffold.add_argument("name", help="Service name (kebab-case)")
    p_scaffold.add_argument("template", help="Template id from catalog.json")
    p_scaffold.add_argument(
        "--output",
        help="Parent directory for the service folder (default: repo parent)",
    )
    p_scaffold.set_defaults(func=_cmd_scaffold)

    p_compose = sub.add_parser(
        "compose",
        help="Scaffold from a ServiceConfig JSON (data stores, deployment mode, etc.)",
        parents=[parent],
    )
    p_compose.add_argument("--service-config", required=True,
                           help="Path to a ServiceConfig JSON file")
    p_compose.add_argument("--output",
                           help="Parent directory for the service folder (default: repo parent)")
    p_compose.set_defaults(func=_cmd_compose)

    p_print = sub.add_parser(
        "print-config",
        help="Print a starter ServiceConfig JSON to stdout",
        parents=[parent],
    )
    p_print.add_argument("--name", default=None)
    p_print.add_argument("--template", default=None)
    p_print.add_argument("--runtime", default=None)
    p_print.set_defaults(func=_cmd_print_config)

    p_custom = sub.add_parser(
        "custom-scaffold",
        help="Generate a custom service scaffold when no catalog template matches",
        parents=[parent],
    )
    p_custom.add_argument("name", help="Service name (kebab-case)")
    p_custom.add_argument("--runtime", default="python", choices=["python", "node", "docker"],
                          help="Application runtime (default: python)")
    p_custom.add_argument("--port", type=int, default=8080,
                          help="Port the service listens on (default: 8080)")
    p_custom.add_argument("--health-path", default="/health",
                          help="Health check URL path (default: /health)")
    p_custom.add_argument("--output",
                          help="Parent directory for the service folder (default: repo parent)")
    p_custom.set_defaults(func=_cmd_custom_scaffold)

    p_publish = sub.add_parser(
        "publish",
        help="Publish service to GitHub and deploy",
        parents=[parent],
    )
    p_publish.add_argument("service_dir", help="Path to scaffolded service directory")
    p_publish.add_argument(
        "--no-watch", action="store_true", help="Skip gh run watch after push"
    )
    p_publish.add_argument("--wif-provider", default=None)
    p_publish.add_argument("--wif-service-account", default=None)
    p_publish.set_defaults(func=_cmd_publish)

    p_doctor = sub.add_parser(
        "doctor", help="Diagnose deploy blockers", parents=[parent]
    )
    p_doctor.add_argument("service_dir", help="Path to service directory")
    p_doctor.set_defaults(func=_cmd_doctor)

    p_upgrade = sub.add_parser(
        "upgrade",
        help="Bump deploy.yml + infra pins to enterprise.env",
        parents=[parent],
    )
    p_upgrade.add_argument("service_dir", help="Path to service directory")
    p_upgrade.set_defaults(func=_cmd_upgrade)

    p_verify = sub.add_parser(
        "verify",
        help="Verify Cloud Run deployment + health",
        parents=[parent],
    )
    p_verify.add_argument("cloud_run_service", help="Cloud Run service name")
    p_verify.add_argument("service_dir", nargs="?", default=None)
    p_verify.add_argument("--project", default=None)
    p_verify.add_argument("--region", default=None)
    p_verify.add_argument("--max-attempts", type=int, default=8)
    p_verify.add_argument("--retry-delay", type=int, default=8)
    p_verify.set_defaults(func=_cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
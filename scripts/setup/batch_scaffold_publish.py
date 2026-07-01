#!/usr/bin/env python3
"""Scaffold + publish one or more Golden Path services (non-interactive)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "setup"))

import goldenpath_ops as ops  # noqa: E402
import wizard_defaults as wd  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch scaffold and publish services")
    parser.add_argument(
        "pairs",
        nargs="+",
        help="template:service_name pairs, e.g. nextjs:gp-nextjs",
    )
    parser.add_argument(
        "--no-watch",
        action="store_true",
        help="Push only; do not wait for deploy workflow",
    )
    args = parser.parse_args()

    cfg = ops.load_config()
    if not cfg.get("wif_provider") or not cfg.get("wif_service_account"):
        print("error: WIF credentials missing in .goldenpath-setup.local.json", file=sys.stderr)
        return 1

    output = ops.get_scaffold_output_dir()
    results: list[dict] = []

    for pair in args.pairs:
        if ":" not in pair:
            print(f"error: expected template:service_name, got {pair!r}", file=sys.stderr)
            return 1
        template, service_name = pair.split(":", 1)
        print(f"\n==> {template} -> {service_name}", flush=True)
        target = output / service_name
        try:
            if target.exists() and any(target.iterdir()):
                print(f"  scaffold skip (exists): {target}", flush=True)
                service_dir = target
                version = wd.resolve_goldenpath_version(REPO_ROOT)
                ops.upgrade_platform_version_refs(service_dir, version)
                org = cfg.get("github_org") or wd.platform_default("GITHUB_ORG", REPO_ROOT)
                platform = cfg.get("github_platform_repo") or wd.platform_default(
                    "PLATFORM_REPO", REPO_ROOT
                )
                import re

                for path in service_dir.rglob("*"):
                    if not path.is_file() or ".git" in path.parts or ".terraform" in path.parts:
                        continue
                    if path.suffix not in (".yml", ".yaml", ".tf", ".tfvars"):
                        continue
                    raw = path.read_text(encoding="utf-8")
                    new = raw
                    for pat, repl in [
                        (re.compile(r"av-sparqgit/goldenpath"), f"{org}/{platform}"),
                        (re.compile(r"goldenpath_org:\s*\S+"), f"goldenpath_org: {org}"),
                        (re.compile(r"github\.com/av-sparqgit/"), f"github.com/{org}/"),
                    ]:
                        new = pat.sub(repl, new)
                    if new != raw:
                        path.write_text(new, encoding="utf-8")
                if (service_dir / ".git").exists():
                    status = ops.run_cmd(["git", "status", "--porcelain"], cwd=service_dir)
                    if status.stdout.strip():
                        ops.run_cmd(["git", "add", "-A"], cwd=service_dir)
                        ops.run_cmd(
                            [
                                "git",
                                "commit",
                                "-m",
                                f"chore: bump to {version} ({org})",
                            ],
                            cwd=service_dir,
                        )
            else:
                result = ops.scaffold(service_name, template, output, cfg)
                service_dir = result.service_dir
                print(f"  scaffolded: {service_dir}", flush=True)

            pub = ops.publish(
                service_dir,
                cfg,
                cfg["wif_provider"],
                cfg["wif_service_account"],
                watch_deploy=not args.no_watch,
                on_step=lambda m: print(f"  {m}", flush=True),
            )
            results.append(
                {
                    "service": service_name,
                    "template": template,
                    "repo": pub.repo,
                    "deploy_ok": pub.deploy_ok,
                    "dir": str(service_dir),
                }
            )
            status = "OK" if pub.deploy_ok else ("PUSHED" if pub.deploy_ok is None else "DEPLOY_FAILED")
            print(f"  publish {status}: {pub.repo}", flush=True)
        except Exception as exc:
            print(f"  FAILED: {exc}", file=sys.stderr)
            results.append(
                {"service": service_name, "template": template, "error": str(exc)}
            )

    print("\n==> SUMMARY", flush=True)
    print(json.dumps(results, indent=2))
    return 0 if all("error" not in r for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
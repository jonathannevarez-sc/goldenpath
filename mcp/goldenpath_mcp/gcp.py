"""GCP helpers — gcloud CLI locally, ADC on Cloud Run (runtime service account)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

from goldenpath_mcp import gcp_adc


class GcpError(Exception):
    pass


def _hosted_runtime() -> bool:
    """Cloud Run sets K_SERVICE; prefer ADC there instead of gcloud."""
    return bool(os.getenv("K_SERVICE")) or os.getenv("GOLDENPATH_GCP_USE_ADC", "").lower() in (
        "1",
        "true",
        "yes",
    )


def _gcloud_available() -> bool:
    return shutil.which("gcloud") is not None


def _run_gcloud(args: list[str]) -> Any:
    cmd = ["gcloud", *args, "--format=json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise GcpError("gcloud CLI not found; install Google Cloud SDK") from exc
    except subprocess.CalledProcessError as exc:
        raise GcpError(exc.stderr.strip() or exc.stdout.strip() or "gcloud failed") from exc

    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def list_services(project: str, region: str) -> list[dict[str, Any]]:
    if _hosted_runtime() or not _gcloud_available():
        try:
            return gcp_adc.list_services(project, region)
        except Exception as exc:
            raise GcpError(str(exc)) from exc

    data = _run_gcloud(
        [
            "run",
            "services",
            "list",
            f"--project={project}",
            f"--region={region}",
        ]
    )
    services = []
    for item in data or []:
        meta = item.get("metadata", {})
        status = item.get("status", {})
        labels = meta.get("labels", {})
        if labels.get("managed_by") != "goldenpath":
            continue
        services.append(
            {
                "name": meta.get("name"),
                "url": status.get("url"),
                "service": labels.get("service"),
                "environment": labels.get("environment"),
                "last_transition_time": status.get("latestCreatedRevisionName"),
            }
        )
    return services


def get_deploy_status(project: str, region: str, service_name: str, environment: str) -> dict[str, Any]:
    if _hosted_runtime() or not _gcloud_available():
        try:
            return gcp_adc.get_deploy_status(project, region, service_name, environment)
        except Exception as exc:
            raise GcpError(str(exc)) from exc

    run_service = f"{service_name}-{environment}"
    data = _run_gcloud(
        [
            "run",
            "services",
            "describe",
            run_service,
            f"--project={project}",
            f"--region={region}",
        ]
    )
    status = data.get("status", {})
    spec = data.get("spec", {})
    template = spec.get("template", {})
    containers = template.get("spec", {}).get("containers", [])
    image = containers[0].get("image") if containers else None

    conditions = status.get("conditions", [])
    ready = next((c for c in conditions if c.get("type") == "Ready"), {})

    return {
        "cloud_run_service": run_service,
        "url": status.get("url"),
        "image": image,
        "ready": ready.get("status"),
        "message": ready.get("message"),
        "latest_revision": status.get("latestReadyRevisionName"),
    }


def get_service_config(project: str, region: str, service_name: str, environment: str) -> dict[str, Any]:
    if _hosted_runtime() or not _gcloud_available():
        try:
            return gcp_adc.get_service_config(project, region, service_name, environment)
        except Exception as exc:
            raise GcpError(str(exc)) from exc

    run_service = f"{service_name}-{environment}"
    data = _run_gcloud(
        [
            "run",
            "services",
            "describe",
            run_service,
            f"--project={project}",
            f"--region={region}",
        ]
    )
    spec = data.get("spec", {})
    template = spec.get("template", {})
    meta = data.get("metadata", {})
    scaling = template.get("scaling", {})

    return {
        "name": run_service,
        "labels": meta.get("labels", {}),
        "service_account": template.get("serviceAccount"),
        "min_instances": scaling.get("minInstanceCount"),
        "max_instances": scaling.get("maxInstanceCount"),
        "region": region,
        "project": project,
    }


def test_iam_permissions(project: str, permissions: list[str]) -> list[str]:
    """Return the subset of ``permissions`` the caller holds on ``project``.

    gcloud locally, ADC (Resource Manager REST) on hosted runtime.
    """
    if not permissions:
        return []
    if _hosted_runtime() or not _gcloud_available():
        try:
            return gcp_adc.test_iam_permissions(project, permissions)
        except Exception as exc:
            raise GcpError(str(exc)) from exc

    data = _run_gcloud(
        [
            "projects",
            "test-iam-permissions",
            project,
            f"--permissions={','.join(permissions)}",
        ]
    )
    return list((data or {}).get("permissions", []))


def get_cost_estimate(project: str, service_name: str, environment: str) -> dict[str, Any]:
    """Cost visibility guidance — detailed billing requires Billing API permissions."""
    return {
        "service": service_name,
        "environment": environment,
        "project": project,
        "estimate": "Use GCP Billing console for exact costs",
        "golden_path_notes": [
            "zero_cost profile: scale-to-zero when idle (~$0 compute)",
            "Artifact Registry storage: ~$0.10/GB/month",
            "Secret Manager: cents per active secret version",
        ],
        "console_url": f"https://console.cloud.google.com/run/detail?project={project}",
    }
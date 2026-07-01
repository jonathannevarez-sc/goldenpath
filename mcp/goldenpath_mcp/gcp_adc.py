"""GCP lookups via Application Default Credentials (Cloud Run runtime SA)."""

from __future__ import annotations

from typing import Any

from google.cloud import run_v2


def _run_service_name(service_name: str, environment: str) -> str:
    return f"{service_name}-{environment}"


def list_services(project: str, region: str) -> list[dict[str, Any]]:
    client = run_v2.ServicesClient()
    parent = f"projects/{project}/locations/{region}"
    services: list[dict[str, Any]] = []

    for item in client.list_services(parent=parent):
        labels = dict(item.labels or {})
        if labels.get("managed_by") != "goldenpath":
            continue
        services.append(
            {
                "name": item.name.split("/")[-1] if item.name else None,
                "url": item.uri,
                "service": labels.get("service"),
                "environment": labels.get("environment"),
                "last_transition_time": item.latest_ready_revision,
            }
        )
    return services


def get_deploy_status(project: str, region: str, service_name: str, environment: str) -> dict[str, Any]:
    client = run_v2.ServicesClient()
    run_service = _run_service_name(service_name, environment)
    name = f"projects/{project}/locations/{region}/services/{run_service}"
    data = client.get_service(name=name)

    ready = next((c for c in data.conditions if c.type_ == "Ready"), None)
    image = None
    if data.template and data.template.containers:
        image = data.template.containers[0].image

    return {
        "cloud_run_service": run_service,
        "url": data.uri,
        "image": image,
        "ready": ready.state.name if ready and ready.state else None,
        "message": ready.message if ready else None,
        "latest_revision": data.latest_ready_revision,
    }


def get_service_config(project: str, region: str, service_name: str, environment: str) -> dict[str, Any]:
    client = run_v2.ServicesClient()
    run_service = _run_service_name(service_name, environment)
    name = f"projects/{project}/locations/{region}/services/{run_service}"
    data = client.get_service(name=name)
    template = data.template

    return {
        "name": run_service,
        "labels": dict(data.labels or {}),
        "service_account": template.service_account if template else None,
        "min_instances": template.scaling.min_instance_count if template and template.scaling else None,
        "max_instances": template.scaling.max_instance_count if template and template.scaling else None,
        "region": region,
        "project": project,
    }
"""Tests for mcp/goldenpath_mcp/gcp.py."""

from __future__ import annotations

import json
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

# gcp_adc imports google.cloud.run_v2 — not required for unit tests
for _mod in ("google", "google.cloud", "google.cloud.run_v2"):
    sys.modules.setdefault(_mod, MagicMock())

from goldenpath_mcp.gcp import GcpError, _run_gcloud, get_deploy_status, get_service_config, list_services


def test_run_gcloud_parses_json() -> None:
    payload = [{"metadata": {"name": "svc"}}]
    with patch("goldenpath_mcp.gcp.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout=json.dumps(payload), stderr="")
        data = _run_gcloud(["run", "services", "list"])
    assert data == payload


def test_run_gcloud_missing_cli() -> None:
    with patch("goldenpath_mcp.gcp.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(GcpError, match="gcloud CLI not found"):
            _run_gcloud(["projects", "list"])


def test_run_gcloud_process_error() -> None:
    err = subprocess.CalledProcessError(1, "gcloud", stderr="permission denied")
    with patch("goldenpath_mcp.gcp.subprocess.run", side_effect=err):
        with pytest.raises(GcpError, match="permission denied"):
            _run_gcloud(["run", "services", "list"])


def test_list_services_filters_goldenpath_labels() -> None:
    payload = [
        {
            "metadata": {
                "name": "orders-api-dev",
                "labels": {"managed_by": "goldenpath", "service": "orders-api", "environment": "dev"},
            },
            "status": {"url": "https://example.run.app", "latestCreatedRevisionName": "rev-1"},
        },
        {
            "metadata": {"name": "other-svc", "labels": {"managed_by": "other"}},
            "status": {},
        },
    ]
    with patch("goldenpath_mcp.gcp._hosted_runtime", return_value=False), patch(
        "goldenpath_mcp.gcp._gcloud_available", return_value=True
    ), patch("goldenpath_mcp.gcp._run_gcloud", return_value=payload):
        services = list_services("my-project", "us-central1")
    assert len(services) == 1
    assert services[0]["name"] == "orders-api-dev"
    assert services[0]["service"] == "orders-api"


def test_get_deploy_status_parses_gcloud_describe() -> None:
    payload = {
        "metadata": {"name": "orders-api-dev"},
        "status": {
            "url": "https://orders-api-dev.run.app",
            "latestReadyRevisionName": "orders-api-dev-00001",
            "conditions": [{"type": "Ready", "status": "True", "message": "Ready"}],
        },
        "spec": {
            "template": {
                "spec": {
                    "containers": [{"image": "us-central1-docker.pkg.dev/p/repo/orders-api:abc"}],
                }
            }
        },
    }
    with patch("goldenpath_mcp.gcp._hosted_runtime", return_value=False), patch(
        "goldenpath_mcp.gcp._gcloud_available", return_value=True
    ), patch("goldenpath_mcp.gcp._run_gcloud", return_value=payload):
        status = get_deploy_status("my-project", "us-central1", "orders-api", "dev")
    assert status["cloud_run_service"] == "orders-api-dev"
    assert status["ready"] == "True"
    assert status["url"] == "https://orders-api-dev.run.app"


def test_get_service_config_parses_scaling_and_labels() -> None:
    payload = {
        "metadata": {
            "name": "orders-api-dev",
            "labels": {"managed_by": "goldenpath", "service": "orders-api"},
        },
        "spec": {
            "template": {
                "serviceAccount": "orders-api@p.iam.gserviceaccount.com",
                "scaling": {"minInstanceCount": 0, "maxInstanceCount": 5},
            }
        },
    }
    with patch("goldenpath_mcp.gcp._hosted_runtime", return_value=False), patch(
        "goldenpath_mcp.gcp._gcloud_available", return_value=True
    ), patch("goldenpath_mcp.gcp._run_gcloud", return_value=payload):
        config = get_service_config("my-project", "us-central1", "orders-api", "dev")
    assert config["name"] == "orders-api-dev"
    assert config["service_account"] == "orders-api@p.iam.gserviceaccount.com"
    assert config["min_instances"] == 0
    assert config["max_instances"] == 5
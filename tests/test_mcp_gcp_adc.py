"""Tests for mcp/goldenpath_mcp/gcp_adc.py (ADC / run_v2 client path)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from goldenpath_mcp import gcp_adc


def _service_item(
    *,
    name: str = "projects/p/locations/r/services/orders-api-dev",
    uri: str = "https://orders-api-dev.run.app",
    labels: dict | None = None,
    revision: str = "orders-api-dev-00001",
) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        uri=uri,
        labels=labels or {
            "managed_by": "goldenpath",
            "service": "orders-api",
            "environment": "dev",
        },
        latest_ready_revision=revision,
    )


def _ready_service(
    *,
    run_service: str = "orders-api-dev",
    ready_state: str = "CONDITION_SUCCEEDED",
    image: str = "us-central1-docker.pkg.dev/p/repo/orders-api:abc",
) -> SimpleNamespace:
    ready = SimpleNamespace(type_="Ready", state=SimpleNamespace(name=ready_state), message="Ready")
    other = SimpleNamespace(type_="RoutesReady", state=SimpleNamespace(name="CONDITION_SUCCEEDED"), message="")
    container = SimpleNamespace(image=image)
    scaling = SimpleNamespace(min_instance_count=0, max_instance_count=3)
    template = SimpleNamespace(
        containers=[container],
        service_account="orders-api@p.iam.gserviceaccount.com",
        scaling=scaling,
    )
    return SimpleNamespace(
        name=f"projects/p/locations/us-central1/services/{run_service}",
        uri="https://orders-api-dev.run.app",
        labels={"managed_by": "goldenpath", "service": "orders-api", "environment": "dev"},
        latest_ready_revision="orders-api-dev-00001",
        conditions=[other, ready],
        template=template,
    )


def test_list_services_filters_goldenpath_labels() -> None:
    client = MagicMock()
    client.list_services.return_value = [
        _service_item(),
        _service_item(
            name="projects/p/locations/r/services/other",
            uri="https://other.run.app",
            labels={"managed_by": "other"},
        ),
    ]
    with patch("goldenpath_mcp.gcp_adc.run_v2.ServicesClient", return_value=client):
        services = gcp_adc.list_services("my-project", "us-central1")
    assert len(services) == 1
    assert services[0]["name"] == "orders-api-dev"
    assert services[0]["service"] == "orders-api"


def test_get_deploy_status_reads_ready_condition() -> None:
    client = MagicMock()
    client.get_service.return_value = _ready_service()
    with patch("goldenpath_mcp.gcp_adc.run_v2.ServicesClient", return_value=client):
        status = gcp_adc.get_deploy_status("my-project", "us-central1", "orders-api", "dev")
    assert status["cloud_run_service"] == "orders-api-dev"
    assert status["ready"] == "CONDITION_SUCCEEDED"
    assert status["image"].endswith(":abc")
    client.get_service.assert_called_once_with(
        name="projects/my-project/locations/us-central1/services/orders-api-dev"
    )


def test_get_service_config_returns_scaling_and_sa() -> None:
    client = MagicMock()
    client.get_service.return_value = _ready_service()
    with patch("goldenpath_mcp.gcp_adc.run_v2.ServicesClient", return_value=client):
        config = gcp_adc.get_service_config("my-project", "us-central1", "orders-api", "dev")
    assert config["name"] == "orders-api-dev"
    assert config["service_account"] == "orders-api@p.iam.gserviceaccount.com"
    assert config["min_instances"] == 0
    assert config["max_instances"] == 3
    assert config["labels"]["managed_by"] == "goldenpath"


def test_get_deploy_status_propagates_client_errors() -> None:
    client = MagicMock()
    client.get_service.side_effect = RuntimeError("permission denied")
    with patch("goldenpath_mcp.gcp_adc.run_v2.ServicesClient", return_value=client):
        with pytest.raises(RuntimeError, match="permission denied"):
            gcp_adc.get_deploy_status("my-project", "us-central1", "orders-api", "dev")
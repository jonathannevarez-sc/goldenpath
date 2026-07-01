# Serverless VPC Access connector — lets Cloud Run reach private-IP resources
# (Cloud SQL/AlloyDB private IP) inside a VPC network.

locals {
  # Connector names are limited to 25 chars; derive a stable, sanitized name.
  connector_name = coalesce(
    var.connector_name,
    substr(replace("${var.service_name}-${var.environment}", "_", "-"), 0, 25),
  )
}

resource "google_project_service" "vpcaccess" {
  count              = var.enable_apis ? 1 : 0
  project            = var.project_id
  service            = "vpcaccess.googleapis.com"
  disable_on_destroy = false
}

resource "google_vpc_access_connector" "connector" {
  project = var.project_id
  region  = var.region
  name    = local.connector_name

  network       = var.network
  ip_cidr_range = var.ip_cidr_range

  min_instances = var.min_instances
  max_instances = var.max_instances

  depends_on = [google_project_service.vpcaccess]
}

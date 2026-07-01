# Cloud SQL (PostgreSQL) with IAM database authentication.
#
# Golden Path defaults:
#   * IAM DB auth ON — the runtime service account connects with an OAuth token;
#     no password is ever created or stored in Secret Manager.
#   * Least privilege — the runtime SA gets roles/cloudsql.client (connect) and
#     roles/cloudsql.instanceUser (IAM login), nothing more.
#   * Public IP by default (deployable without a preconfigured VPC); private IP
#     is available when a VPC network is supplied.

locals {
  instance_name = replace("${var.service_name}-${var.environment}-sql", "_", "-")
  is_private    = var.ip_mode == "private"

  # Cloud SQL IAM user names are the SA email without the trailing domain.
  iam_user = trimsuffix(var.runtime_service_account_email, ".gserviceaccount.com")

  base_apis = ["sqladmin.googleapis.com"]
  vpc_apis  = ["servicenetworking.googleapis.com", "compute.googleapis.com"]
  apis      = var.enable_apis ? toset(concat(local.base_apis, local.is_private ? local.vpc_apis : [])) : toset([])
}

resource "google_project_service" "apis" {
  for_each           = local.apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ── Private services access (only for private IP) ─────────────────────────────

resource "google_compute_global_address" "private_range" {
  count         = local.is_private ? 1 : 0
  project       = var.project_id
  name          = "${local.instance_name}-psa"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = var.network

  depends_on = [google_project_service.apis]
}

resource "google_service_networking_connection" "private_vpc" {
  count                   = local.is_private ? 1 : 0
  network                 = var.network
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_range[0].name]
}

# ── Instance ──────────────────────────────────────────────────────────────────

resource "google_sql_database_instance" "main" {
  project          = var.project_id
  name             = local.instance_name
  region           = var.region
  database_version = var.database_version

  deletion_protection = var.deletion_protection

  settings {
    tier              = var.tier
    edition           = var.edition
    availability_type = var.high_availability ? "REGIONAL" : "ZONAL"

    # Enable IAM database authentication.
    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    ip_configuration {
      ipv4_enabled    = local.is_private ? false : true
      private_network = local.is_private ? var.network : null
    }

    backup_configuration {
      enabled = true
    }
  }

  depends_on = [
    google_project_service.apis,
    google_service_networking_connection.private_vpc,
  ]
}

resource "google_sql_database" "app" {
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  name     = var.database_name
}

# IAM database user backed by the runtime service account (no password).
resource "google_sql_user" "iam_sa" {
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  name     = local.iam_user
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}

# ── Least-privilege IAM for the runtime SA ────────────────────────────────────

resource "google_project_iam_member" "client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = var.runtime_service_account_member
}

resource "google_project_iam_member" "instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = var.runtime_service_account_member
}

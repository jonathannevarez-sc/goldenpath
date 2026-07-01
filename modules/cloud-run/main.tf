locals {
  name = "${var.service_name}-${var.environment}"

  # Golden Path: images MUST live in this project's regional Artifact Registry.
  image_name = coalesce(var.image_name, var.service_name)
  image      = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/${local.image_name}:${var.image_tag}"

  # Zero-cost profile: no idle instances, request-based CPU billing, modest limits.
  min_instances     = var.zero_cost ? 0 : var.min_instances
  max_instances     = var.zero_cost ? var.max_instances_zero_cost : var.max_instances
  cpu               = coalesce(var.cpu, var.zero_cost ? "0.5" : "1")
  memory            = coalesce(var.memory, "512Mi")
  cpu_idle          = coalesce(var.cpu_idle, var.zero_cost ? true : false)
  startup_cpu_boost = coalesce(var.startup_cpu_boost, var.zero_cost ? false : true)
}

resource "google_cloud_run_v2_service" "service" {
  project  = var.project_id
  name     = local.name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  labels = {
    service      = var.service_name
    environment  = var.environment
    managed_by   = "goldenpath"
    cost_profile = var.zero_cost ? "scale-to-zero" : "standard"
  }

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = local.min_instances
      max_instance_count = local.max_instances
    }

    # Serverless VPC Access — required to reach private-IP data stores.
    dynamic "vpc_access" {
      for_each = var.vpc_connector == null ? [] : [1]
      content {
        connector = var.vpc_connector
        egress    = var.vpc_egress
      }
    }

    containers {
      image = local.image
      ports {
        container_port = var.port
      }

      resources {
        limits = {
          cpu    = local.cpu
          memory = local.memory
        }
        cpu_idle          = local.cpu_idle
        startup_cpu_boost = local.startup_cpu_boost
      }

      dynamic "env" {
        for_each = var.env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secret_env
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      startup_probe {
        http_get {
          path = var.health_check_path
          port = var.port
        }
        initial_delay_seconds = 5
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = var.health_check_path
          port = var.port
        }
        timeout_seconds   = 3
        period_seconds    = 30
        failure_threshold = 3
      }
    }
  }

  lifecycle {
    precondition {
      condition     = can(regex("^${var.region}-docker\\.pkg\\.dev/${var.project_id}/", local.image))
      error_message = "Golden Path requires Artifact Registry images: {region}-docker.pkg.dev/{project_id}/{repo}/{name}:{tag}. External registries are not allowed."
    }
  }
}

# Runtime SA must read images from Artifact Registry (Golden Path does not use GCR/Docker Hub).
resource "google_artifact_registry_repository_iam_member" "runtime_reader" {
  project    = var.project_id
  location   = var.region
  repository = var.artifact_registry_repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${var.service_account_email}"
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
resource "google_artifact_registry_repository" "services" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_id
  description   = "Golden Path container images"
  format        = "DOCKER"
}
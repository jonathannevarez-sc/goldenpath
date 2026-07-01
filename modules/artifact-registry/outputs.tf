output "repository_id" {
  value = google_artifact_registry_repository.services.repository_id
}

output "repository_url" {
  description = "Docker repository URL prefix (without image name/tag)"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.services.repository_id}"
}
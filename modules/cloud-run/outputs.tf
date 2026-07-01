output "name" {
  value = google_cloud_run_v2_service.service.name
}

output "image" {
  description = "Artifact Registry image URL deployed to Cloud Run"
  value       = local.image
}

output "uri" {
  value = google_cloud_run_v2_service.service.uri
}

output "location" {
  value = google_cloud_run_v2_service.service.location
}
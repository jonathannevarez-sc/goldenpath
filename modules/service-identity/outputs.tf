output "email" {
  description = "Runtime service account email"
  value       = google_service_account.runtime.email
  depends_on  = [time_sleep.wait_for_sa]
}

output "name" {
  description = "Runtime service account resource name"
  value       = google_service_account.runtime.name
}

output "member" {
  description = "IAM member string for the runtime service account"
  value       = "serviceAccount:${google_service_account.runtime.email}"
  depends_on  = [time_sleep.wait_for_sa]
}
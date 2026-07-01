output "dashboard_name" {
  value = google_monitoring_dashboard.service.id
}

output "alert_policy_name" {
  value = google_monitoring_alert_policy.high_error_rate.name
}
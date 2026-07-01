output "instance_connection_name" {
  description = "INSTANCE_CONNECTION_NAME for the language connectors (project:region:instance)"
  value       = google_sql_database_instance.main.connection_name
}

output "instance_name" {
  value = google_sql_database_instance.main.name
}

output "database" {
  description = "Application database name"
  value       = google_sql_database.app.name
}

output "iam_user" {
  description = "IAM DB username the runtime SA connects as (SA email minus domain)"
  value       = google_sql_user.iam_sa.name
}

output "private_ip_address" {
  description = "Private IP (empty for public instances)"
  value       = google_sql_database_instance.main.private_ip_address
}

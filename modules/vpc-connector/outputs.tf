output "id" {
  description = "Connector ID for Cloud Run vpc_access.connector"
  value       = google_vpc_access_connector.connector.id
}

output "name" {
  description = "Connector name"
  value       = google_vpc_access_connector.connector.name
}

output "self_link" {
  value = google_vpc_access_connector.connector.self_link
}

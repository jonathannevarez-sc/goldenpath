output "secret_ids" {
  value = [for s in google_secret_manager_secret.secrets : s.secret_id]
}

output "secret_resource_names" {
  value = { for k, s in google_secret_manager_secret.secrets : k => s.name }
}
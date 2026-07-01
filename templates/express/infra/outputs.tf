output "url" {
  value = module.cloud_run.uri
}

output "cloud_run_service" {
  value = module.cloud_run.name
}
output "dev_artifact_registry_url" {
  value = module.artifact_registry_dev.repository_url
}

output "prod_artifact_registry_url" {
  value = var.personal_test ? module.artifact_registry_dev.repository_url : module.artifact_registry_prod[0].repository_url
}

output "dev_github_wif_provider_name" {
  description = "Full WIF provider resource name for GitHub Actions (dev)"
  value       = google_iam_workload_identity_pool_provider.github["dev"].name
}

output "prod_github_wif_provider_name" {
  description = "Full WIF provider resource name for GitHub Actions (prod; same as dev in personal_test)"
  value       = var.personal_test ? google_iam_workload_identity_pool_provider.github["dev"].name : google_iam_workload_identity_pool_provider.github["prod"].name
}

output "dev_github_actions_sa_email" {
  value = google_service_account.github_actions["dev"].email
}

output "prod_github_actions_sa_email" {
  value = var.personal_test ? google_service_account.github_actions["dev"].email : google_service_account.github_actions["prod"].email
}

output "personal_test" {
  value = var.personal_test
}

output "project_id" {
  description = "Primary project (test project in personal_test mode)"
  value       = local.dev_project
}
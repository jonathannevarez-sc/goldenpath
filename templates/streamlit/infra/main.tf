provider "google" {
  project = var.project_id
  region  = var.region
}

module "identity" {
  source = "git::https://github.com/{{GITHUB_ORG}}/{{PLATFORM_REPO}}.git//modules/service-identity?ref={{GOLDENPATH_VERSION}}"

  project_id   = var.project_id
  service_name = var.service_name
  environment  = var.environment
}

module "secrets" {
  source = "git::https://github.com/{{GITHUB_ORG}}/{{PLATFORM_REPO}}.git//modules/secrets?ref={{GOLDENPATH_VERSION}}"

  project_id   = var.project_id
  service_name = var.service_name
  environment  = var.environment
  secret_ids   = ["app-config"]

  accessor_members = [module.identity.member]
}

module "cloud_run" {
  source = "git::https://github.com/{{GITHUB_ORG}}/{{PLATFORM_REPO}}.git//modules/cloud-run?ref={{GOLDENPATH_VERSION}}"

  project_id                      = var.project_id
  region                          = var.region
  service_name                    = var.service_name
  environment                     = var.environment
  artifact_registry_repository_id = var.artifact_registry_repo
  image_name                      = var.service_name
  image_tag                       = var.image_tag
  service_account_email           = module.identity.email
  allow_unauthenticated           = var.environment == "dev"
  zero_cost                       = var.zero_cost
  port                            = var.container_port
  health_check_path               = var.health_check_path

  env = {
    SERVICE_NAME = var.service_name
    ENVIRONMENT  = var.environment
  }

  secret_env = {
    APP_CONFIG = module.secrets.secret_resource_names["app-config"]
  }
}

module "observability" {
  source = "git::https://github.com/{{GITHUB_ORG}}/{{PLATFORM_REPO}}.git//modules/observability?ref={{GOLDENPATH_VERSION}}"

  project_id             = var.project_id
  service_name           = var.service_name
  environment            = var.environment
  cloud_run_service_name = module.cloud_run.name
}
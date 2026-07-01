provider "google" {
  project = var.project_id
  region  = var.region
}

module "identity" {
  source = "../../modules/service-identity"

  project_id   = var.project_id
  service_name = var.service_name
  environment  = var.environment
}

locals {
  secret_ids = var.enable_github_token ? ["mcp-api-key", "github-token"] : ["mcp-api-key"]
}

module "secrets" {
  source = "../../modules/secrets"

  project_id   = var.project_id
  service_name = var.service_name
  environment  = var.environment
  secret_ids   = local.secret_ids

  accessor_members = [module.identity.member]
}

# API key lives in Secret Manager (bootstrap placeholder, then operator or seed script).
data "google_secret_manager_secret_version" "mcp_api_key" {
  secret  = module.secrets.secret_resource_names["mcp-api-key"]
  version = "latest"
}

resource "google_secret_manager_secret_version" "github_token" {
  count = var.enable_github_token ? 1 : 0

  secret      = module.secrets.secret_resource_names["github-token"]
  secret_data = var.github_token
}

resource "google_project_iam_member" "mcp_run_viewer" {
  project = var.project_id
  role    = "roles/run.viewer"
  member  = module.identity.member
}

locals {
  secret_env = merge(
    {
      MCP_API_KEY = module.secrets.secret_resource_names["mcp-api-key"]
    },
    var.enable_github_token ? {
      GITHUB_TOKEN = module.secrets.secret_resource_names["github-token"]
    } : {}
  )
}

module "cloud_run" {
  source = "../../modules/cloud-run"

  project_id                      = var.project_id
  region                          = var.region
  service_name                    = var.service_name
  environment                     = var.environment
  artifact_registry_repository_id = var.artifact_registry_repo
  image_name                      = var.service_name
  image_tag                       = var.image_tag
  service_account_email           = module.identity.email
  allow_unauthenticated           = true
  zero_cost                       = var.zero_cost
  port                            = 8080
  health_check_path               = "/health"

  env = {
    MCP_TRANSPORT        = "streamable-http"
    GOLDENPATH_ROOT      = "/app"
    GOLDENPATH_CHANNEL   = "stable"
    GOLDENPATH_VERSION   = var.goldenpath_version
    GCP_PROJECT          = var.project_id
    GCP_REGION           = var.region
    GOLDENPATH_GCP_USE_ADC = "true"
  }

  secret_env = local.secret_env
}

module "observability" {
  source = "../../modules/observability"

  project_id             = var.project_id
  service_name           = var.service_name
  environment            = var.environment
  cloud_run_service_name = module.cloud_run.name
}
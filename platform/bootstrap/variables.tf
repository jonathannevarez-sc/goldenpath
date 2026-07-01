variable "region" {
  description = "Default GCP region for Golden Path resources"
  type        = string
}

variable "personal_test" {
  description = "Use a single isolated GCP project for personal testing (dev only, no duplicate prod resources)"
  type        = bool
  default     = false
}

variable "test_project_id" {
  description = "Dedicated test project ID (required when personal_test = true)"
  type        = string
  default     = ""
}

variable "dev_project_id" {
  description = "GCP project ID for dev environment (ignored when personal_test = true)"
  type        = string
  default     = ""
}

variable "prod_project_id" {
  description = "GCP project ID for prod environment (ignored when personal_test = true)"
  type        = string
  default     = ""
}

variable "github_org" {
  description = "GitHub organization that owns service repos"
  type        = string
}

variable "github_repo" {
  description = "GitHub repo allowed to impersonate CI SA (platform repo name; WIF trusts github_org/* via attribute_condition)"
  type        = string
}

variable "github_trusted_service_repos" {
  description = "Service repos needing explicit WIF bindings (org wildcard alone is insufficient for serviceAccountTokenCreator)"
  type        = list(string)
  default     = []
}

variable "artifact_registry_id" {
  description = "Shared Artifact Registry repository ID (ARTIFACT_REGISTRY_REPO in config/enterprise.env)"
  type        = string
}

variable "tfstate_bucket_name" {
  description = "GCS bucket name for Terraform state (created if bootstrap runs with appropriate permissions)"
  type        = string
  default     = ""
}
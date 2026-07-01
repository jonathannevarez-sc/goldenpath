variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "service_name" {
  type = string
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "artifact_registry_repo" {
  type = string
}

variable "image_tag" {
  description = "MCP Docker image tag (git SHA recommended)"
  type        = string
}

variable "zero_cost" {
  type    = bool
  default = true
}

variable "enable_github_token" {
  description = "Mount GITHUB_TOKEN secret for trigger_deploy tool"
  type        = bool
  default     = false
}

variable "github_token" {
  description = "GitHub token (required when enable_github_token = true)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "goldenpath_version" {
  description = "Golden Path release tag exposed to the MCP container"
  type        = string
}
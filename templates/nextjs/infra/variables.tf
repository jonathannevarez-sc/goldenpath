variable "goldenpath_org" {
  type = string
}


variable "goldenpath_repo" {
  description = "GitHub repo name hosting Golden Path modules and workflows"
  type        = string
  default     = "{{PLATFORM_REPO}}"
}
variable "goldenpath_version" {
  type    = string
  default = "{{GOLDENPATH_VERSION}}"
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "{{GCP_REGION}}"
}

variable "service_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "image_tag" {
  type    = string
  default = "bootstrap"
}

variable "artifact_registry_repo" {
  type = string
  
}

variable "zero_cost" {
  type    = bool
  default = true
}

variable "container_port" {
  type    = number
  default = 3000
}

variable "health_check_path" {
  type    = string
  default = "/api/health"
}
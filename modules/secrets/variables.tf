variable "project_id" {
  type = string
}

variable "service_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "secret_ids" {
  description = "Secret Manager secret IDs to create for this service"
  type        = list(string)
  default     = ["app-config"]
}

variable "accessor_members" {
  description = "IAM members granted secretAccessor on all service secrets"
  type        = list(string)
  default     = []
}
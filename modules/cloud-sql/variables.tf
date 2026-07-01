variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Region for the Cloud SQL instance"
  type        = string
}

variable "service_name" {
  description = "Logical service name (used in resource naming)"
  type        = string
}

variable "environment" {
  description = "Environment label (dev, prod)"
  type        = string
}

variable "runtime_service_account_email" {
  description = "Email of the service's runtime SA (becomes the IAM DB user)"
  type        = string
}

variable "runtime_service_account_member" {
  description = "IAM member string for the runtime SA (serviceAccount:...)"
  type        = string
}

variable "database_version" {
  description = "Cloud SQL database version (e.g. POSTGRES_16)"
  type        = string
  default     = "POSTGRES_16"

  validation {
    condition     = startswith(var.database_version, "POSTGRES_")
    error_message = "Only PostgreSQL is supported in this release (POSTGRES_*)."
  }
}

variable "tier" {
  description = "Machine tier (e.g. db-f1-micro, db-custom-2-7680)"
  type        = string
  default     = "db-f1-micro"
}

variable "edition" {
  description = "Instance edition: ENTERPRISE or ENTERPRISE_PLUS"
  type        = string
  default     = "ENTERPRISE"
}

variable "high_availability" {
  description = "REGIONAL (HA) when true, ZONAL when false"
  type        = bool
  default     = false
}

variable "ip_mode" {
  description = "public or private"
  type        = string
  default     = "public"

  validation {
    condition     = contains(["public", "private"], var.ip_mode)
    error_message = "ip_mode must be public or private."
  }
}

variable "network" {
  description = "VPC network self-link (required when ip_mode = private)"
  type        = string
  default     = null
}

variable "database_name" {
  description = "Application database name"
  type        = string
  default     = "appdb"
}

variable "deletion_protection" {
  description = "Block terraform destroy of the instance"
  type        = bool
  default     = true
}

variable "enable_apis" {
  description = "Enable required APIs (sqladmin, and servicenetworking/compute for private IP)"
  type        = bool
  default     = true
}

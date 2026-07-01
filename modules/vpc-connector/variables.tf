variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Region for the connector (must match the Cloud Run service region)"
  type        = string
}

variable "service_name" {
  description = "Logical service name (used to derive the connector name)"
  type        = string
}

variable "environment" {
  description = "Environment label (dev, prod)"
  type        = string
}

variable "connector_name" {
  description = "Override the derived connector name (<= 25 chars)"
  type        = string
  default     = null
}

variable "network" {
  description = "VPC network name or self-link the connector attaches to"
  type        = string
}

variable "ip_cidr_range" {
  description = "Unused /28 CIDR range for the connector"
  type        = string
  default     = "10.8.0.0/28"
}

variable "min_instances" {
  description = "Minimum connector instances"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum connector instances"
  type        = number
  default     = 3
}

variable "enable_apis" {
  description = "Enable the vpcaccess API as part of this module"
  type        = bool
  default     = true
}

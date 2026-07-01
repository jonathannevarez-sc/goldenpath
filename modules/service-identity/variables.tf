variable "project_id" {
  description = "GCP project ID"
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
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

variable "iam_propagation_wait" {
  description = "How long to wait after SA creation before IAM bindings proceed. Increase in high-latency environments."
  type        = string
  default     = "15s"
}
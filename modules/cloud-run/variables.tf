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
  type = string
}

variable "artifact_registry_repository_id" {
  description = "Artifact Registry repository ID (Golden Path requires AR — not GCR or Docker Hub)"
  type        = string
}

variable "image_name" {
  description = "Image name within the Artifact Registry repository (defaults to service_name)"
  type        = string
  default     = null
}

variable "image_tag" {
  description = "Image tag (CI sets this to the git SHA on each deploy)"
  type        = string
}

variable "service_account_email" {
  description = "Runtime service account email"
  type        = string
}

variable "zero_cost" {
  description = <<-EOT
    Minimize idle spend: scale to zero, request-based CPU (cpu_idle), no startup CPU boost,
    and modest CPU/instance caps. Set false for always-warm or higher burst capacity.
  EOT
  type        = bool
  default     = true
}

variable "min_instances" {
  description = "Minimum instances. Forced to 0 when zero_cost is true."
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum instances. Capped at max_instances_zero_cost when zero_cost is true."
  type        = number
  default     = 10
}

variable "max_instances_zero_cost" {
  description = "Max instance cap applied when zero_cost is true"
  type        = number
  default     = 3
}

variable "cpu" {
  description = "CPU limit. Defaults to 0.5 vCPU when zero_cost is true."
  type        = string
  default     = null
}

variable "memory" {
  description = "Memory limit. Defaults to 512Mi when zero_cost is true."
  type        = string
  default     = null
}

variable "cpu_idle" {
  description = "Allocate CPU only during request processing (reduces cost between requests)."
  type        = bool
  default     = null
}

variable "startup_cpu_boost" {
  description = "Temporarily boost CPU on startup. Disabled by default under zero_cost."
  type        = bool
  default     = null
}

variable "port" {
  type    = number
  default = 3000
}

variable "health_check_path" {
  description = "HTTP path for startup/liveness probes and CI smoke check"
  type        = string
  default     = "/api/health"
}

variable "env" {
  description = "Plain environment variables"
  type        = map(string)
  default     = {}
}

variable "secret_env" {
  description = "Map of env var name to Secret Manager secret resource name (latest version)"
  type        = map(string)
  default     = {}
}

variable "allow_unauthenticated" {
  description = "Allow public invoke (typical for dev; prod often uses IAP)"
  type        = bool
  default     = true
}
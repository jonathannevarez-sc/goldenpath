terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.30.0"
    }
  }

  # ── Remote state ────────────────────────────────────────────────────────────
  # Configure after bootstrap creates the shared state bucket:
  #   terraform init -backend-config="bucket=YOUR_ORG-goldenpath-tfstate" \
  #                  -backend-config="prefix=services/{{SERVICE_NAME}}"
  # backend "gcs" {
  #   bucket = "YOUR_ORG-goldenpath-tfstate"
  #   prefix = "services/{{SERVICE_NAME}}"
  # }
}
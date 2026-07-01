terraform {
  required_version = ">= 1.5.0"

  # Uncomment and set your GCS bucket after bootstrap (cannot use variables here).
  # backend "gcs" {
  #   bucket = "your-org-goldenpath-tfstate"
  #   prefix = "mcp/infra"
  # }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}
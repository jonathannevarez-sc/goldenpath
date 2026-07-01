terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.30.0"
    }
  }

  # Uncomment and set after creating a state bucket (recommended before apply).
  # backend "gcs" {
  #   bucket = "shop-goldenpath-tfstate"
  #   prefix = "platform/bootstrap"
  # }
}
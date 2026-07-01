terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.30.0"
    }
  }

  # ── Remote state ────────────────────────────────────────────────────────────
  # After bootstrap creates the bucket, uncomment and run:
  #   terraform init -migrate-state \
  #     -backend-config="bucket=YOUR_ORG-goldenpath-tfstate"
  # backend "gcs" {
  #   bucket = "YOUR_ORG-goldenpath-tfstate"   # replace with your bucket name
  #   prefix = "mcp/infra"
  # }
}
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.30.0"
    }
  }

  # ── Remote state (strongly recommended for team use) ───────────────────────
  # Step 1: run once with local state to create the bucket, then:
  # Step 2: uncomment the block below and run:
  #   terraform init -migrate-state \
  #     -backend-config="bucket=YOUR_ORG-goldenpath-tfstate"
  #
  # The bucket name must match tfstate_bucket_name in your terraform.tfvars.
  # backend "gcs" {
  #   bucket = "YOUR_ORG-goldenpath-tfstate"   # replace with your bucket name
  #   prefix = "platform/bootstrap"
  # }
}
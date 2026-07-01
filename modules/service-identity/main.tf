locals {
  account_id = substr(replace("${var.service_name}-${var.environment}-run", "_", "-"), 0, 30)
  email      = "${local.account_id}@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = local.account_id
  display_name = "${var.service_name} ${var.environment} Cloud Run runtime"
}

# GCP IAM can lag briefly after SA creation; sibling modules bind IAM in parallel.
resource "time_sleep" "wait_for_sa" {
  depends_on = [google_service_account.runtime]

  create_duration = var.iam_propagation_wait
}
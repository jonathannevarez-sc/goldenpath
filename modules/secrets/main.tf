resource "google_secret_manager_secret" "secrets" {
  for_each  = toset(var.secret_ids)
  project   = var.project_id
  secret_id = "${var.service_name}-${var.environment}-${each.value}"

  replication {
    auto {}
  }

  labels = {
    service     = var.service_name
    environment = var.environment
    managed_by  = "goldenpath"
  }
}

# Placeholder version so Cloud Run can mount secrets before operators add real config.
resource "google_secret_manager_secret_version" "bootstrap" {
  for_each    = toset(var.secret_ids)
  secret      = google_secret_manager_secret.secrets[each.value].id
  secret_data = "{}"

  lifecycle {
    ignore_changes = [secret_data]
  }
}

resource "google_secret_manager_secret_iam_member" "accessor" {
  for_each = {
    for pair in setproduct(var.secret_ids, var.accessor_members) :
    "${pair[0]}-${pair[1]}" => {
      secret_id = pair[0]
      member    = pair[1]
    }
  }

  project   = var.project_id
  secret_id = google_secret_manager_secret.secrets[each.value.secret_id].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = each.value.member
}
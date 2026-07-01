locals {
  dev_project  = var.personal_test ? var.test_project_id : var.dev_project_id
  prod_project = var.personal_test ? "" : var.prod_project_id

  projects = var.personal_test ? {
    dev = local.dev_project
    } : {
    dev  = var.dev_project_id
    prod = var.prod_project_id
  }
}

provider "google" {
  region = var.region
}

resource "google_project_service" "required" {
  for_each = {
    for pair in setproduct(keys(local.projects), [
      "run.googleapis.com",
      "artifactregistry.googleapis.com",
      "secretmanager.googleapis.com",
      "iam.googleapis.com",
      "iamcredentials.googleapis.com",
      "cloudresourcemanager.googleapis.com",
      "monitoring.googleapis.com",
      "logging.googleapis.com",
      "cloudtrace.googleapis.com",
      "cloudbuild.googleapis.com",
      "storage.googleapis.com",
    ]) : "${pair[0]}-${pair[1]}" => {
      project = local.projects[pair[0]]
      service = pair[1]
    }
  }

  project            = each.value.project
  service            = each.value.service
  disable_on_destroy = false
}

module "artifact_registry_dev" {
  source = "../../modules/artifact-registry"

  project_id    = local.dev_project
  region        = var.region
  repository_id = var.artifact_registry_id

  depends_on = [google_project_service.required]
}

module "artifact_registry_prod" {
  count = var.personal_test ? 0 : 1

  source = "../../modules/artifact-registry"

  project_id    = var.prod_project_id
  region        = var.region
  repository_id = var.artifact_registry_id

  depends_on = [google_project_service.required]
}

resource "google_service_account" "github_actions" {
  for_each = local.projects

  project      = each.value
  account_id   = "github-actions"
  display_name = "GitHub Actions CI (Golden Path)"
}

resource "google_service_account_iam_member" "github_actions_wif_user" {
  for_each = local.projects

  service_account_id = google_service_account.github_actions[each.key].name
  role               = "roles/iam.workloadIdentityUser"
  # Trust all repos under github_org (matches attribute_condition in wif.tf)
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github[each.key].name}/attribute.repository/${var.github_org}/*"
}

resource "google_service_account_iam_member" "github_actions_wif_token_creator" {
  for_each = local.projects

  service_account_id = google_service_account.github_actions[each.key].name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github[each.key].name}/attribute.repository/${var.github_org}/*"
}

locals {
  trusted_repo_bindings = {
    for pair in setproduct(keys(local.projects), distinct(concat([var.github_repo], var.github_trusted_service_repos))) :
    "${pair[0]}-${pair[1]}" => {
      env  = pair[0]
      repo = pair[1]
    }
  }
}

resource "google_service_account_iam_member" "github_actions_wif_user_repo" {
  for_each = local.trusted_repo_bindings

  service_account_id = google_service_account.github_actions[each.value.env].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github[each.value.env].name}/attribute.repository/${var.github_org}/${each.value.repo}"
}

resource "google_service_account_iam_member" "github_actions_wif_token_creator_repo" {
  for_each = local.trusted_repo_bindings

  service_account_id = google_service_account.github_actions[each.value.env].name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github[each.value.env].name}/attribute.repository/${var.github_org}/${each.value.repo}"
}

resource "google_project_iam_member" "github_actions_roles" {
  for_each = {
    for pair in setproduct(keys(local.projects), [
      "roles/run.admin",
      "roles/artifactregistry.admin",
      "roles/iam.serviceAccountAdmin",
      "roles/iam.serviceAccountUser",
      "roles/secretmanager.admin",
      "roles/monitoring.editor",
      "roles/resourcemanager.projectIamAdmin",
      "roles/storage.objectAdmin",
    ]) : "${pair[0]}-${pair[1]}" => {
      project = local.projects[pair[0]]
      role    = pair[1]
      env     = pair[0]
    }
  }

  project = each.value.project
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.github_actions[each.value.env].email}"
}
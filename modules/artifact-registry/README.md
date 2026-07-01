# artifact-registry module

Creates a **Docker** Artifact Registry repository in a GCP project.

## Who uses it

| Consumer | When |
|----------|------|
| **`platform/bootstrap`** | Once per dev (and prod) project during bootstrap |
| **Service `infra/`** | Does **not** call this module — uses the repo created at bootstrap |

Service deploys reference the existing repository by ID via `cloud-run` input `artifact_registry_repository_id` (from `artifact_registry_repo` in tfvars).

## Repository ID

Set in [`config/enterprise.env`](../config/enterprise.env) as `ARTIFACT_REGISTRY_REPO` (example default in `enterprise.env.example`: `shop-services`). Bootstrap passes it as `artifact_registry_id` in `platform/bootstrap/terraform.tfvars`.

## Golden Path rule

**Cloud Run always pulls from Artifact Registry** — not Container Registry (`gcr.io`), not Docker Hub, not third-party registries.

CI pushes:

```text
{region}-docker.pkg.dev/{project_id}/{ARTIFACT_REGISTRY_REPO}/{service_name}:{git_sha}
```

The [`cloud-run`](../cloud-run/) module builds the same URL pattern and grants the runtime service account `roles/artifactregistry.reader` on that repository.

## Outputs

| Output | Purpose |
|--------|---------|
| `repository_id` | Repository ID string |
| `repository_url` | URL prefix `{region}-docker.pkg.dev/{project}/{repo}` (no image/tag) |
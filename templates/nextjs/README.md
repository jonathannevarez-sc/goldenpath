# {{SERVICE_NAME}}

Shop service scaffolded from the **Golden Path** Next.js template.

## Local development

```bash
npm ci
npm run dev
```

Open http://localhost:3000 — health check at `/api/health`.

## Deploy

Prerequisites: platform bootstrap + `shop publish` (or wizard menu **7**).

- **dev:** push to `main` → GitHub Actions deploys automatically
- **prod:** Actions → **Deploy** workflow → `workflow_dispatch` → environment `prod`

## Infrastructure

Terraform in `infra/` uses shared modules from the [{{PLATFORM_REPO}}](https://github.com/{{GITHUB_ORG}}/{{PLATFORM_REPO}}) repo.

CI builds and pushes to **Artifact Registry only**, then sets `TF_VAR_image_tag` to the git SHA. Cloud Run pulls from `{region}-docker.pkg.dev/{project}/{{ARTIFACT_REGISTRY_REPO}}/{service}:{sha}`.

## Secrets

Secret Manager secret `{{SERVICE_NAME}}-<env>-app-config` is provisioned automatically. Add a secret version in GCP Console or gcloud before the app depends on it (optional for hello-world).
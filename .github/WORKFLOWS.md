# Platform repo GitHub Actions

Workflows in **this** repo (`goldenpath`). Service repos have their own `.github/workflows/deploy.yml` that **calls** the reusable workflow here.

**Full map:** [docs/repository-guide.md](../docs/repository-guide.md#github--ci-workflows-for-this-platform-repo)

## Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| [`workflows/deploy.yml`](./workflows/deploy.yml) | `workflow_call` only — **no `push:` on platform repo** | Reusable deploy pipeline. Service repos call `uses: YOUR_ORG/goldenpath/.github/workflows/deploy.yml@YOUR_GOLDENPATH_VERSION` (pin from `config/enterprise.env`). |
| [`workflows/deploy-mcp.yml`](./workflows/deploy-mcp.yml) | Push to `main` (path-filtered) / `workflow_dispatch` | Build and deploy hosted MCP to Cloud Run (streamable-http + API key). |
| [`workflows/tests.yml`](./workflows/tests.yml) | PR / push to `main` | **Tier 1** platform tests — blocks merge. |
| [`workflows/integration-tests.yml`](./workflows/integration-tests.yml) | Release tags `v*` / `workflow_dispatch` | **Tier 2** sandbox `publish` → `verify` — blocks customer-facing release. |

### Hosted MCP prerequisites

Set repository **Actions variables** (see header in `deploy-mcp.yml`): `GCP_SANDBOX_PROJECT`, `GCP_REGION`, `MCP_SERVICE_NAME`, `ARTIFACT_REGISTRY_REPO`. Details: [mcp/README.md](../mcp/README.md).

## Critical rule

`deploy.yml` must remain a **reusable** workflow. If `push:` triggers were added at platform root, the platform repo itself would try to deploy a non-existent service. Hygiene check: [`scripts/check-repo-hygiene.sh`](../scripts/check-repo-hygiene.sh).

## Service repo pattern

After scaffold, each service workflow matches the canonical snippet in [`templates/_shared/workflow-deploy.yml`](../templates/_shared/workflow-deploy.yml) (tokens replaced by `shop new`):

```yaml
# .github/workflows/deploy.yml in the service repo (after scaffold)
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        default: dev
        type: choice
        options: [dev, prod]

jobs:
  deploy-dev:
    if: github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && inputs.environment == 'dev')
    uses: YOUR_ORG/goldenpath/.github/workflows/deploy.yml@YOUR_GOLDENPATH_VERSION
    with:
      service_name: my-service
      environment: dev
      gcp_project: your-org-goldenpath-dev
      gcp_region: us-central1
      artifact_registry_repo: shop-services   # ARTIFACT_REGISTRY_REPO from enterprise.env
      goldenpath_org: YOUR_ORG
      goldenpath_version: YOUR_GOLDENPATH_VERSION
      app_runtime: node                       # node | python | docker
      health_check_path: /api/health
    secrets:
      GCP_WIF_PROVIDER: ${{ secrets.GCP_WIF_PROVIDER }}
      GCP_WIF_SERVICE_ACCOUNT: ${{ secrets.GCP_WIF_SERVICE_ACCOUNT }}
      GOLDENPATH_MODULE_TOKEN: ${{ secrets.GOLDENPATH_MODULE_TOKEN }}

  deploy-prod:
    if: github.event_name == 'workflow_dispatch' && inputs.environment == 'prod'
    uses: YOUR_ORG/goldenpath/.github/workflows/deploy.yml@YOUR_GOLDENPATH_VERSION
    with:
      service_name: my-service
      environment: prod
      gcp_project: your-org-goldenpath-prod
      gcp_region: us-central1
      artifact_registry_repo: shop-services
      goldenpath_org: YOUR_ORG
      goldenpath_version: YOUR_GOLDENPATH_VERSION
      app_runtime: node
      health_check_path: /api/health
    secrets:
      GCP_WIF_PROVIDER: ${{ secrets.GCP_WIF_PROVIDER_PROD }}
      GCP_WIF_SERVICE_ACCOUNT: ${{ secrets.GCP_WIF_SERVICE_ACCOUNT_PROD }}
      GOLDENPATH_MODULE_TOKEN: ${{ secrets.GOLDENPATH_MODULE_TOKEN }}
```

Push to `main` deploys **dev** only. **Prod** requires a manual `workflow_dispatch` with `environment: prod`.

## Related

- [04-journey-cli.md](../docs/getting-started/04-journey-cli.md) — publish flow
- [deploy-to-shop-gcp skill](../skills/deploy-to-shop-gcp/SKILL.md) — troubleshoot CI
- [mcp/README.md](../mcp/README.md) — hosted MCP deploy and auth
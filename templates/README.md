# Golden Path service templates

Each template is a complete service repo after `shop new` + `shop publish` (bootstrap must exist first).

## Choose a template

```bash
./cli/shop list
```

| Template | Runtime | Port | Health | Use case |
|----------|---------|------|--------|----------|
| **nextjs** (default) | node | 3000 | `/api/health` | Full-stack web / SSR |
| **fastapi** | python | 8000 | `/api/health` | Python REST API |
| **streamlit** | python | 8501 | `/_stcore/health` | Dashboards, internal tools |
| **express** | node | 3000 | `/api/health` | Lightweight Node API |
| **react-spa** | docker | 8080 | `/health` | React frontend (static + nginx) |
| **svelte-spa** | docker | 8080 | `/health` | Svelte frontend (static + nginx) |

Port and health path come from `catalog.json`; `shop new` writes them into `infra/*.tfvars` via `{{CONTAINER_PORT}}` and `{{HEALTH_CHECK_PATH}}` tokens.

## Scaffold

Prerequisites: `config/enterprise.env`, platform bootstrap (`./scripts/standup-teardown-env.sh`).

```bash
shop new my-api --template fastapi --output .. \
  --github-org ORG --gcp-dev PROJECT --gcp-prod PROJECT
shop publish ../my-api
```

## What every template includes

- Application hello-world
- `Dockerfile` → **Artifact Registry** → **Cloud Run**
- `infra/` — shared Golden Path Terraform modules
- `.github/workflows/deploy.yml` — reusable workflow from `{{PLATFORM_REPO}}` (`@{{GOLDENPATH_VERSION}}`)
- `zero_cost` Cloud Run defaults (scale to zero)

## Shared building blocks

- `catalog.json` — template metadata for CLI and MCP `list_templates()`
- `_shared/` — infra + workflow snippets (maintainer reference)

## Adding a template

1. Copy `_shared/infra` and `_shared/workflow-deploy.yml`
2. Add app code + `Dockerfile` (match `container_port` / health route to `catalog.json`)
3. Use `{{CONTAINER_PORT}}` and `{{HEALTH_CHECK_PATH}}` in `infra/dev.tfvars` and `infra/prod.tfvars`
4. Register in `catalog.json`
5. Verify `shop new` + `shop publish` smoke test
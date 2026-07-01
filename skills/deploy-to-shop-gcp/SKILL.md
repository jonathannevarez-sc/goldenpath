---
name: deploy-to-shop-gcp
phase: 2
description: >
  Deploy and operate Golden Path services on GCP. Use for deploy status, prod promotion,
  pipeline failures, shop publish, and WIF troubleshooting after bootstrap.
distribution: mcp-resources
status: implemented
---

# Deploy to Golden Path GCP

## When to use

- User asks about deploy status, prod promotion, or failed pipeline
- User says "deploy to dev/prod" for a Golden Path service
- After `shop new` / `scaffold_service` — publish and verify deploy

## Prerequisites

1. **Platform bootstrap** applied (`platform/bootstrap` — WIF pool, `github-actions` SA, shared Artifact Registry)
2. **`config/enterprise.env`** — `ARTIFACT_REGISTRY_REPO` must match bootstrap `artifact_registry_id`
3. **Service repo published** — `shop publish` or wizard menu **7** (MCP has no publish tool)
4. **WIF secrets** on service repo: `GCP_WIF_PROVIDER`, `GCP_WIF_SERVICE_ACCOUNT` (from terraform outputs)
5. **WIF trust** for service repo: `scripts/lib/wif-trust-repo.sh <project> <org> <repo>` if not in `github_trusted_service_repos`

## Read first

- `goldenpath://docs/getting-started/03-quickstart.md`
- `goldenpath://docs/getting-started/04-journey-cli.md` — `shop publish` happy path
- `goldenpath://docs/getting-started/08-journey-mcp.md` — MCP limits (no bootstrap/publish tools)
- Tool: `get_version()` — confirm channel/version

---

## First deploy (happy path)

```bash
shop new my-api --template fastapi --output ..
shop publish ../my-api
```

Wizard equivalent: menus **6** → **7**. Dev deploy runs on push to `main`.

---

## Dev deploy (ongoing)

Dev deploys **automatically** on push to `main`. Do not manually click Cloud Console.

If user needs status:

```
get_deploy_status(service_name="my-api", environment="dev", project="...")
```

---

## Prod deploy

Prod is **gated** via GitHub Actions `workflow_dispatch` (input `environment: prod`).

MCP (requires `GITHUB_TOKEN` + confirmation):

```
trigger_deploy(github_repo="ORG/REPO", environment="prod", confirm=true)
```

Or: GitHub UI → Actions → **Deploy** → Run workflow → `prod`

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Never published | Run `shop publish <dir>` or wizard **7** — scaffold alone does not deploy |
| Bootstrap missing | `./scripts/standup-teardown-env.sh --yes` or wizard **3** |
| Workflow not triggered | Push to `main` (not `master`) |
| Reusable workflow not found | Enable Actions access on platform `goldenpath` repo |
| `startup_failure` / OIDC | Caller workflow needs `permissions: id-token: write` |
| Workflow auth error | Verify `GCP_WIF_PROVIDER` and `GCP_WIF_SERVICE_ACCOUNT` secrets |
| Docker push denied | WIF SA needs AR write + `workloadIdentityUser` / `serviceAccountTokenCreator` on repo principal; run `wif-trust-repo.sh` |
| Terraform module fetch failed | Reusable workflow configures git for private `goldenpath` modules; check `GOLDENPATH_MODULE_TOKEN` if private |
| Image pull failed | Image must be Artifact Registry (`*-docker.pkg.dev/*`); `artifact_registry_repo` must match bootstrap repo |
| Health check failed | Match template health path from `list_templates()` |
| Stale `deploy.yml` pin (v0.3.0–v0.3.6) | `shop upgrade <dir>` or wizard publish (**7**) — only **v0.3.7** tag exists |
| `gh account ≠ GITHUB_ORG` | `gh auth switch --user <GITHUB_ORG>` |
| 403 on Cloud Run | Check IAM / invoker settings (`allow_unauthenticated` on dev only) |

---

## Tools

- `get_deploy_status`
- `get_service_config`
- `list_services`
- `trigger_deploy` (writes, audited, requires `confirm=true`)
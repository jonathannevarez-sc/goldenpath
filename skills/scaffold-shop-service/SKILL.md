---
name: scaffold-shop-service
phase: 2
description: >
  Scaffold a new Golden Path service from templates (shop CLI or scaffold_service MCP).
  Use when the user wants shop new, scaffold_service, or a new Cloud Run service repo.
  Do NOT use for platform GCP bootstrap — use goldenpath-setup-wizard first.
distribution: mcp-resources
status: implemented
---

# Scaffold Golden Path service

Create a **new service repo** from `templates/` — not platform bootstrap.

## When to use

- User asks to create a new Golden Path / shop service on GCP
- User says `shop new`, `scaffold_service`, or scaffold a service repo
- After GCP bootstrap is already done (WIF + Artifact Registry exist)

## When NOT to use

- User needs **platform bootstrap** (WIF, shared AR) → `goldenpath-setup-wizard` or `./scripts/standup-teardown-env.sh`
- User only needs deploy troubleshooting → `deploy-to-shop-gcp`

## Prerequisites

1. `config/enterprise.env` configured (`GITHUB_ORG`, `GCP_*`, `ARTIFACT_REGISTRY_REPO`, `GOLDENPATH_VERSION`)
2. Bootstrap applied once (`./scripts/standup-teardown-env.sh --yes` or wizard menu **3**)
3. Scaffold output **outside** the platform repo (`output_dir=".."` or `shop new --output ..`)

---

## Step 1 — Pick template

```
list_templates()
```

| Template | When |
|----------|------|
| `nextjs` | Default web app / SSR |
| `fastapi` | Python API |
| `streamlit` | Dashboard / internal tool |
| `express` | Node API |
| `react-spa` / `svelte-spa` | Frontend SPA |

---

## Step 2 — Scaffold

**MCP** (audited write — runs `shop new`):

```
scaffold_service(
  name="orders-api",
  template="fastapi",
  github_org="YOUR_ORG",
  gcp_dev_project="your-org-goldenpath-dev",
  gcp_prod_project="your-org-goldenpath-prod",
  region="us-central1",
  output_dir=".."
)
```

`output_dir=".."` places the repo next to `goldenpath/`. Default `"."` scaffolds inside the platform repo — avoid.

**CLI** (equivalent):

```bash
shop new orders-api --template fastapi --output ..
```

Workflow tag comes from `GOLDENPATH_VERSION` in `config/enterprise.env` (example: `v0.3.7`). Tfvars include `artifact_registry_repo` from `ARTIFACT_REGISTRY_REPO`.

---

## Step 3 — Publish (not automatic)

`scaffold_service` / `shop new` only create local files. Deploy requires publish:

**CLI:**

```bash
shop publish ../orders-api
```

**Wizard:** menu **7** (repo + WIF secrets + `wif-trust-repo.sh` + push `main` + watch deploy)

**Manual minimum:** `gh repo create`, set `GCP_WIF_PROVIDER` + `GCP_WIF_SERVICE_ACCOUNT` from bootstrap outputs, run `scripts/lib/wif-trust-repo.sh <project> <org> <repo>`, push to `main`.

Then load **`deploy-to-shop-gcp`** for deploy status and failures.

---

## Step 4 — Verify

```
validate_service_repo(path="../orders-api")
get_deploy_status(service_name="orders-api", environment="dev", project="your-org-goldenpath-dev")
```

Cloud Run service name is `{service_name}-{environment}` (e.g. `orders-api-dev`).

---

## Definition of done

Service repo lives outside `goldenpath/`, passes `validate_service_repo`, and dev deploy succeeds after `shop publish` (or wizard **7**) with no manual edits to scaffolded files.

## Resources

- `goldenpath://docs/getting-started/03-quickstart.md`
- `goldenpath://docs/getting-started/04-journey-cli.md`
- `goldenpath://docs/getting-started/08-journey-mcp.md`
- `goldenpath://skills/deploy-to-shop-gcp/SKILL.md`
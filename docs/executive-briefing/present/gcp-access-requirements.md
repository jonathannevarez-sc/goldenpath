# GCP access requirements for Golden Path

**Platform version:** v0.3.8 · **Date:** 2026-06-24  
**Audience:** Engineering leads, platform/DevOps, FinOps, and anyone onboarding to Golden Path

---

## Summary

Golden Path splits GCP access into **three levels**. Most people only need **Level 1**. One-time platform setup needs **Level 2**. Billing and org-wide project creation need **Level 3**.

| Level | Who | GCP access needed | When |
|-------|-----|-------------------|------|
| **1 — Developer** | Product engineers using `shop`, wizard, or MCP | Project-scoped read + limited IAM on the CI service account | Day-to-day scaffold, publish, verify |
| **2 — Platform** | Platform / DevOps running bootstrap | Project Owner (or equivalent custom role) on dev + prod projects | One-time per environment |
| **3 — Org / FinOps** | GCP org admin, FinOps | Billing + project creation at org/folder level | Sandbox standup, new project provisioning |

**He does not need billing access** if platform has already bootstrapped dev/prod and shared `config/enterprise.env` (see [team-env-setup.md](../../../config/team-env-setup.md)).

---

## Level 1 — Developer (typical product engineer)

This is the access profile for someone who clones the repo, scaffolds a service, publishes to GitHub, and deploys to the shared dev project.

### Authentication (required)

```bash
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_GCP_DEV_PROJECT
```

No service-account keys. No tokens in `enterprise.env`.

### Minimum GCP roles on the **dev project**

| Role | Why |
|------|-----|
| `roles/run.viewer` | `shop verify`, MCP `get_deploy_status`, `list_services` |
| `roles/iam.serviceAccountAdmin` **on the `github-actions@` SA only** | `shop publish` runs `wif-trust-repo.sh` to bind WIF for the new service repo |

**Practical shortcut:** `roles/editor` on the dev project covers read + WIF trust, but is broader than necessary. Platform teams often grant a **custom role** with only:

- `run.services.get`, `run.services.list`
- `iam.serviceAccounts.getIamPolicy`, `iam.serviceAccounts.setIamPolicy` (scoped to `github-actions@*`)
- `iam.workloadIdentityPools.get`, `iam.workloadIdentityPools.list`

### What developers do **not** need

| Not required | Reason |
|--------------|--------|
| Billing account access | Platform links billing during bootstrap |
| `roles/owner` or `roles/resourcemanager.projectIamAdmin` | Bootstrap already created WIF, Artifact Registry, and CI service accounts |
| Org/folder admin | Developers deploy into existing projects only |
| Ability to create GCP projects | Platform provisions `GCP_DEV_PROJECT` / `GCP_PROD_PROJECT` |
| Secret values in repos | Secrets live in Secret Manager; CI uses WIF |

### GitHub access (not GCP, but required for publish)

| Permission | Why |
|------------|-----|
| `gh auth login` with repo create rights in the org | `shop publish` creates the service repo and sets WIF secrets |
| OIDC enabled for GitHub Actions in the org | Required for keyless WIF auth (no JSON keys) |

### Success checklist — developer path

- [ ] Received `enterprise.env` from platform (not looked up billing IDs personally)
- [ ] `gcloud` and `gh` authenticated
- [ ] Can run `shop new` → `shop publish` → `shop verify` against dev
- [ ] GitHub Actions deploy completes green on push to `main`

---

## Level 2 — Platform engineer (bootstrap + handoff)

Someone running **one-time** Golden Path setup: `platform/bootstrap` Terraform, sandbox standup, or wizard menu **3) Bootstrap GCP**.

### Scope

Apply to **each** Golden Path project:

- `GCP_DEV_PROJECT`
- `GCP_PROD_PROJECT` (enterprise footprint)
- `GCP_SANDBOX_PROJECT` (optional isolated test)

Golden Path **never deploys into** `PARENT_PROJECT_ID` — that project is only a billing anchor.

### Recommended role

**`roles/owner`** on each target project is the simplest path and matches what Terraform bootstrap creates.

If your security team prefers least privilege, the human running `terraform apply` needs equivalent permissions to create and manage:

| Resource | APIs / permissions |
|----------|-------------------|
| Enable APIs | `serviceusage.services.enable` on the project |
| Artifact Registry | Create Docker repository |
| Workload Identity Federation | Create pool + OIDC provider |
| Service accounts | Create `github-actions@` and set IAM bindings |
| Project IAM | Grant CI service account its deploy roles |

Bootstrap grants the **CI service account** (not the human) these project roles:

| Role on `github-actions@` SA | Purpose |
|-------------------------------|---------|
| `roles/run.admin` | Deploy Cloud Run services |
| `roles/artifactregistry.admin` | Push/pull container images |
| `roles/iam.serviceAccountAdmin` | Create per-service runtime SAs |
| `roles/iam.serviceAccountUser` | Act as runtime SAs during deploy |
| `roles/secretmanager.admin` | Provision service secrets |
| `roles/monitoring.editor` | Observability defaults |
| `roles/resourcemanager.projectIamAdmin` | Wire runtime SA IAM |
| `roles/storage.objectAdmin` | Build/cache artifacts |

### APIs enabled by bootstrap

```
run, artifactregistry, secretmanager, iam, iamcredentials,
cloudresourcemanager, monitoring, logging, cloudtrace, cloudbuild, storage
```

### Platform also needs (GitHub, not GCP)

| Access | Why |
|--------|-----|
| GitHub org admin (or equivalent) | Org variables, reusable workflow access, OIDC |
| Push access to `goldenpath` repo | Release tags (`GOLDENPATH_VERSION`) |

### Success checklist — platform path

- [ ] `terraform apply` in `platform/bootstrap/` succeeds on dev (+ prod if not sandbox)
- [ ] WIF outputs recorded (`dev_github_wif_provider_name`, `dev_github_actions_sa_email`, …)
- [ ] `enterprise.env.team` created and shared (see [team-env-setup.md](../../../config/team-env-setup.md))
- [ ] Smoke test: `shop publish` deploys a reference service to dev with zero manual edits

---

## Level 3 — Org admin / FinOps (project + billing)

Required only when **creating new GCP projects** or **linking billing** — e.g. first sandbox via `standup-teardown-env.sh` or wizard bootstrap before projects exist.

### Org / folder level

| Permission | Why |
|------------|-----|
| `roles/resourcemanager.projectCreator` (or folder equivalent) | `gcloud projects create` in standup script |
| `roles/billing.user` on the billing account | `gcloud billing projects link` |

### Values FinOps provides (go in `enterprise.env`, never in git)

| Variable | Owner |
|----------|-------|
| `PARENT_PROJECT_ID` | FinOps — billing anchor only |
| `BILLING_ACCOUNT_ID` | FinOps |
| `GCP_DEV_PROJECT` / `GCP_PROD_PROJECT` | Platform (IDs may be pre-provisioned by org admin) |

### Safety guardrails (configured by platform)

| Setting | Purpose |
|---------|---------|
| `PROTECTED_PROJECTS` | Teardown scripts refuse to delete prod or billing anchor |
| `personal_test = true` | Required for sandbox teardown path only |

---

## Access by journey step

| Step | Tool | Minimum access |
|------|------|----------------|
| Configure org | Edit `enterprise.env` | None on GCP (receives file from platform) |
| Personal sandbox | `standup-teardown-env.sh` or wizard **3** | **Level 3** (create project + link billing) + **Level 2** (terraform apply) |
| Enterprise bootstrap | `platform/bootstrap` terraform | **Level 2** on existing dev/prod projects |
| Scaffold service | `shop new` | None (local files only) |
| Publish + deploy | `shop publish` | **Level 1** on dev project + GitHub repo rights |
| Check deploy | `shop verify` or MCP | **Level 1** (`run.viewer`) |
| Teardown sandbox | `teardown-personal-test.sh` | **Level 2** on sandbox project; `--delete-project` also needs project delete |

---

## Request template for your GCP admin

Copy and customize:

```
Subject: GCP access for Golden Path — [Name], [Role]

Projects:
  - Dev:  your-org-goldenpath-dev
  - Prod: your-org-goldenpath-prod  (platform bootstrap only; developer uses dev first)

For [Name] as product engineer (Level 1):
  - roles/run.viewer on dev project
  - roles/iam.serviceAccountAdmin on service account:
      github-actions@your-org-goldenpath-dev.iam.gserviceaccount.com
    (or roles/editor on dev if custom SA-scoped IAM is not supported)

For platform team (Level 2) — one-time bootstrap:
  - roles/owner on dev + prod Golden Path projects
  - OR equivalent custom role for Terraform bootstrap (see golden-path repo:
      docs/executive-briefing/present/gcp-access-requirements.md)

For FinOps (Level 3) — only if creating sandbox projects:
  - roles/billing.user on billing account [ID]
  - roles/resourcemanager.projectCreator at folder [path]

Authentication: user credentials via gcloud login + application-default login.
No long-lived service account keys.
```

---

## Common permission errors

| Symptom | Likely missing access | Fix |
|---------|----------------------|-----|
| `billing link failed` | `roles/billing.user` | FinOps links billing, or grant billing user to platform runner |
| `IAM_PERMISSION_DENIED` on `terraform apply` | Project Owner or bootstrap custom role | Platform DRI runs bootstrap with elevated access |
| `workloadIdentityPools.create` denied | Same as above | Run bootstrap as platform, not developer |
| `add-iam-policy-binding` failed on publish | `serviceAccountAdmin` on `github-actions@` SA | Grant Level 1 IAM on dev to publisher |
| MCP / verify cannot read Cloud Run | `roles/run.viewer` | Add viewer on dev project |
| AR docker push 403 in Actions | Per-repo WIF trust | Re-run `shop publish` or `wif-trust-repo.sh` (needs Level 1 IAM) |

---

## Security principles (built into the path)

- **Keyless CI** — GitHub Actions authenticates via Workload Identity Federation; no JSON keys in GitHub secrets.
- **Least privilege by layer** — Humans get read + narrow IAM; CI service account gets deploy roles; runtime SAs get only what each service needs.
- **MCP does not escalate** — MCP tools use the caller's own `gcloud` / ADC credentials; they cannot exceed the user's GCP permissions.
- **Billing isolation** — `PARENT_PROJECT_ID` is never a deploy target; protected-project lists block accidental teardown.

---

## Related docs

- [team-env-setup.md](../../../config/team-env-setup.md) — who fills billing vs project IDs
- [getting-started-platform.md](../../platform/getting-started-platform.md) — platform bootstrap walkthrough
- [sandbox-env.md](../../environments/sandbox-env.md) — isolated test project
- [platform/bootstrap/README.md](../../../platform/bootstrap/README.md) — what Terraform creates

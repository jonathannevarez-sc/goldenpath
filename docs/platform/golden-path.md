# Golden Path — comprehensive guide

**Status:** Living document  
**Last updated:** 2026-06-15  
**Platform repo:** `goldenpath` — [github.com/YOUR_GITHUB_ORG/goldenpath](https://github.com/YOUR_GITHUB_ORG/goldenpath)  
**Owners:** Platform / DevEx team  
**Audience:** Product engineers, tech leads, SRE/Platform, Security

---

## Table of contents

1. [What is Golden Path?](#1-what-is-golden-path)
2. [The problem it solves](#2-the-problem-it-solves)
3. [Goals and non-goals](#3-goals-and-non-goals)
4. [Who it is for](#4-who-it-is-for)
5. [What you can do as a developer](#5-what-you-can-do-as-a-developer)
6. [Benefits summary](#6-benefits-summary)
7. [Solution architecture](#7-solution-architecture)
8. [Reference architecture (GCP)](#8-reference-architecture-gcp)
9. [Framework and templates](#9-framework-and-templates)
10. [Golden Path MCP server](#10-golden-path-mcp-server)
11. [Developer workflows](#11-developer-workflows)
12. [What you do not have to do](#12-what-you-do-not-have-to-do)
13. [Off-road and edge cases](#13-off-road-and-edge-cases)
14. [Without MCP (fallbacks)](#14-without-mcp-fallbacks)
15. [For platform teams](#15-for-platform-teams)
16. [Phasing and rollout](#16-phasing-and-rollout)
17. [Success metrics](#17-success-metrics)
18. [Risks and mitigations](#18-risks-and-mitigations)
19. [Open decisions](#19-open-decisions)
20. [Quick reference](#20-quick-reference)
21. [FAQ](#21-faq)
22. [Glossary](#22-glossary)

---

## 1. What is Golden Path?

A **Golden Path** (also called a **paved road**) is an opinionated, supported, well-documented route for the **common case** of shipping software. It is the path of least resistance that is also the **secure, observable, and compliant** one.

For Shop, Golden Path means:

- A **standard way** to structure a service repo
- **Shared infrastructure** (Terraform modules, CI/CD, GCP patterns)
- **Starter templates** (default: containerized web/API on Cloud Run)
- **One front door** for developers: a hosted **MCP server** that serves official skills, docs, and platform tools
- **AI-assisted workflows** so Claude and similar tools scaffold, deploy, and troubleshoot the Shop way

Teams that need something different can go **off-road**. The Golden Path is **opt-in** for existing services; new services are encouraged to use it because it is faster and safer.

### One-sentence summary

**Run one command (or one MCP conversation), get a repo, push code, and your service is live on GCP in `dev` with security and monitoring already done — and the same flow takes you to `prod`.**

---

## 2. The problem it solves

Today, developers shipping into Shop’s GCP environment re-solve the same problems on every new service:

| Problem area | What developers redo today |
|--------------|----------------------------|
| Repo structure | Layout, Dockerfile, config conventions |
| CI/CD | Lint, test, build, push image, deploy |
| Infrastructure | Cloud Run, IAM, Artifact Registry, secrets |
| Security | Service accounts, keyless auth, Secret Manager |
| Observability | Logging, metrics, traces, dashboards, alerts |

This is **slow**, **inconsistent**, and pushes security and reliability decisions onto individual developers who should not have to own them.

### Distribution problem (why MCP-centric delivery matters)

Even with good templates, if skills and docs live on each developer’s laptop:

| Scenario | Failure mode |
|----------|--------------|
| Fresh laptop | Hunt for skills, docs, MCP config, CLI |
| Local skill edits | Runbooks drift per developer |
| Version skew | Different engineers on different “golden path” versions |
| Multiple channels | Wiki disagrees with skills; tools updated before docs |

Golden Path solves **both** the technical paved road **and** consistent delivery of knowledge and actions.

---

## 3. Goals and non-goals

### Goals

| Goal | Target |
|------|--------|
| **Time to first production deploy** | Days/weeks → **under one day** (stretch: under one hour) |
| **Secure, observable, cost-aware defaults** | Built into template, not bolted on later |
| **Legibility** | Any engineer, SRE, or security reviewer recognizes the setup |
| **AI-assisted DX** | Claude + MCP produce on-pattern code and routine platform ops |

### Non-goals

| Non-goal | Meaning |
|----------|---------|
| **Forced migration** | Existing services are not required to move on day one |
| **Every architecture** | Common case only (containerized web service / API) |
| **Replace human judgment** | Tooling assists; humans own production |
| **MCP-only deploys** | CI/CD still deploys on git push if MCP is unavailable |

---

## 4. Who it is for

| Persona | Need | How Golden Path helps |
|---------|------|------------------------|
| **Product engineer** | Ship a feature behind a service without learning all of GCP | Scaffold → code → auto-deploy |
| **Tech lead** | Consistency across team services | Same repo shape, pipeline, and conventions |
| **SRE / Platform** | Supportable services with standard telemetry and IaC | Modules and baselines enforced by template |
| **Security** | Guardrails by default | Least-privilege IAM, keyless CI, Secret Manager only |

---

## 5. What you can do as a developer

This section describes Golden Path **as if you have it today**.

### 5.1 Day one — new service

| Action | How |
|--------|-----|
| **Connect Golden Path** | Add MCP server URL + SSO to Claude Code, or your MCP client |
| **Scaffold a service** | Ask: *“Create a new Shop service called orders-api”* — or run `shop new orders-api --output ..` |
| **Get a complete repo** | Next.js (or chosen template), Dockerfile, Terraform, CI/CD, tests, observability wiring |
| **Deploy to dev** | Push or merge to `main` → pipeline runs automatically |
| **Verify** | Open the `dev` URL; health check passes |

**No manual steps:** no Cloud Console clicking, no wiring GitHub Actions, no creating service accounts by hand.

### 5.2 Every day — building features

| Action | How |
|--------|-----|
| **Develop** | Edit app code in `src/` (or equivalent) like any normal project |
| **Deploy to dev** | Merge to `main` → automatic deploy |
| **Check deploy** | MCP: *“What’s the deploy status for orders-api?”* — or CI UI / GCP console |
| **View logs & metrics** | Standard Cloud Logging / Monitoring dashboards (same layout for every Shop service) |
| **Add secrets** | Secret Manager via documented flow — never commit secrets to git |
| **Promote to prod** | Approve gated CI step or tag a release (one standardized flow) |

### 5.3 With AI (MCP + official skills)

| Action | Example prompt / tool |
|--------|------------------------|
| **Scaffold** | *“Scaffold a Shop service named inventory-api using the nextjs template”* |
| **Deploy status** | `get_deploy_status(service="inventory-api")` |
| **List services** | `list_services()` |
| **Config lookup** | `get_service_config(service="inventory-api")` |
| **Cost visibility** | `get_cost_estimate(service="inventory-api")` |
| **Debug failed deploy** | *“Why did the last deploy of inventory-api fail?”* (skill + status tool) |
| **Extend infra safely** | *“Add a Pub/Sub subscription the Shop way”* (terraform conventions skill) |

Official skills and docs are **read from MCP** at a pinned platform version — not copied onto your laptop.

### 5.4 When something goes wrong

| Action | How |
|--------|-----|
| **Check pipeline** | GitHub Actions run for your repo |
| **Check runtime** | MCP `get_deploy_status` or GCP Cloud Run console |
| **Follow runbook** | `goldenpath://docs/runbooks/deploy-failure.md` via MCP |
| **Get help** | `#golden-path` support channel — platform recognizes your setup |

### 5.5 What your service repo looks like

After scaffolding:

```
my-service/
├── src/                    # Application code (e.g. Next.js)
├── Dockerfile              # Container build
├── infra/
│   ├── main.tf             # Calls shared Golden Path Terraform modules
│   ├── dev.tfvars
│   └── prod.tfvars
├── .github/workflows/
│   └── deploy.yml          # Calls shared Golden Path reusable workflow
└── README.md               # Service-specific notes
```

You mostly edit **`src/`** and occasionally **`infra/`** for service-specific resources. Platform maintains shared modules and workflows.

---

## 6. Benefits summary

### Speed and focus

| Benefit | What it means for you |
|---------|------------------------|
| **Hours, not weeks** | First `dev` deploy in under a day; repeat deploys much faster |
| **Just code** | Platform owns pipeline, baseline infra, and observability |
| **Fast feedback** | Push → see changes in `dev` quickly |

### Safety and compliance

| Benefit | What it means for you |
|---------|------------------------|
| **Secure by default** | Secret Manager, keyless CI, least-privilege IAM |
| **Passes review** | New services align with security expectations out of the box |
| **Observable by default** | Logs, metrics, traces, dashboards without extra setup |

### Consistency and mobility

| Benefit | What it means for you |
|---------|------------------------|
| **Same flow on every team** | Rotate teams without relearning deploy |
| **Same guidance everywhere** | Official skills/docs from MCP — no local drift |
| **Recognizable to SRE** | Support and incident response follow known patterns |

### AI and onboarding

| Benefit | What it means for you |
|---------|------------------------|
| **Fresh laptop ready** | Connect MCP once; no skill hunting |
| **No tribal knowledge** | Ask Claude using Shop official skills |
| **Always current** | Platform updates `stable` channel; you pick up new guidance automatically |

### Before vs after

| Today (without Golden Path) | With Golden Path |
|----------------------------|------------------|
| Figure out repo structure yourself | Template gives you the structure |
| Wire CI/CD yourself | Pipeline already works |
| Provision Cloud Run, IAM, secrets yourself | Terraform modules do it |
| Ask how things should look | Defaults are already correct |
| Days/weeks to first deploy | Hours to first deploy |

---

## 7. Solution architecture

Golden Path has **three layers**. Layers B and C are delivered through **one MCP server** (evolved model).

### Layer A — Paved-road artifacts (the road itself)

Concrete, runnable building blocks:

| # | Artifact | Purpose |
|---|----------|---------|
| A1 | **Reference architecture** | Standard Shop service on GCP |
| A2 | **Terraform modules** | Reusable infra (Cloud Run, IAM, secrets, observability) |
| A3 | **CI/CD pipeline template** | Shared GitHub Actions workflow |
| A4 | **Service templates** | Next.js first; more frameworks over time |

**This layer is what actually runs in production.** MCP does not replace it.

### Layer B — Golden Path MCP server (AI-assisted DX)

A **single hosted MCP server** provides:

| Surface | Content | Who maintains |
|---------|---------|---------------|
| **MCP Resources** | Skills (`SKILL.md`), docs, conventions | Platform admins via GitHub PR |
| **MCP Tools** | Scaffold, deploy, status, config, cost | Platform team |

- **Resources** = knowledge (read-only virtual filesystem from pinned git release)
- **Tools** = live actions and data
- Skills instruct the AI *when and how* to call tools

### Layer C — Discoverability and support

| Item | Delivery |
|------|----------|
| Start here | `goldenpath://docs/getting-started/01-start-here.md` |
| 15-minute quickstart | `goldenpath://docs/getting-started/03-quickstart.md` |
| Support channel | `#golden-path` (or equivalent) |
| Service catalog | MCP `list_services` (+ optional portal later) |
| Adoption metrics | Platform dashboards |

Docs are primarily via **MCP Resources**; optional static mirror for browsers and fallback.

### End-to-end architecture diagram

```
┌──────────────────────────────────────────────────────────────────┐
│  GitHub (admin-only writes) — single source of truth             │
│    modules/   templates/   workflows/   skills/   docs/          │
└────────────────────────────┬─────────────────────────────────────┘
                             │  pinned release (e.g. stable → v1.4.0)
┌────────────────────────────▼─────────────────────────────────────┐
│  Golden Path MCP Server (hosted, SSO)                            │
│    Resources: goldenpath://skills/*  goldenpath://docs/*         │
│    Tools: scaffold_service, get_deploy_status, list_services, …  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
  Claude Code            Claude Code              Other MCP clients
       │                     │                     │
       └─────────────────────┴─────────────────────┘
                             │
                             ▼
              Service repo  →  GitHub Actions  →  GCP
              (Layer A)
```

### Critical design rule

```
MCP = front door (guidance + orchestration)
CI  = deploy engine (runs on every push)
GCP = runtime (Cloud Run, secrets, observability)
```

Production deploys **must work** when MCP is down.

---

## 8. Reference architecture (GCP)

Standard Shop service on the Golden Path (common case):

| Area | Standard | Notes |
|------|----------|-------|
| **Runtime** | Cloud Run | Containerized app; scale-to-zero default |
| **Images** | Artifact Registry | Built in CI, immutable tags |
| **Infrastructure** | Terraform | No click-ops in production |
| **Secrets** | Secret Manager | Never in repos or `.env` committed to git |
| **CI auth** | Workload Identity Federation | No long-lived service account keys |
| **App auth** | Identity Platform or IAP | Per-product choice |
| **Data** | Cloud SQL / Firestore / none | Opt-in modules; not required in base template |
| **Observability** | Cloud Logging, Monitoring, Cloud Trace | OpenTelemetry; baseline dashboard + alerts |
| **Environments** | `dev` → `prod` | Promotion via gated pipeline |

### Deploy flow

```
lint → test → build image → push to Artifact Registry
  → Terraform plan/apply → deploy Cloud Run (dev)
  → (manual approval or tag) → deploy Cloud Run (prod)
```

### Acceptance test (most important criterion)

> A developer scaffolds a new project and deploys end-to-end to **`dev` with zero manual edits**.

If this passes, Golden Path works. Everything else accelerates adoption.

---

## 9. Framework and templates

### Default: Next.js

The **first template** is a containerized **Next.js** app — the documented common case in the original requirements.

### Not Next.js-only

The **platform** (Cloud Run, Terraform, CI/CD) is **framework-agnostic**. Only the **app template** changes per framework.

| Layer | Next.js | Streamlit | React SPA | Svelte |
|-------|---------|-----------|-----------|--------|
| Terraform modules | Shared | Shared | Shared | Shared |
| CI/CD workflow | Shared | Shared | Shared | Shared |
| Dockerfile | Node multi-stage | Python | Node/static | Node |
| App scaffold | Next.js | Streamlit | Vite/React | SvelteKit |

### Multi-template model (future)

```
goldenpath/templates/
├── nextjs/       # default paved road
├── streamlit/
├── react-spa/
└── svelte/
```

CLI / MCP:

```bash
shop new my-app --template nextjs --output ..      # default template
shop new my-dashboard --template streamlit --output ..
```

### Off-road before a template exists

Reuse **shared modules + CI workflow** with your own Dockerfile and app code — half paved road until a template is added.

---

## 10. Golden Path MCP server

### Why MCP for skills and docs

| Problem with local skills | MCP solution |
|---------------------------|--------------|
| Copy to laptop | Connect MCP once |
| Developers edit skills | Read-only Resources |
| Version drift | Pinned `stable` / `beta` channels |
| Skills vs docs vs tools out of sync | One server, one release tag |

### MCP Resources (virtual filesystem)

| URI | Content |
|-----|---------|
| `goldenpath://skills/{name}/SKILL.md` | Agent skill instructions |
| `goldenpath://skills/{name}/*` | Bundled references, scripts |
| `goldenpath://docs/{path}` | Start here, quickstart, runbooks, conventions |
| `goldenpath://meta/version` | Channel, git tag, release notes |

Helper tools (if client has weak Resource support): `list_skills()`, `get_skill(name)`, `get_doc(path)`.

### MCP Tools (phased)

| Phase | Tools | Access |
|-------|-------|--------|
| **v1 — read** | `list_services`, `get_deploy_status`, `get_service_config`, `get_cost_estimate`, `list_templates` | All authenticated devs |
| **v2 — write** | `scaffold_service`, `trigger_deploy`, `validate_service_repo` | Guarded + audited |

### Version channels

| Channel | Points to | Audience |
|---------|-----------|----------|
| `stable` | e.g. `v1.4.0` | All product engineers |
| `beta` | e.g. `v1.5.0-rc1` | Pilot team |
| `main` | Latest | Platform internal only — not default |

### Security rules

| Rule | Requirement |
|------|-------------|
| **Authentication** | SSO / OIDC |
| **Authorization** | MCP never exceeds caller’s GCP/GitHub permissions |
| **Writes** | Audit log; confirmation for deploy |
| **Official content** | Admin-only merges via GitHub branch protection + team reviews |

### Core skills (authored in GitHub, served via MCP)

| Skill | Purpose |
|-------|---------|
| `scaffold-shop-service` | Create repo, explain layout |
| `deploy-to-shop-gcp` | Dev/prod promotion, rollback, failures |
| `goldenpath-setup-wizard` | Full wizard onboarding via AI |
| `shop-terraform-conventions` | Extend infra safely |
| `shop-observability` | Logs, metrics, traces, alerts |

---

## 11. Developer workflows

### 11.1 Onboarding (fresh laptop)

| Step | Action |
|------|--------|
| 1 | Obtain MCP endpoint URL and SSO access (from platform onboarding) |
| 2 | Add Golden Path MCP to Claude Code config |
| 3 | Optional: install `shop` CLI for terminal scaffolding |
| 4 | Read `goldenpath://docs/getting-started/01-start-here.md` or ask Claude for quickstart |
| 5 | Scaffold first service; push to `main`; verify `dev` URL |

**Target time:** under 15 minutes to first scaffold; under one day to first successful `dev` deploy.

### 11.2 Create a new service

**Option A — AI (preferred)**

1. *“Scaffold a Shop service named `payments-api` with template `nextjs`”*
2. Claude loads `scaffold-shop-service` skill from MCP
3. Skill invokes `scaffold_service` tool
4. New GitHub repo created with all wiring
5. Clone (if needed), push, merge → `dev` deploy

**Option B — CLI**

```bash
shop new payments-api --template nextjs --output ..
shop publish ../payments-api
```

**Option C — GitHub template**

Use **Use this template** on `shop-service-template` repo, fill naming variables, push.

### 11.3 Daily development loop

```
branch → code → PR → review → merge to main → CI → dev deploy → verify
```

### 11.4 Promote to production

```
verify in dev → approve prod gate in CI (or create release tag) → prod deploy → smoke check
```

Exact gate mechanism is standardized across all Golden Path services.

### 11.5 Secrets

| Do | Don't |
|----|-------|
| Store in Secret Manager | Commit secrets to git |
| Reference secret names in Terraform / Cloud Run config | Put secrets in `.env` in repo |
| Follow skill/doc for rotation | Share secrets in Slack |

### 11.6 Observability

| Signal | Where |
|--------|-------|
| **Logs** | Cloud Logging — structured JSON |
| **Metrics** | Cloud Monitoring — default dashboard per service |
| **Traces** | Cloud Trace — OpenTelemetry |
| **Alerts** | Baseline policies from observability module |

---

## 12. What you do not have to do

When using Golden Path, you are **not** responsible for:

- Inventing repo structure from scratch
- Writing GitHub Actions → GCP integration from zero
- Manually creating Cloud Run services in console
- Creating and rotating long-lived CI service account keys
- Copying Terraform from another team’s repo
- Designing IAM from scratch for a basic service
- Building logging/metrics/tracing plumbing yourself
- Hunting tribal knowledge for “how Shop deploys”
- Maintaining local copies of platform skills or runbooks

---

## 13. Off-road and edge cases

Golden Path covers the **common case**. Use off-road when:

| Situation | Approach |
|-----------|----------|
| Unusual architecture (e.g. heavy Kafka, mobile backend with special needs) | Custom design; platform consults |
| Framework not yet templated | Shared modules + custom Dockerfile |
| Team-specific compliance beyond baseline | Security review + custom IaC |
| Legacy service | No forced migration; optional adoption later |

**Off-road policy** (who supports what) is documented at `goldenpath://docs/off-road-policy.md` and finalized in platform open decisions.

Personal or team customizations must **not** edit official `goldenpath://` content — use separate namespaces or repos.

---

## 14. Without MCP (fallbacks)

Golden Path must remain usable if MCP is unavailable.

| Need | Fallback |
|------|----------|
| **Scaffold** | `shop new` CLI or GitHub template button |
| **Deploy** | Push to `main` → GitHub Actions (unchanged) |
| **Docs** | Static mirror (GitHub Pages / internal site) |
| **Status** | GitHub Actions UI, `gcloud`, GCP console |
| **Help** | `#golden-path` support channel |

MCP is the **preferred** experience, not a **hard dependency** for production.

---

## 15. For platform teams

### Repository layout

```
goldenpath/
├── platform/           # Bootstrap: GCP folders, WIF, org IAM, Artifact Registry
├── modules/            # Versioned Terraform modules
├── .github/workflows/  # Reusable deploy workflow (service repos call @GOLDENPATH_VERSION)
├── templates/          # Service scaffolds (nextjs, streamlit, …)
├── skills/             # SKILL.md files (served via MCP)
├── docs/               # Start here, quickstart, runbooks (served via MCP)
├── cli/                # shop new (thin wrapper)
├── scripts/            # standup / teardown helpers
└── mcp/                # Golden Path MCP server implementation
```

### Terraform modules (platform-owned)

| Module | Responsibility |
|--------|----------------|
| `service-identity` | Runtime service account, IAM bindings |
| `artifact-registry` | Repo + reader permissions |
| `cloud-run` | Service, env, secrets refs, invoker IAM |
| `secrets` | Secret Manager + accessor bindings |
| `observability` | Dashboard, alerts, log-based metrics |
| `wif-ci` | GitHub OIDC → GCP (bootstrap) |

Version with git tags (`v1.4.0`). Services pin module versions.

### Governance

| Concern | Mechanism |
|---------|-----------|
| Who changes official path | Platform team review (GitHub branch protection / PRs; CODEOWNERS when configured) |
| Release train | Tag bundles modules + template refs + skills + docs |
| Breaking changes | Semver, migration notes, comms |
| MCP `stable` pointer | Updated only by platform admins |

### Comparison: original requirements vs evolved delivery

| Dimension | Original draft | Evolved (this guide) |
|-----------|----------------|----------------------|
| Layer A | Templates, modules, CI | **Same** |
| Skills delivery | Local / marketplace | **MCP Resources from git** |
| Docs delivery | Separate portal/site | **MCP Resources** + static mirror |
| MCP role | Actions only | **Actions + knowledge distribution** |
| §6 MCP hosting | Open | Hosted internal + SSO |
| §7 Skill distribution | Open | MCP pinned releases |

See [MCP Evolution Proposal](../design/golden-path-mcp-evolution-proposal.md) for full rationale.

---

## 16. Phasing and rollout

| Phase | Focus | Exit criterion |
|-------|-------|----------------|
| **0 — Align** | Stack decisions, pilot team, metrics, MCP distribution model | Signed decisions; pilot committed |
| **1 — Paved road (Layer A)** | Modules, CI workflow, Next.js template, GCP bootstrap | Pilot deploys to `dev`, **zero manual edits** |
| **2 — MCP (Layer B)** | Resources (skills/docs) + read tools → write tools | Fresh laptop + MCP only → scaffold and deploy |
| **3 — Scale (Layer C)** | Rollout, metrics, optional extra templates, portal if needed | Adoption and satisfaction targets trending |

**Phase 1 does not depend on MCP.** Prove the road first.

---

## 17. Success metrics

| Metric | Target |
|--------|--------|
| Time to first `dev` deploy (new service) | < 1 day (< 1 hour stretch) |
| Manual steps after scaffold | **0** |
| % new services from Golden Path template | Track; aim > 50% within 6 months |
| % services with standard telemetry | 100% for templated services |
| Security findings (secrets/IAM) on new services | Decrease vs baseline |
| Developer satisfaction | Pilot survey: faster than DIY |

---

## 18. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| **Low adoption** | Co-design with pilot; measure time-to-deploy honestly |
| **Template / module / skill drift** | Single release tag; platform owner for sync |
| **MCP security gap** | No privilege escalation; read-only first; audit writes |
| **Over-engineering** | Docs via MCP first; defer Backstage |
| **MCP downtime** | CI-independent deploys; static doc mirror; CLI fallback |
| **Client Resource support gaps** | `get_skill` / `get_doc` helper tools |

---

## 19. Open decisions

Resolved by this guide:

| # | Decision | Resolution |
|---|----------|------------|
| 6 | MCP hosting | Hosted internal MCP, HTTPS, SSO |
| 7 | Skill distribution | MCP Resources from pinned git |
| 5 | Developer portal | MCP docs first; Backstage deferred |
| 4 | Template delivery | MCP `scaffold_service` + GitHub template + CLI |

Still open for Phase 0:

| # | Decision | Options |
|---|----------|---------|
| 1 | Compute runtime | Cloud Run (assumed) vs Firebase App Hosting vs GKE |
| 2 | IaC tool | Terraform (assumed) vs Pulumi vs Config Connector |
| 3 | CI/CD platform | GitHub Actions vs Cloud Build vs GitLab CI |
| 8 | Database defaults | Cloud SQL vs Firestore vs per-service |
| 9 | Environment topology | dev/prod vs staging; shared vs per-team projects |
| 10 | Off-road policy | Support boundaries for non-Golden-Path services |

---

## 20. Quick reference

### Developer cheat sheet

```
ONBOARD     →  Connect Golden Path MCP (+ optional shop CLI)
NEW SERVICE →  MCP scaffold or shop new <name> → push main → dev live
DAILY       →  code → merge → auto dev deploy
PROD        →  approve CI gate or release tag
STATUS      →  MCP get_deploy_status or GitHub Actions
SECRETS     →  Secret Manager only
LOGS        →  Cloud Logging / standard dashboards
HELP        →  Claude + official skills, or #golden-path
```

### MCP tools (Phase 2 — shipped in `v0.3.8`)

**13 tools** — full list in [`mcp/README.md`](../../mcp/README.md). Bootstrap and `shop publish` are **not** MCP tools.

| Tool | Purpose |
|------|---------|
| `list_templates` / `list_skills` / `get_skill` / `list_docs` / `get_doc` / `get_version` | Catalog, skills, docs |
| `list_services` | Cloud Run services with Golden Path labels |
| `get_deploy_status` | Last deploy state |
| `get_service_config` | Cloud Run spec summary |
| `get_cost_estimate` | Cost visibility |
| `scaffold_service` | Run `shop new` on disk (write, audited) |
| `validate_service_repo` | Check repo layout |
| `trigger_deploy` | `workflow_dispatch` (write, guarded) |

### Key URLs / paths (conceptual)

| Path | Content |
|------|---------|
| `goldenpath://docs/getting-started/01-start-here.md` | Entry point |
| `goldenpath://docs/getting-started/03-quickstart.md` | 15-minute tutorial |
| `goldenpath://skills/scaffold-shop-service/SKILL.md` | Scaffolding skill |
| `goldenpath://skills/deploy-to-shop-gcp/SKILL.md` | Deploy runbook skill |

---

## 21. FAQ

### Is Golden Path only for Next.js?

**No.** Next.js is the **first** template. The deploy pipeline and Terraform modules work for any containerized app. Additional templates (Streamlit, React, Svelte) plug into the same path.

### Do I have to use MCP?

**No.** You can use the CLI or GitHub template and push code normally. MCP is the recommended way to get consistent skills, docs, and platform tools.

### Can I edit Golden Path skills locally?

**Not official skills.** They are read-only via MCP to prevent drift. For custom workflows, use team-specific docs or off-road patterns — do not fork official skills silently.

### Does MCP deploy my code?

**Indirectly.** `trigger_deploy` may kick off the same pipeline as a git push. Day-to-day deploys happen via **merge to `main`** and GitHub Actions.

### What if I need something Golden Path does not support?

Go **off-road**: consult platform/security, reuse modules where possible. Golden Path is opt-in, not a cage.

### Will existing services be forced to migrate?

**No.** Adoption is earned through speed and safety, not mandate at launch.

### Who do I contact for help?

`#golden-path` (or platform support channel defined at launch). Ownership: Platform / DevEx team.

---

## 22. Glossary

| Term | Definition |
|------|------------|
| **Golden Path / paved road** | Opinionated, supported default route for deploying Shop services to GCP |
| **Layer A** | Templates, Terraform modules, CI/CD — the runnable road |
| **Layer B** | Golden Path MCP server — skills, docs, and platform tools |
| **Layer C** | Discoverability, onboarding, support, metrics |
| **Agent Skill** | `SKILL.md` instructions Claude loads to perform tasks the Shop way |
| **MCP** | Model Context Protocol — connects AI clients to tools and resources |
| **MCP Resource** | Read-only URI (e.g. skill or doc) served from pinned git content |
| **MCP Tool** | Callable action (e.g. `get_deploy_status`, `scaffold_service`) |
| **Release channel** | Named pointer (`stable`, `beta`) to a git tag on MCP |
| **Off-road** | Custom architecture outside the common Golden Path case |
| **IaC** | Infrastructure as Code (Terraform) — infra in version control |
| **WIF** | Workload Identity Federation — keyless CI authentication to GCP |
| **Acceptance test** | Scaffold → deploy to `dev` with zero manual edits |

---

## Related documents

- [MCP Evolution Proposal](../design/golden-path-mcp-evolution-proposal.md) — detailed comparison with original requirements and distribution rationale
- [Repository readme](../readme.md) — entry point and doc index

---

*Document version: 1.0 — 2026-06-15*

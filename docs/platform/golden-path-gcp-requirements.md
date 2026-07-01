# Requirements: Golden Path for deploying to the shop's GCP environment

**Status:** Draft for review **Owners:** *Platform / DevEx team (TBD)* **Last updated:** 2026-06-15 **Reviewers:** *Eng leads, Security, SRE/Platform, a pilot product team*

This document defines what we are building, why, and how we will know it worked. It deliberately leaves stack choices open where a decision is still owed; those are collected in **§9 Open Decisions**. Anything marked *(assumption)* is a starting position, not a settled choice.

---

## 1\. Problem statement

Developers shipping into the Shop's GCP environment currently re-solve the same problems on every new service: how to structure a repo, wire CI/CD, provision infrastructure, handle secrets and auth, and get observability. This is slow, inconsistent, and pushes security and reliability decisions onto individual developers who shouldn't have to own them.

A **Golden Path** (a "paved road") is an opinionated, supported, well-documented route for the common case. It is the path of least resistance that is *also* the secure, observable, compliant one. Teams that need something different can still go off-road, but the default should be fast and safe.

## 2\. Goals

- Reduce **time-to-first-production-deploy** for a new service from days/weeks to under one day.  
- Make the secure, observable, cost-aware setup the *default*, not an add-on.  
- Standardize how Shop services are built and deployed so they are legible to SRE, security, and any engineer who rotates teams.  
- Provide an AI-assisted developer experience (Claude \+ Claude Code) that generates on-pattern code and can perform routine platform operations.

## 3\. Non-goals

- Forcing all existing services to migrate immediately (the path is opt-in; adoption is earned, not mandated at launch).  
- Supporting every possible architecture. The Golden Path covers the **common case** (a containerized web service / API). Edge cases remain off-road.  
- Replacing the Platform/SRE team's judgment with automation. The tooling assists; humans own production.

## 4\. Target users (personas)

- **Product engineer** — wants to ship a feature behind a service without learning all of GCP. Primary customer.  
- **Tech lead** — wants consistency across their team's services and a clear review surface.  
- **SRE / Platform engineer** — wants every service to emit standard telemetry, follow IaC conventions, and be supportable.  
- **Security** — wants guardrails (least-privilege IAM, keyless auth, secret hygiene) enforced by the path rather than reviewed case-by-case.

## 5\. Solution overview — three layers

The Golden Path is not a single artifact. It is three layers that reinforce each other.

### Layer A — Paved-road artifacts (the path itself)

The concrete, runnable building blocks:

1. A **reference architecture** for a standard Shop service on GCP.  
2. Reusable **infrastructure-as-code modules** (e.g., Terraform) for that architecture.  
3. A **standard CI/CD pipeline** template.  
4. A **Next.js scaffolding template** that ties A1–A3 together and produces a deployable "hello world" on day one.

### Layer B — AI-assisted developer experience

1. **Agent Skills** — `SKILL.md` folders that encode the Shop's conventions, runbooks, and templates so Claude and Claude Code produce on-pattern output and follow the deployment process. Skills load on demand (progressive disclosure), can bundle scripts and reference files, and work across Claude.ai, Claude Code, and the Claude API. Author them as internal skills, e.g. `scaffold-shop-service`, `deploy-to-shop-gcp`, `shop-terraform-conventions`.  
2. **An MCP server** — exposes the platform's live capabilities to Claude as tools (status, deploys, scaffolding, config lookup, cost). Distinct from skills: **skills carry the knowledge, MCP carries the live actions and data**. A skill can instruct Claude *when and how* to call the MCP tools.

### Layer C — Discoverability & support

Docs, onboarding, ownership, a service catalog/portal entry point, and adoption metrics. A paved road no one can find is just a road.

## 6\. Functional requirements

### 6.1 Reference architecture *(assumptions — confirm in §9)*

The standard Shop service should target:

- **Runtime:** Cloud Run for a containerized Next.js app *(assumption; Firebase App Hosting is a GCP-native SSR alternative, GKE if container orchestration is already standard)*.  
- **Images:** built and stored in Artifact Registry.  
- **Infra:** declared in Terraform; no click-ops in production.  
- **Secrets:** Secret Manager; never in env files or repos.  
- **Identity / auth:** Identity Platform or IAP for app auth; Workload Identity Federation for keyless CI → GCP auth (no long-lived service-account keys).  
- **Data:** Cloud SQL / Firestore as appropriate *(per-service decision)*.  
- **Observability:** structured logging to Cloud Logging, metrics to Cloud Monitoring, traces via OpenTelemetry → Cloud Trace; a baseline dashboard and alerts provisioned by default.  
- **Environments:** at minimum `dev` → `prod`, with promotion via the pipeline.

### 6.2 Next.js template

- One command (or one MCP tool call) produces a new repo with: a working Next.js app, Dockerfile, Cloud Run service config, Terraform for its infra, the CI/CD pipeline, linting/formatting, a test harness, OpenTelemetry wiring, and Secret Manager integration.  
- The freshly scaffolded project must **deploy end-to-end to `dev` with no manual edits** — this is the single most important acceptance test for the whole initiative.  
- Sensible, overridable defaults; the template is a starting point, not a cage.  
- Delivery mechanism options (see §9): a GitHub *template repository* \+ a thin CLI, a custom `create-next-app` template, or a developer-portal scaffolder (e.g. Backstage) if one is in scope.

### 6.3 CI/CD pipeline

- Standard stages: lint → test → build image → push to Artifact Registry → deploy to `dev` → gated promotion to `prod`.  
- Keyless auth via Workload Identity Federation.  
- Pipeline defined as code and shared across services (reusable workflow / config), not copy-pasted.

### 6.4 Agent Skills (Layer B)

- An internal skill set covering: scaffolding a new service, the deployment runbook, IaC/repo conventions, and observability expectations.  
- Each skill is a self-contained folder with a `SKILL.md` (YAML frontmatter \+ instructions) and may bundle scripts/templates.  
- Skills should be versioned in a repo and distributable to the team (e.g. as a Claude Code plugin marketplace and/or via the API/Claude.ai for paid plans).  
- **Definition of done for a skill:** a developer using Claude Code on a fresh machine can scaffold and deploy a compliant service guided by the skill alone.

### 6.5 MCP server (Layer B)

- Exposes tools such as: `scaffold_service`, `get_deploy_status`, `trigger_deploy` (with appropriate authorization), `get_service_config`, `list_services`, `get_cost_estimate`.  
- Authenticated; respects the caller's existing GCP permissions — the server must not become a privilege-escalation path.  
- Read-heavy tools first (status, catalog, config); write/action tools (deploy) added once auth and audit are solid.  
- Decide on hosting and transport (see §9).

### 6.6 Documentation & onboarding (Layer C)

- A single "Start here" page describing the path and when *not* to use it.  
- A 15-minute quickstart proven against the acceptance test in §6.2.  
- Clear ownership and a support channel.

## 7\. Non-functional requirements

- **Security:** least-privilege IAM by default; keyless CI auth; secrets only in Secret Manager; the MCP server never broadens a user's effective permissions.  
- **Reliability:** the template's default config should pass the platform's production-readiness checklist out of the box.  
- **Cost:** scale-to-zero defaults where appropriate; cost visibility surfaced (dashboard and/or MCP tool).  
- **Maintainability:** all artifacts versioned; breaking changes to template/modules/skills are communicated and migratable.  
- **Adoptability:** the path must be measurably faster than rolling your own, or teams won't use it.

## 8\. Success metrics

- Time-to-first-`dev`\-deploy for a new service (target: \< 1 day; stretch: \< 1 hour).  
- Number / percentage of new services started from the template.  
- Percentage of services emitting standard telemetry.  
- Reduction in security findings related to secrets/IAM on new services.  
- Developer satisfaction (qualitative survey of pilot teams).

## 9\. Open decisions

These need owners and answers before or during Phase 1\.

| \# | Decision | Options / notes |
| :---- | :---- | :---- |
| 1 | Compute runtime | Cloud Run *(assumed)* vs Firebase App Hosting vs GKE |
| 2 | IaC tool | Terraform *(assumed)* vs Config Connector vs Pulumi |
| 3 | CI/CD platform | GitHub Actions vs Cloud Build vs GitLab CI |
| 4 | Template delivery | GitHub template repo \+ CLI vs custom create-next-app vs Backstage scaffolder |
| 5 | Developer portal | Adopt one (e.g. Backstage) for discoverability, or docs-only to start? |
| 6 | MCP server hosting & transport | Where it runs, auth model, remote vs local |
| 7 | Skill distribution | Claude Code plugin marketplace, API, Claude.ai, or all |
| 8 | Database defaults | Cloud SQL vs Firestore as the standard, or per-service |
| 9 | Environment topology | `dev`/`prod` only vs adding `staging`; per-team vs shared projects |
| 10 | "Off-road" policy | What's supported when a team needs something the path doesn't cover |

## 10\. Phasing

**Phase 0 — Align (this doc).** Confirm §9 decisions, pick one pilot team, agree on the success metrics.

**Phase 1 — The paved road (Layer A).** Reference architecture \+ Terraform modules \+ CI/CD \+ Next.js template. Exit criterion: pilot team scaffolds and deploys a real service end-to-end with no manual edits.

**Phase 2 — AI-assisted DX (Layer B).** Author the core Agent Skills against the Phase 1 artifacts. Stand up the MCP server with read-only tools first, then a guarded `trigger_deploy`/`scaffold_service`.

**Phase 3 — Scale & support (Layer C).** Docs, onboarding, portal/catalog entry, broader rollout, and a feedback loop. Treat the path as a product with internal customers.

## 11\. Risks

- **Low adoption** if the path isn't meaningfully faster than DIY — mitigate by co-designing with the pilot team and measuring time-to-deploy honestly.  
- **Drift** between the template, the IaC modules, and the skills as each evolves — mitigate with versioning and an owner for keeping them in sync.  
- **MCP server as a security gap** — mitigate by never exceeding the caller's own permissions, auditing all write actions, and shipping read-only first.  
- **Over-engineering** (building a portal/platform no one asked for) — mitigate by starting docs-only and earning the next layer.

## 12\. Appendix — glossary

- **Golden Path / paved road:** the opinionated, supported default route for a common engineering task.  
- **Agent Skill:** a `SKILL.md`\-based folder of instructions (and optional scripts/resources) Claude loads on demand to perform a task in a repeatable, on-pattern way.  
- **MCP (Model Context Protocol):** an open standard for connecting an AI assistant to external tools and data via a server that exposes those capabilities.  
- **IaC:** infrastructure as code (e.g., Terraform) — infrastructure defined in version-controlled files rather than configured by hand.  
- **Workload Identity Federation:** lets CI authenticate to GCP without long-lived service-account keys.


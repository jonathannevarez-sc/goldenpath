# Golden Path — Q&A Gold Mine

**Platform version:** v0.3.7  
**Purpose:** Comprehensive question-and-answer preparation for executive briefings, technical deep-dives, security reviews, and developer onboarding sessions.  
**Audience:** Presenters, platform sponsors, and subject-matter experts fielding questions about Golden Path.

---

## Executive Overview

Golden Path (`goldenpath`) is an enterprise-agnostic developer platform for building and deploying containerized services to Google Cloud Platform. The platform repository supplies bootstrap infrastructure, reusable modules, six service templates, a `shop` command-line tool, four setup-wizard backends, a reusable GitHub Actions deploy workflow, and an MCP server that exposes official skills, documentation, and platform tools to AI coding assistants.

Developers scaffold **separate service repositories** — not applications inside the platform repo itself. They push code; GitHub Actions deploys to Cloud Run using keyless Workload Identity Federation authentication. The acceptance test: scaffold a new project and deploy end-to-end to `dev` with **zero manual edits**.

Golden Path is **opt-in for legacy services**. It is not a forced migration. Three onboarding paths — CLI, wizard, and MCP — converge on identical artifacts. Enterprise-specific values (billing, projects, GitHub org, region) live in `config/enterprise.env`, not in committed scripts.

This document provides confident, specific answers referencing Golden Path v0.3.7 capabilities. Use it to prepare for any audience — from the boardroom to the engineering standup.

---

## Table of Contents

1. [Executive & Business Questions](#executive--business-questions) (12 Q&As)
2. [Technical Questions](#technical-questions) (16 Q&As)
3. [Security & Compliance Questions](#security--compliance-questions) (12 Q&As)
4. [Developer Experience Questions](#developer-experience-questions) (12 Q&As)
5. [Challenges & Future Questions](#challenges--future-questions) (8 Q&As)
6. [Preparation Tips](#preparation-tips)
7. [Why This Document Is a Gold Mine](#why-this-document-is-a-gold-mine)

**Total Q&As: 60**

---

## Executive & Business Questions

### Q1. What is Golden Path in one sentence for the board?

Golden Path is our organization's paved road for shipping containerized cloud services — a shared platform that lets product engineers scaffold a new service, push code, and land on Google Cloud Run in development with security, secrets management, and monitoring already wired, while platform and security teams set the guardrails once instead of reviewing every bespoke setup.

### Q2. What business problem does Golden Path solve?

Today, every new Cloud Run service forces teams to reinvent repository layout, continuous integration, infrastructure provisioning, identity management, secret handling, and observability. That work is largely identical across services but rarely shared in a durable, versioned form. Golden Path closes that gap by packaging bootstrap Terraform, reusable modules, six service templates, a shared deploy workflow, and centralized skills/documentation into one platform repository. The business outcome is faster time-to-market, lower cost per new service, and a consistent risk posture across the portfolio.

### Q3. What is the return on investment?

ROI comes from eliminating repeated platform work. Without Golden Path, each new service typically costs days or weeks of engineering time before the first feature ships — time spent on CI/CD wiring, Cloud Run provisioning, IAM design, and monitoring setup that does not differentiate the product. Golden Path's stated goal is reducing time to first production deploy from days/weeks to under one day, with a stretch target of under one hour for experienced users. Platform team investment is front-loaded (one-time bootstrap, ongoing module maintenance), but amortizes across every subsequent service. Security review cycles shorten because new services arrive pre-aligned with organizational standards.

### Q4. Who are the primary users and beneficiaries?

Four personas benefit directly. **Product engineers** scaffold services and edit application code in `src/` without learning all of GCP. **Tech leads** get consistent repo shape, pipeline, and conventions across their team. **Platform and SRE teams** support services with standard telemetry, infrastructure-as-code, and recognizable layouts. **Security teams** review services that already include least-privilege IAM, keyless CI authentication, and Secret Manager — not ad hoc configurations. Executives benefit indirectly through measurable delivery speed, reduced incident risk, and engineering capacity redirected from infrastructure to product innovation.

### Q5. Is Golden Path mandatory for existing services?

No. Golden Path is explicitly opt-in for existing services. The platform guide lists "forced migration" as a non-goal. Adoption is earned through speed and safety, not mandate at launch. New services are encouraged to use Golden Path because the paved road is faster and more secure. Legacy services can adopt selectively, go off-road with platform consultation, or remain on their current stack indefinitely.

### Q6. How do we measure success?

Golden Path defines concrete success metrics in the platform guide. Primary targets include: time to first `dev` deploy under one day (stretch: under one hour), zero manual steps after scaffold, tracking percentage of new services created from Golden Path templates (aim >50% within six months), 100% standard telemetry for templated services, decreasing security findings on new services versus baseline, and positive developer satisfaction from pilot surveys. The acceptance test — scaffold and deploy to `dev` with zero manual edits — is the most important technical criterion; if it passes, the platform works.

### Q7. What does v0.3.7 include today?

Version v0.3.7 delivers Phase 1 (paved-road artifacts) and Phase 2 (MCP server) in an enterprise-agnostic form. Concrete deliverables include: bootstrap Terraform for one-time GCP setup with Workload Identity Federation, five reusable Terraform modules (cloud-run, secrets, service-identity, artifact-registry, observability), six service templates (Next.js, FastAPI, Streamlit, Express, React SPA, Svelte SPA), the `shop` CLI, four wizard backends (bash, Python, PowerShell, Streamlit) sharing a 15-option menu, a reusable GitHub Actions `deploy.yml` workflow, an MCP server with 13 tools and 3 resources, and six official agent skills. Enterprises configure org-specific values in `config/enterprise.env`.

### Q8. How does Golden Path compare to hiring more platform engineers?

Golden Path does not replace platform engineers — it multiplies their impact. Instead of each platform engineer supporting bespoke deployments across dozens of unique service layouts, the team maintains one versioned platform that every service inherits. Platform engineers own modules, templates, workflows, skills, and release governance. Product engineers own application code. The ratio shifts: fewer hours per service on repetitive setup, more hours on platform improvements that benefit the entire organization. Golden Path is the institutional memory and assembly line; platform engineers are the factory operators.

### Q9. What is the rollout plan?

Rollout follows four phases defined in the platform guide. **Phase 0 — Align:** stack decisions, pilot team commitment, metrics definition. **Phase 1 — Paved road:** modules, CI workflow, templates, GCP bootstrap; exit criterion is pilot deploys to `dev` with zero manual edits. **Phase 2 — MCP:** skills/docs resources plus read and write tools; exit criterion is fresh-laptop onboarding via MCP only. **Phase 3 — Scale:** broader rollout, adoption metrics, optional additional templates. Phase 1 does not depend on MCP — prove the road first, then add AI-assisted delivery.

### Q10. What happens if we do nothing?

Without Golden Path, the organization continues paying the per-service tax: weeks of setup, inconsistent security postures, monitoring gaps, tribal knowledge in wikis and laptops, and longer incident response times because every service looks different. AI coding assistants will lack authoritative, versioned procedures — developers will paste stale skills or improvise. Security reviews will remain reactive, catching issues late. Engineering leaders will lack a measurable baseline for deployment speed. The competitive cost is slower experimentation and duplicated platform work that does not create customer value.

### Q11. Can Golden Path work for multiple business units or enterprises?

Yes. Golden Path is enterprise-agnostic by design. Org-specific values — billing account, dev/prod/sandbox project IDs, GitHub organization, region, naming conventions — live in `config/enterprise.env`, which is gitignored locally. The same platform codebase serves multiple enterprises by swapping configuration, not forking the repository. Service repos pin `goldenpath_version` in their Terraform variables and reference the reusable workflow at the matching git tag (e.g., `@v0.3.7`). This portability is a deliberate architectural choice documented in the problem statement.

### Q12. What is the relationship between Golden Path and our cloud provider commitment?

Golden Path standardizes on Google Cloud Platform and Cloud Run as the default runtime for the common case — containerized web services and APIs. This aligns platform investment with a single cloud provider's primitives: Artifact Registry, Secret Manager, Cloud Monitoring, and Workload Identity Federation. The platform is framework-agnostic at the application layer (six templates share the same modules and deploy workflow), but the infrastructure layer is GCP-specific. Organizations committed to GCP gain a paved road; multi-cloud is explicitly outside the common-case scope and would be an off-road engagement.

---

## Technical Questions

### Q13. What is the Golden Path repository — platform or application?

The `goldenpath` repository is the **platform**, not an application. Running `shop new my-service` copies a template into a **separate service repo** (sibling directory or its own GitHub repository). The platform repo supplies bootstrap Terraform, reusable modules, templates, the `shop` CLI, wizards, MCP server, skills, and documentation. Application code lives in service repos under `src/`. This separation is documented in the root README and `docs/repository-guide.md` and is critical for audiences to understand.

### Q14. What are the three layers of the solution architecture?

Golden Path has three layers governed by one rule: MCP is the front door, CI is the deploy engine, GCP is the runtime. **Layer A — Paved-road artifacts:** bootstrap Terraform, reusable modules, six service templates, and the shared `deploy.yml` workflow — this is what actually runs in production. **Layer B — MCP server:** serves official skills and docs as read-only resources, plus 13 platform tools for status, scaffolding, validation, and guarded deploy triggers. **Layer C — Discoverability and support:** getting-started docs, wizard menus, support channels, and adoption metrics. Layers B and C improve developer experience; Layer A is the non-negotiable foundation.

### Q15. What templates are available in v0.3.7?

Six official templates ship in `templates/`, cataloged in `templates/catalog.json`:

| Template | Runtime | Use case |
|----------|---------|----------|
| `nextjs` | Node.js | Default — containerized Next.js App Router |
| `fastapi` | Python | REST APIs |
| `streamlit` | Python | Data dashboards and internal tools |
| `express` | Node.js | Lightweight Node APIs |
| `react-spa` | Node/static | React + Vite + nginx |
| `svelte-spa` | Node/static | Svelte + Vite + nginx |

All six share the same Terraform modules, CI/CD workflow, and observability wiring. Only the application scaffold and Dockerfile differ.

### Q16. How does the deployment pipeline work end-to-end?

When a developer pushes to `main` in a service repo, GitHub Actions triggers the reusable `deploy.yml` workflow from the goldenpath repo at the pinned version tag. The pipeline runs checkout, optional runtime tests (npm ci + lint/test for Node, pip + ruff/pytest for Python), authenticates to GCP via Workload Identity Federation (OIDC token exchange — no stored keys), builds a Docker image and pushes to Artifact Registry, runs `terraform init/plan/apply` using shared modules from the git tag, resolves the Cloud Run service URL, and performs a smoke check (curl health path, five retries). Service repos pass all required inputs (project, region, org, version, artifact registry repo) as workflow caller inputs.

### Q17. What Terraform modules does each service use?

Every scaffolded service's `infra/main.tf` composes four modules in dependency order: `service-identity` (runtime service account), `secrets` (Secret Manager secrets and accessor IAM), `cloud-run` (Cloud Run v2 service, probes, invoker IAM), and `observability` (monitoring dashboard and 5xx alert policy). Modules are fetched from the goldenpath git tag pinned in `goldenpath_version` — services do not copy module source. The bootstrap layer (`platform/bootstrap/`) is separate and runs once per organization to establish WIF, IAM, and Artifact Registry foundations.

### Q18. What is Workload Identity Federation and why does it matter?

Workload Identity Federation (WIF) enables GitHub Actions to authenticate to GCP without long-lived service account keys. Bootstrap Terraform in `platform/bootstrap/wif.tf` creates a workload identity pool and OIDC provider scoped to `token.actions.githubusercontent.com`, with an attribute condition restricting trust to the configured `github_org`. The `github-actions` service account receives `workloadIdentityUser` and `serviceAccountTokenCreator` bindings. At deploy time, `google-github-actions/auth` exchanges the GitHub OIDC token for a short-lived GCP access token. This eliminates a major breach vector: stolen service account keys in repositories.

### Q19. What are the three onboarding paths and how do they differ?

Three paths converge on identical service-repo artifacts but use separate local config files:

| Path | Entry point | Config file |
|------|-------------|-------------|
| **CLI** | `shop config init` → `shop new` → `shop publish` | `.goldenpath-cli.local.json` |
| **Wizard** | `./scripts/goldenpath-setup.sh` (auto backend) | `.goldenpath-setup.local.json` |
| **MCP** | Claude + goldenpath MCP server (stdio or hosted) | MCP client config |

Do not mix CLI and wizard config files. The wizard offers four backends (bash, Python, PowerShell, Streamlit) sharing the same 15-option menu. MCP adds AI-assisted scaffolding, validation, deploy status, and official skills served from pinned releases.

### Q20. What does the `shop` CLI do?

The `shop` bash CLI in `cli/shop` provides: `shop list` (template catalog), `shop config init` (local CLI defaults), `shop new <name> --template <t> --output <dir>` (scaffold from templates with `{{TOKEN}}` replacement), `shop publish <path>` (create GitHub repo, grant WIF trust via `wif-trust-repo.sh`, verify deployment), `shop verify` (post-deploy health check), and `shop doctor` (environment diagnostics). The documented developer loop is: `config init` → `new` → `publish`.

### Q21. What is the MCP server and what tools does it expose?

The MCP server (`mcp/goldenpath_mcp/`, Python FastMCP) is the AI gateway for Golden Path. It exposes **13 tools** and **3 resources**. Read tools include `list_templates`, `list_skills`, `get_skill`, `list_docs`, `get_doc`, `get_version`, `list_services`, `get_deploy_status`, `get_service_config`, and `get_cost_estimate`. Write tools (audited to stderr JSON) include `scaffold_service` (runs `shop new`), `validate_service_repo`, and `trigger_deploy` (requires `confirm=true`). Resources serve the virtual filesystem: `goldenpath://skills/*`, `goldenpath://docs/*`, and version metadata. MCP does not replace bootstrap, wizard teardown, or `shop publish` — those remain CLI/wizard flows.

### Q22. How does enterprise configuration work?

All org-specific values live in `config/enterprise.env` (gitignored), templated from `enterprise.env.example`. Key variables include `PARENT_PROJECT_ID`, `BILLING_ACCOUNT_ID`, `GCP_DEV_PROJECT`, `GCP_PROD_PROJECT`, `GCP_SANDBOX_PROJECT`, `GITHUB_ORG`, `PLATFORM_REPO`, `GOLDENPATH_VERSION`, `PROTECTED_PROJECTS`, and `ALLOWED_TEARDOWN_PROJECTS`. Three loaders consume this file: `scripts/lib/load-config.sh` (bash), `scripts/lib/wizard_defaults.py` (Python), and `mcp/goldenpath_mcp/enterprise.py` (MCP). Override path: `export GOLDENPATH_CONFIG=/path/to/custom.env`. No org secrets are hardcoded in committed scripts.

### Q23. What is the bootstrap process?

Bootstrap is a one-time Terraform apply in `platform/bootstrap/` that enables 11 GCP APIs per project, creates Artifact Registry repositories (dev + prod, unless `personal_test = true`), creates a `github-actions` service account per project, establishes WIF pool and provider, binds workload identity, and grants IAM roles (run.admin, AR admin, SA admin/user, secrets.admin, monitoring.editor, etc.). Enterprise path: edit `terraform.tfvars` with dev/prod project IDs and `personal_test = false`. Sandbox path: `./scripts/standup-teardown-env.sh --yes` creates an isolated project with `personal_test = true`. Bootstrap runs once; teardown scripts are sandbox-only.

### Q24. How do services pin platform versions?

Service repos reference the reusable workflow as `uses: YOUR_ORG/goldenpath/.github/workflows/deploy.yml@v0.3.7` and pin `goldenpath_version` in `infra/dev.tfvars` and `infra/prod.tfvars` (from `GOLDENPATH_VERSION` in enterprise.env). Terraform module sources use the same git tag. Platform releases bundle modules, template refs, skills, and docs under one semver tag. Services upgrade by updating the pin and running their normal deploy pipeline. Architecture documentation recommends documenting a procedure to pin `ref=<commit-sha>` in production for immutability beyond mutable git tags.

### Q25. What testing does the platform include?

Golden Path has a two-tier test pyramid. **Tier 1 — Contract tests** run on every PR via `./tests/run-all-tests.sh`, validating repo hygiene, template structure, and wizard module contracts (Pester tests in `tests/goldenpath-setup.tests.ps1`). **Tier 2 — Integration tests** run on release tags via `./tests/run-integration-tests.sh`, requiring sandbox GCP credentials for end-to-end scaffold and deploy validation. This ensures the acceptance test remains achievable across releases.

### Q26. What is the sandbox environment?

The sandbox is an optional isolated GCP project for personal or team experimentation. `scripts/standup-teardown-env.sh` creates a disposable project, runs bootstrap with `personal_test = true` (single project, no prod Artifact Registry), and enables safe iteration. `scripts/teardown-personal-test.sh` destroys bootstrap resources and optionally deletes the project — blocked for IDs in `PROTECTED_PROJECTS`. Sandbox teardown is explicitly not used on the enterprise bootstrap-once path. Documentation lives in `docs/environments/sandbox-env.md`.

### Q27. Can developers extend infrastructure beyond the base template?

Yes, following platform conventions. The `shop-terraform-conventions` skill documents how to extend service infrastructure safely: call shared modules from the goldenpath git tag (do not copy module source), add service-specific resources in `infra/main.tf`, and prefer new platform-owned modules in `goldenpath/modules/` if multiple services need the same extension. Off-road cases (unusual architectures, team-specific compliance) involve platform and security consultation. The paved road covers the common case; extension is supported, not discouraged.

### Q28. What happens when MCP is unavailable?

Golden Path explicitly requires production deploys to work when MCP is down. Fallbacks are documented: scaffold via `shop new` CLI or wizard, deploy via push to `main` → GitHub Actions (unchanged), docs via static mirror or GitHub, status via GitHub Actions UI or `gcloud`, help via support channel. MCP is the preferred experience for skills, docs, and orchestration — not a hard dependency for production. This is a core design rule: MCP = front door, CI = deploy engine.

---

## Security & Compliance Questions

### Q29. How does Golden Path handle secrets?

Secrets never belong in git. The `modules/secrets/` Terraform module provisions Secret Manager secrets with accessor IAM bindings tied to the per-service runtime service account from `module.identity`. Application code references secret names in Cloud Run environment configuration; values are injected at runtime. The platform guide and skills explicitly prohibit committing secrets to repositories, putting them in `.env` files tracked by git, or sharing them in chat. Rotation procedures are documented in skills and runbooks served via MCP.

### Q30. Are long-lived service account keys used anywhere?

No. Golden Path's reference architecture mandates keyless CI authentication via Workload Identity Federation. Bootstrap Terraform in `wif.tf` establishes the OIDC trust chain between GitHub Actions and GCP. The `github-actions` service account authenticates through short-lived token exchange at pipeline runtime. The problem statement cites "no long-lived service account keys" as a core design mandate. This eliminates a common breach vector where keys are committed to repositories or stored in CI secrets indefinitely.

### Q31. What IAM model do services run under?

Each service gets a dedicated runtime service account via `module.service-identity`, granted only the permissions needed for its role — not broad project admin. The Cloud Run module configures invoker IAM (public invoker by default in dev; production guardrails are an open decision with a recommended `precondition` block). The `github-actions` service account used by CI receives elevated roles for deployment (run.admin, AR admin, secrets.admin, etc.) but operates only within the CI pipeline context. Least-privilege is the default posture for runtime; deployment accounts are scoped to automation.

### Q32. How is MCP access controlled?

MCP security follows layered rules. **Local stdio mode** relies on the caller's OS credentials — no API key gate. **Hosted mode** (SSE or streamable-http on Cloud Run) enforces `MCP_API_KEY` via `auth.py` middleware. MCP never exceeds the caller's GCP or GitHub permissions — tools shell out to `gcloud` and `gh` under the caller's identity. Write tools (`scaffold_service`, `trigger_deploy`) emit JSON audit logs to stderr before executing. `trigger_deploy` requires explicit `confirm=true`. Official skills and docs are read-only resources; admin-only merges via GitHub branch protection.

### Q33. What audit trail exists for automated actions?

The MCP server's `audit.py` module writes structured JSON audit events to stderr for write operations — specifically `scaffold_service` and `trigger_deploy`. In hosted deployments, these appear in Cloud Run logs. Architecture documentation recommends creating log-based metrics on `jsonPayload.event` for platform team visibility. GitHub Actions provides its own audit trail for workflow runs. Terraform state changes are versioned in git through the normal PR process. A consolidated audit dashboard is identified as a future improvement.

### Q34. How does Golden Path protect production environments?

Production deploys use `infra/prod.tfvars` with the same module composition as dev but environment-specific values. The deploy workflow supports gated promotion — manual approval or release tag before prod apply. Architecture documentation recommends adding a Terraform `precondition` in `cloud-run/main.tf` asserting production services cannot be publicly invokable without explicit override. `PROTECTED_PROJECTS` in enterprise.env prevents accidental sandbox teardown scripts from deleting production projects. Human judgment on production changes remains explicit — Golden Path assists, it does not replace approval workflows.

### Q35. What data residency and sovereignty considerations apply?

Golden Path deploys to GCP regions configured in `config/enterprise.env` (e.g., `GCP_REGION`). Cloud Run services, Artifact Registry, Secret Manager, and monitoring resources are created in the specified region. The platform does not impose a specific region — the enterprise chooses during configuration. Data residency compliance is achieved through regional deployment choices and GCP's regional service boundaries, not through Golden Path-specific abstractions. Off-road compliance requirements beyond the baseline require security review and custom infrastructure.

### Q36. How does the platform handle vulnerability in dependencies?

Service templates include dependency manifests (`package.json`, `requirements.txt`) with standard lockfile practices. The deploy pipeline runs lint and test steps before build. Container images are built in CI with immutable tags pushed to Artifact Registry. Golden Path does not include a built-in dependency scanning gate in v0.3.7 — that would be an organizational addition to the reusable workflow or a separate security pipeline. The paved road provides the hook point (CI workflow) where scanning tools can be inserted consistently across all services.

### Q37. What compliance frameworks does Golden Path align with?

Golden Path aligns with common cloud security practices: infrastructure-as-code (auditability), least-privilege IAM, secrets in dedicated vaults, keyless authentication, structured logging, monitoring dashboards, and alert policies. It does not certify compliance with specific frameworks (SOC 2, HIPAA, PCI-DSS) out of the box. Instead, it provides a consistent baseline that reduces the scope of per-service compliance work. Teams with framework-specific requirements go off-road with security review, extending modules or adding controls while reusing the paved road where possible.

### Q38. Who can change official platform content?

Official platform content — modules, templates, workflows, skills, docs — is maintained by the platform team through GitHub pull requests with branch protection and team reviews. MCP serves read-only resources from pinned git releases; developers cannot silently fork official skills. Service repos own their application code and service-specific `infra/` extensions but call shared modules from the goldenpath git tag. CODEOWNERS configuration (when enabled) enforces review requirements. This governance model prevents drift between what AI agents read and what CI deploys.

### Q39. What happens if a service account is compromised?

With WIF-based keyless auth, there are no long-lived keys to steal from repositories. A compromised `github-actions` service account would require compromising the GitHub OIDC trust chain or the GCP IAM bindings — both auditable and revocable through Terraform. Runtime service accounts are per-service with limited permissions. Incident response follows standard GCP IAM revocation: remove bindings, rotate secrets in Secret Manager, redeploy. The consistent service layout means platform and SRE teams can respond using known patterns rather than discovering bespoke configurations under pressure.

### Q40. How are teardown and destruction operations safeguarded?

`PROTECTED_PROJECTS` in enterprise.env lists project IDs that teardown scripts must never delete — typically the billing parent and production projects. `ALLOWED_TEARDOWN_PROJECTS` optionally restricts deletion to an explicit allowlist. `scripts/teardown-personal-test.sh` checks these lists before `--delete-project`. Teardown is documented as sandbox-only (`personal_test = true`); enterprise bootstrap is "apply once, rarely tear down." These guards prevent accidental destruction of organizational infrastructure during experimentation.

---

## Developer Experience Questions

### Q41. How long does it take a new developer to ship their first service?

Golden Path targets under 15 minutes to first scaffold and under one business day to first successful `dev` deploy for a new developer. The stretch goal is under one hour for experienced users repeating the flow. The acceptance test — zero manual steps after scaffold — is designed so that once the platform is bootstrapped and the developer picks a path (CLI, wizard, or MCP), the remaining work is writing application code and pushing to `main`. Fresh-laptop onboarding via MCP is the Phase 2 exit criterion: connect MCP once, scaffold, push, verify.

### Q42. What does a developer actually edit day-to-day?

After scaffolding, developers primarily edit application code in `src/` (or equivalent per template). Occasionally they extend `infra/main.tf` for service-specific resources following the `shop-terraform-conventions` skill. They do not write GitHub Actions workflows from scratch, create Cloud Run services in the console, or design IAM policies for basic services. The service repo README documents service-specific notes. Platform maintains shared modules, workflows, and templates.

### Q43. What if a developer doesn't want to use AI/MCP?

MCP is recommended but not required. The CLI path (`shop config init` → `shop new` → `shop publish`) and wizard path (`./scripts/goldenpath-setup.sh`) produce identical service repos. Docs are available in `docs/getting-started/` and via GitHub. Deploy happens through push to `main` regardless of onboarding path. Golden Path's design rule ensures CI-independent deploys. Developers who prefer terminal workflows have full parity with AI-assisted workflows for scaffolding and deployment.

### Q44. What wizard options exist and when should I use each?

Four wizard backends share the same 15-option menu and `.goldenpath-setup.local.json` config:

| Backend | Command | Best for |
|---------|---------|----------|
| Auto | `./scripts/goldenpath-setup.sh` | Default — uses PowerShell if available, else bash |
| Bash | `./scripts/goldenpath-setup-bash.sh` | macOS/Linux without PowerShell |
| Python | `./scripts/goldenpath-setup-py.sh` | Python-preferred environments |
| PowerShell | `./scripts/goldenpath-setup-ps.sh` | Windows or PowerShell shops |
| Streamlit | `./scripts/goldenpath-setup-ui.sh` | Browser-based UI preference |

Use the wizard when you want guided menus for bootstrap, scaffold, publish, WIF trust, deploy verification, and teardown — especially for first-time setup or private GitHub repo creation (wizard menu option 7 supports private repos; `shop publish` creates public repos by default).

### Q45. How do official skills stay current?

Six official skills live in `skills/` and are served read-only via MCP at `goldenpath://skills/{name}/SKILL.md`. They are authored in GitHub, released with platform version tags, and pinned on the MCP server's stable channel. Developers do not copy skills to laptops or edit them locally. When the platform team releases a new version, updating the MCP channel pointer or `GOLDENPATH_VERSION` brings current guidance automatically. This solves the distribution problem: no wiki drift, no per-developer skill edits, no version skew.

### Q46. What does the service repo look like after scaffolding?

```
my-service/
├── src/                    # Application code
├── Dockerfile              # Container build
├── infra/
│   ├── main.tf             # Calls shared Golden Path modules
│   ├── dev.tfvars
│   └── prod.tfvars
├── .github/workflows/
│   └── deploy.yml          # Calls shared Golden Path workflow
└── README.md
```

Every Golden Path service follows this recognizable layout. SRE and security reviewers know exactly where to look. The `_shared/` template directory provides common infra and workflow snippets token-replaced during scaffold.

### Q47. How do developers check deploy status?

Multiple options: MCP tool `get_deploy_status(service, environment, project)`, GitHub Actions workflow run UI in the service repo, `gcloud run services describe` in terminal, GCP Cloud Run console, or `shop verify` post-deploy. The `deploy-to-shop-gcp` skill documents troubleshooting failed deploys. Standard observability dashboards from `module.observability` provide runtime health signals. The paved road ensures every service has the same status-checking surfaces.

### Q48. Can I use a framework not in the six templates?

Yes — go half-paved-road. Reuse shared Terraform modules and the reusable `deploy.yml` workflow with your own Dockerfile and application code. This is the documented off-road pattern for frameworks not yet templated. Alternatively, request a new template from the platform team if multiple services will use the same framework. The platform is framework-agnostic at the infrastructure layer; only the app scaffold and Dockerfile change per template.

### Q49. What is the daily development loop?

```
branch → code → PR → review → merge to main → CI → dev deploy → verify
```

Promotion to production: verify in dev → approve prod gate in CI (or create release tag) → prod deploy → smoke check. Secrets go in Secret Manager, never in git. Logs and metrics are in standard Cloud Logging and Monitoring dashboards. This loop is identical across all Golden Path services, which is the consistency benefit for tech leads and rotating team members.

### Q50. How do I get help when something goes wrong?

Escalation paths: check GitHub Actions pipeline logs for the service repo, use MCP `get_deploy_status` or the `deploy-to-shop-gcp` skill for troubleshooting guidance, consult runbooks at `goldenpath://docs/` via MCP, run `shop doctor` for environment diagnostics, or contact the platform support channel (e.g., `#golden-path`). Because every service follows the same layout, platform and SRE teams can assist without learning bespoke configurations.

### Q51. What is the difference between `shop publish` and wizard publish?

`shop publish` creates a **public** GitHub repository, grants WIF trust via `scripts/lib/wif-trust-repo.sh`, and fails if post-deploy health checks fail. The wizard publish path (menu option 7) supports **private** repository creation. Both paths converge on the same service-repo structure and deploy workflow. Choose based on repository visibility requirements. Neither path is MCP-exclusive — both are CLI/wizard flows.

### Q52. Do CLI and wizard configs conflict?

Yes, if mixed. CLI uses `.goldenpath-cli.local.json`; wizard uses `.goldenpath-setup.local.json`. The getting-started guide (`docs/getting-started/02-pick-your-path.md`) explicitly says: pick one path, do not mix config files. Both read defaults from `config/enterprise.env`, but local state is separate. This supports different preferences without forking the paved road.

---

## Challenges & Future Questions

### Q53. What are the known risks and mitigations?

The platform guide documents six risks. **Low adoption:** co-design with pilot, measure time-to-deploy honestly. **Template/module/skill drift:** single release tag, platform owner for sync. **MCP security gap:** no privilege escalation, read-only first, audit writes. **Over-engineering:** docs via MCP first, defer Backstage portal. **MCP downtime:** CI-independent deploys, static doc mirror, CLI fallback. **Client Resource support gaps:** `get_skill`/`get_doc` helper tools. Architecture documentation adds: local Terraform state risk (recommend GCS remote backend), mutable git tags (recommend commit-sha pinning for prod), and MCP API key rotation automation.

### Q54. What decisions are still open?

Several Phase 0 decisions remain open per the platform guide: compute runtime alternatives (Cloud Run assumed vs Firebase App Hosting vs GKE), IaC tool choice (Terraform assumed vs Pulumi), CI/CD platform (GitHub Actions assumed vs Cloud Build), database defaults (Cloud SQL vs Firestore vs per-service), environment topology (dev/prod vs staging, shared vs per-team projects), and off-road support policy boundaries. Resolved decisions include MCP hosting (internal hosted + SSO), skill distribution (MCP resources from pinned git), developer portal (MCP docs first, Backstage deferred), and template delivery (MCP + CLI + GitHub template).

### Q55. What improvements are recommended in the architecture review?

Five recommendations from `docs/platform/architecture.md`: (1) Add Terraform remote state backend in GCS — high priority, prevents concurrent bootstrap corruption. (2) Pin module git references to commit SHA in production — prevents silent changes from mutable tags. (3) Automate MCP API key rotation and Secret Manager binding for hosted MCP — medium priority. (4) Surface audit log with log-based metrics and alerting for write tools. (5) Add prod tfvars validation gate preventing `allow_unauthenticated = true` in production without explicit override.

### Q56. Will there be more templates and a service catalog?

Yes, incrementally. Phase 3 includes optional extra templates beyond the current six. The multi-template model is documented: new frameworks plug into the same modules and workflow. MCP `list_templates` already catalogs available scaffolds. A service catalog portal is deferred (MCP `list_services` provides programmatic catalog today). Adoption metrics and optional portal are Layer C deliverables for scaled rollout.

### Q57. How does Golden Path relate to internal developer portals like Backstage?

Golden Path defers Backstage or similar portals. Documentation and discoverability are delivered primarily through MCP resources, with an optional static mirror for browsers. The rationale: avoid over-engineering before proving adoption. MCP serves getting-started docs, quickstart, runbooks, and skills from pinned releases. If adoption scales and a portal becomes necessary, Golden Path's consistent service metadata (labels, standard layout) makes catalog integration straightforward — but it is not a v0.3.7 deliverable.

### Q58. Can Golden Path support databases and messaging?

Not in the base template. The reference architecture lists Cloud SQL, Firestore, or none as opt-in modules — not required in the base scaffold. Pub/Sub and other GCP services can be added following `shop-terraform-conventions` (service-specific `infra/main.tf` extensions) or through new platform-owned modules if multiple services need them. Database defaults are an open decision. The paved road covers the common case of a stateless containerized web service or API; stateful and messaging patterns are extension points.

### Q59. What is the long-term vision for AI on the platform?

Golden Path treats AI as a first-class onboarding and operations interface, not a gimmick. The MCP server centralizes official skills, docs, and platform tools so Claude and similar agents produce on-pattern code and routine platform operations. Write tools are guarded and audited. The evolution proposal documents the shift from local/marketplace skills to MCP resources from pinned git. Future phases may expand tool coverage, improve audit dashboards, and add cost optimization recommendations — always under the rule that CI deploys work when MCP is down.

### Q60. How do we handle breaking platform changes?

Platform releases follow semver with git tags (e.g., `v0.3.7`). Breaking changes include migration notes and communications. Service repos pin `goldenpath_version` and upgrade on their own schedule by updating the pin in tfvars and workflow references. The platform team maintains a release train bundling modules, template refs, skills, and docs. MCP `stable` channel pointer is updated only by platform admins. This decoupled upgrade model lets conservative teams stay on older versions while pilot teams adopt beta.

---

## Preparation Tips

### Before the meeting

1. **Know your audience.** Lead with business outcomes for executives, architecture diagrams for technical leads, IAM and WIF for security, and the acceptance test for developers.
2. **Prepare the one-liner.** "Golden Path is our paved road — scaffold a service, push code, land on Cloud Run in dev with security and monitoring already done."
3. **Have the acceptance test ready.** "Scaffold → deploy to dev with zero manual edits" is the single criterion that proves the platform works.
4. **Distribute materials.** Send the formal briefing document before the meeting; use the business presentation deck for non-technical rooms.
5. **Line up a pilot story.** Real or planned: team name, service name, timeline, expected time savings.

### During the presentation

1. **Use the end-to-end flow diagram** as the anchor slide — most people remember the story left to right.
2. **Emphasize opt-in** early to reduce resistance from legacy service owners.
3. **Separate platform from application** when confusion arises — `goldenpath` is the factory; service repos are the products.
4. **Acknowledge open decisions honestly** — database defaults, environment topology, and off-road policy are not finalized.
5. **Demo if possible.** Five-minute wizard or CLI scaffold is more convincing than slides alone.

### Handling difficult questions

| Question type | Strategy |
|---------------|----------|
| "Why not just use [vendor tool]?" | Golden Path is GCP-native, version-controlled, and owned by us — no vendor lock-in on the platform layer |
| "What about legacy?" | Opt-in, no forced migration; off-road with platform consultation |
| "Is AI a security risk?" | MCP never exceeds caller permissions; write tools are audited; CI deploys independently |
| "How much does it cost?" | Platform team capacity + GCP usage; savings from eliminated per-service setup |
| "When can we start?" | After enterprise.env configuration and bootstrap — sandbox path available immediately for pilots |

### After the meeting

1. Send follow-up with links to `docs/getting-started/01-start-here.md` and the formal briefing document.
2. Confirm pilot team and success metrics with engineering leadership.
3. Schedule platform bootstrap if not yet done.
4. Log unanswered questions and update this document.

---

## Why This Document Is a Gold Mine

This Q&A Gold Mine is valuable because it anticipates the full spectrum of questions Golden Path will face across its adoption lifecycle — from the boardroom to the terminal.

**Breadth across audiences.** Sixty questions span executives (ROI, rollout, mandatory adoption), engineers (architecture, modules, pipelines, templates), security reviewers (WIF, secrets, IAM, audit), and developers (daily workflow, wizard vs CLI, skills, troubleshooting). A presenter can prepare for a mixed room without guessing what each stakeholder will ask.

**Specificity to Golden Path v0.3.7.** Answers reference real artifacts — `config/enterprise.env`, `shop new`, `deploy.yml@v0.3.7`, six templates, 13 MCP tools, four wizard backends, `PROTECTED_PROJECTS`, the acceptance test — not generic platform engineering platitudes. This builds credibility with technical audiences who will probe for substance.

**Honest about gaps.** Open decisions, architecture recommendations, off-road policy, and MCP fallback paths are addressed directly. Stakeholders trust presenters who acknowledge what is not yet decided instead of overselling completeness.

**Reusable across formats.** Each Q&A is 100–300 words — suitable for verbal responses, email follow-ups, FAQ pages, internal wikis, or AI assistant grounding. The preparation tips section converts Q&A knowledge into meeting execution.

**Living document.** As Golden Path evolves beyond v0.3.7 — new templates, remote state backend, audit dashboards, production gates — this document should be updated with each release. The categorized structure makes additions straightforward.

**Competitive advantage in presentations.** Most platform pitches fail in Q&A because presenters lack depth. This document ensures confident, accurate responses that demonstrate the platform team has thought through business, technical, security, and developer concerns — turning skepticism into sponsorship.

---

© 2026 Varanabox. All rights reserved.
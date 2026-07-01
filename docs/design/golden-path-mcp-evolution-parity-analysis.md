# Golden Path MCP Evolution — Parity Analysis

**Source document:** [golden-path-mcp-evolution-proposal.md](./golden-path-mcp-evolution-proposal.md) (stakeholder proposal, 2026-06-15)  
**Compared against:** `goldenpath` repository **v0.3.7** (as of 2026-06-24)  
**Audience:** Executives, product owners, engineers, security — all levels  
**Companion documents:** [Coverage check](./golden-path-mcp-evolution-coverage-check.md) · [Gap analysis](./golden-path-mcp-evolution-gap-analysis.md) · [Architecture](./golden-path-mcp-evolution-architecture.md)

---

## How to read this document

This document answers: **“How closely does the project match the proposal’s shape and intent?”**

Parity is not the same as coverage. Two systems can cover the same requirements but **differ in how** they deliver them. This analysis compares **distribution model**, **developer experience**, **surface area**, and **governance** side by side.

| If you are… | Start here |
|-------------|------------|
| **Executive / sponsor** | Parity verdict → Distribution model → Fresh-laptop journey |
| **Product / program manager** | Distribution model → Phase parity → Naming/branding deltas |
| **Engineer / architect** | MCP surface area → Architecture parity → Implementation deltas |
| **Security / compliance** | Auth parity → Write-tool parity → Governance parity |
| **New to Golden Path** | Plain-English summary → Fresh-laptop journey |

**Parity symbols**

| Symbol | Meaning |
|--------|---------|
| ✅ | **Full parity** — same intent and delivery |
| ⚠️ | **Partial parity** — same intent, different delivery |
| ❌ | **No parity** — proposal intent not reflected |
| ➕ | **Exceeds** — project goes beyond proposal |

---

## Parity verdict

| Dimension | Parity | Summary |
|-----------|--------|---------|
| **Strategic intent** | ✅ **High** | One MCP front door; Layer A unchanged — aligned |
| **Distribution model** | ⚠️ **Medium** | One server yes; SSO and dynamic channels differ |
| **Developer experience** | ⚠️ **Medium** | MCP journey works; publish step breaks “one integration” |
| **MCP surface area** | ➕ **Exceeds** | More tools, templates, and skills than proposed |
| **Governance** | ⚠️ **Medium** | Read-only resources yes; channel enforcement partial |
| **Branding / naming** | ⚠️ **Medium** | `goldenpath` enterprise model; legacy `shop-*` names remain |

**Overall parity with proposal intent:** **~82%** — same vision, different polish on enterprise operations.

---

## Plain-English summary

Think of the proposal as a blueprint for a **single front desk** at a factory. Everyone should get the same instruction manual from that desk, and the desk can also check order status or start a new order.

The project built the front desk and the factory line. Parity is high on **what the desk does** (skills, docs, status, scaffold). Parity is lower on **how people log in** (API key vs corporate SSO) and **how the manual updates** (baked into the Docker image vs live git pull per channel).

The project also built **more than the blueprint asked for**: six app templates instead of one family, helper tools for weak MCP clients, and four wizard interfaces as fallbacks.

---

## Distribution model — side by side

| Dimension | Proposal (2026-06-15) | Project (v0.3.7) | Parity |
|-----------|----------------------|------------------|--------|
| **Primary integration** | 1 (MCP) + optional CLI | MCP + **CLI + wizard** (3 paths) | ⚠️ Broader than “one path” wording |
| **Knowledge delivery** | MCP Resources from pinned git | MCP Resources from repo root / Docker COPY | ⚠️ Same UX, different backend |
| **Action delivery** | MCP Tools (phased v1→v2) | 13 tools (v1+v2 together) | ➕ Exceeds |
| **Docs delivery** | MCP Resources + optional static mirror | MCP Resources only | ⚠️ |
| **Skill delivery** | No local canonical copies | MCP-only distribution documented | ✅ |
| **Hosted transport** | HTTPS internal MCP | Cloud Run `streamable-http` + SSE | ✅ |
| **Hosted auth** | SSO/OIDC | `MCP_API_KEY` Bearer/header | ⚠️ |
| **Version example** | Tag e.g. `v1.4.0` | Tag **`v0.3.7`** | ✅ (different number, same model) |
| **Release channels** | `stable`, `beta`, `main` (internal) | Env vars + Dockerfile default | ⚠️ Metadata yes; hot-swap partial |
| **Branding** | “Shop” in diagrams | Enterprise-agnostic `goldenpath` | ➕ Evolution beyond proposal |
| **Critical path** | GitHub Actions → GCP | Same — `workflow_call` deploy | ✅ |
| **MCP gates deploy?** | No | No | ✅ |

### What “partial parity” means here

**Integration count:** The proposal’s marketing line is “one MCP connection.” The project delivers that for **learning and scaffolding**, but **publishing** (GitHub repo creation, WIF trust, first push) still requires `shop publish` or wizard menu 7. That is intentional — publish was never in the proposal’s MCP tool list — but it weakens the “one integration” story for onboarding.

**Content backend:** The proposal imagines the hosted server **reading a pinned git ref at runtime**. The project **copies** `skills/`, `docs/`, and `templates/` into the Docker image at build time (`mcp/Dockerfile`). Developers get the same read-only experience; platform teams must **redeploy** to change content, not flip a channel pointer.

---

## Developer experience — fresh laptop journey

| Step | Proposal | Project (v0.3.7) | Parity |
|------|----------|------------------|--------|
| 1 | Add MCP URL + SSO to client | MCP config + API key (hosted) or stdio (local) | ⚠️ |
| 2 | Docs served as MCP Resources | `get_doc` / `goldenpath://docs/*` | ✅ |
| 3 | MCP already configured for deploy/status | Same server | ✅ |
| 4 | Ask Claude; skill from MCP; `scaffold_service` | `scaffold_service` runs `cli/shop new` | ✅ |
| 5 | Push code; CI deploys | Requires **`shop publish`** or wizard first | ⚠️ |
| 6 | (implied) Check status via MCP | `get_deploy_status`, `list_services` | ✅ |
| 7 | (optional) Prod via MCP | `trigger_deploy(confirm=true)` | ✅ |

### Journey diagram — proposal vs project

**Proposal (5 steps)**

```
Connect MCP → Read docs → Scaffold → Push → Live
```

**Project (7 steps)**

```
Bootstrap GCP → Connect MCP → Read docs → Scaffold → Publish (CLI/wizard) → Push → Live
         ↑                              ↑
    not in proposal              not an MCP tool
```

The extra steps are **documented honestly** in `docs/getting-started/08-journey-mcp.md` and `mcp/guide.md`. Parity gap is in **messaging**, not hidden behavior.

---

## MCP surface area — side by side

### Resources

| URI pattern | Proposal | Shipped | Parity |
|-------------|----------|---------|--------|
| `goldenpath://skills/{name}/SKILL.md` | Yes | Yes | ✅ |
| `goldenpath://skills/{name}/*` | Bundled assets | SKILL.md only | ⚠️ |
| `goldenpath://docs/{path}` | Yes | Yes + aliases | ➕ |
| `goldenpath://meta/version` | Yes | Yes | ✅ |

**Count:** Proposal describes 4 URI patterns; project registers **3** resource templates (path params expand to many URIs).

### Tools

| Category | Proposed | Shipped | Parity |
|----------|----------|---------|--------|
| **v1 read tools** | 4 | 4 | ✅ |
| **v2 write tools** | 4 (`validate_service`) | 4 (`validate_service_repo`) | ✅ |
| **Helper tools** | 2 optional (`list_skills`, `get_skill`) | 5 (`+ list_docs`, `get_doc`, `get_version`) | ➕ |
| **Total tools** | 8–10 | **13** | ➕ |

### Skills and templates

| Asset | Proposal examples | Project | Parity |
|-------|-------------------|---------|--------|
| **Skills** | 5 (`scaffold-service`, `deploy-to-shop-gcp`, …) | **6** (`scaffold-shop-service`, …) | ➕ (rename delta) |
| **Templates** | `nextjs` + future | **6** (`nextjs`, `fastapi`, `streamlit`, `express`, `react-spa`, `svelte-spa`) | ➕ |

---

## Architecture parity

| Layer | Proposal | Project | Parity |
|-------|----------|---------|--------|
| **Source of truth** | GitHub `goldenpath` repo | Same | ✅ |
| **MCP runtime** | Hosted internal server | Cloud Run + local stdio | ✅ |
| **MCP packaging** | Not specified | `mcp/Dockerfile`, `mcp/infra/` Terraform | ➕ |
| **MCP deploy CI** | Not specified | `.github/workflows/deploy-mcp.yml` | ➕ |
| **Content loader** | Pinned git ref | `ContentStore` reads `GOLDENPATH_ROOT` | ⚠️ |
| **Auth middleware** | SSO/OIDC | `auth.py` API key gate | ⚠️ |
| **Audit** | Audit on writes | `audit.py` → stderr JSON | ✅ |
| **GCP reads** | Caller credentials | `gcp_adc.py` / caller ADC | ✅ |
| **GitHub writes** | Caller token | `github_ops.py` + `confirm=true` | ✅ |

### Hosted MCP deployment parity

The proposal resolves §9 decision 6 as “hosted internal MCP, HTTPS, SSO.” The project ships:

- **Cloud Run** service via `mcp/infra/` (Terraform reuses platform modules)
- **`streamable-http`** transport (also SSE-capable in code)
- **`MCP_API_KEY`** in Secret Manager, enforced by middleware
- **Health endpoint** at `/health` (unauthenticated probe)
- **Auto-redeploy** on changes to `mcp/`, `skills/`, `docs/`, `templates/catalog.json`

SSO is the main architectural delta: the project expects **corporate IdP in front of Cloud Run** (documented as future/org pattern), not first-class OIDC in `goldenpath_mcp`.

---

## Governance and consistency parity

| Concern | Proposal | Project | Parity |
|---------|----------|---------|--------|
| **Who changes guidance** | Platform admins via GitHub PR | Same — skills/docs in repo | ✅ |
| **Developer editability** | Read-only via MCP | MCP Resources; local clone for stdio dev | ⚠️ |
| **Version pinning** | Enforced channels | `GOLDENPATH_VERSION` in Dockerfile + env | ⚠️ |
| **Skill ↔ template alignment** | Same release tag | Single repo tag bundles all | ✅ |
| **Cross-client consistency** | Same resources for all MCP clients | Same `ContentStore` | ✅ |
| **Write tool gating** | Phased; audit on writes | All write tools shipped; audit on 2 | ➕ |
| **No privilege escalation** | MCP ≤ caller permissions | Uses caller `gcloud`/`gh` | ✅ |

---

## Goals and non-goals parity

| Item | Proposal | Project | Parity |
|------|----------|---------|--------|
| Time-to-first-deploy < 1 day | Goal | Documented target; not measured | ⚠️ |
| Secure, observable default | Goal | Modules + templates | ✅ |
| Standardized services | Goal | Templates + `validate_service_repo` | ✅ |
| Stronger AI-assisted DX | Evolved plan benefit | MCP + 6 skills | ✅ |
| No forced migration | Non-goal | Documented opt-in | ✅ |
| Common case only | Non-goal | 6 templates; off-road in docs | ✅ |
| Humans own production | Non-goal | `confirm=true`, CI gates | ✅ |
| Backstage deferred | Decision | No Backstage | ✅ |

---

## Naming and branding parity

The proposal diagrams use **Shop** naming (`scaffold-service`, `deploy-to-shop-gcp`). The project uses **enterprise-agnostic** naming in repo structure (`goldenpath`, `GOLDENPATH_VERSION`) while retaining legacy identifiers:

| Proposal name | Project name | Parity |
|---------------|--------------|--------|
| `scaffold-service` | `scaffold-shop-service` | ⚠️ |
| `goldenpath` (repo) | `goldenpath` | ✅ |
| `v1.4.0` (example tag) | `v0.3.7` | ✅ (versioning model, not number) |
| `shop new` CLI | `cli/shop` | ⚠️ Legacy CLI name |

This does not block function — MCP URIs use folder names — but **diagrams and stakeholder decks** should use actual skill folder names to avoid confusion.

---

## Fallback parity

| Need | Proposal fallback | Project fallback | Parity |
|------|-------------------|------------------|--------|
| Scaffold | GitHub template / `shop new` | `cli/shop`, wizard menu 5 | ✅ |
| Deploy | Push → GHA | Service repo workflows | ✅ |
| Docs | Static mirror | MCP + git clone only | ⚠️ |
| Status | GCP console / `gcloud` | MCP tools + CLI | ✅ |
| Bootstrap | (implicit CLI) | standup script + 4 wizard backends | ➕ |

---

## Phase parity

| Phase | Proposal focus | Project state | Parity |
|-------|----------------|---------------|--------|
| **0 — Align** | Close §6, §7; MCP-centric distribution | Docs updated; MCP guide shipped | ⚠️ Pilot not in repo |
| **1 — Paved road** | Layer A unchanged | Modules, templates, CI shipped | ✅ |
| **2 — AI DX** | Unified MCP Resources + tools | MCP server shipped; publish gap | ⚠️ |
| **3 — Scale** | Metrics; portal if needed | Not started | ❌ |

**Exit criteria parity**

| Criterion | Proposal | Project | Parity |
|-----------|----------|---------|--------|
| Phase 1: zero manual edits to dev | Required | Tier 2 integration path exists | ⚠️ |
| Phase 2: MCP-only laptop | Required | Scaffold via MCP; publish external | ⚠️ |
| Phase 3: adoption trending | Required | No instrumentation | ❌ |

---

## Where parity exceeds the proposal

| # | Delta | Why it strengthens parity with *spirit* if not *letter* |
|---|-------|----------------------------------------------------------|
| P1 | 6 templates | More “common cases” without separate off-road work |
| P2 | 13 tools in one release | Faster time-to-value for AI-assisted DX |
| P3 | Hosted MCP + Terraform | Proposal described model; project is deployable |
| P4 | Helper tools for weak clients | Directly addresses proposal risk §269 |
| P5 | `enterprise.env` | Multi-org without forking the platform |
| P6 | Test pyramid (Tier 1 + 2) | Proves paved road mechanically, not just on paper |
| P7 | DOC_ALIASES | Stable URIs across doc renames — better than proposal assumed |

---

## Where parity diverges (summary)

These are the **material differences** between proposal intent and project delivery. Remediation detail lives in [gap analysis](./golden-path-mcp-evolution-gap-analysis.md).

| # | Topic | Proposal | Project |
|---|-------|----------|---------|
| D1 | Hosted auth | SSO/OIDC | API key |
| D2 | Content pinning | Runtime git ref per channel | Docker COPY at build |
| D3 | Onboarding steps | 5-step MCP-centric | 7-step with bootstrap + publish |
| D4 | Docs fallback | Static mirror | MCP/git only |
| D5 | Skill asset URIs | `skills/{name}/*` | `SKILL.md` only |
| D6 | Adoption proof | Metrics | Not instrumented |

---

## Stakeholder Q&A — parity edition

| Question | Parity answer |
|----------|---------------|
| "Is this the same product the proposal described?" | **Same architecture and intent** — one MCP front door, unchanged paved road |
| "Did we simplify onboarding as promised?" | **Partially** — MCP collapses skills+docs+tools; publish/bootstrap remain separate |
| "Is hosted MCP enterprise-ready?" | **Partially** — deployed on Cloud Run; SSO is org-layer, not built-in |
| "Do we have more than the proposal?" | **Yes** — templates, tools, wizards, tests |
| "Can we claim version channels work?" | **Careful** — labels exist; content switching needs redeploy |
| "Is the factory line the same?" | **Yes** — full parity on Layer A |

---

## Glossary

| Term | Plain language | Technical meaning |
|------|----------------|-------------------|
| **Parity** | How alike two things are | Proposal shape vs project implementation |
| **Distribution** | How developers get the official manual | MCP Resources vs local copies |
| **Partial parity** | Same goal, different method | e.g. API key vs SSO |
| **Exceeds** | Project has extra capability | e.g. 6 templates vs 1 family |
| **stdio MCP** | Local AI connection | MCP over stdin/stdout on developer machine |
| **streamable-http** | Network AI connection | MCP over HTTPS on Cloud Run |

---

## Document history

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-06-24 | Initial parity analysis vs v0.3.7 (split from combined doc) |

---

© 2026 Varanabox. All rights reserved.

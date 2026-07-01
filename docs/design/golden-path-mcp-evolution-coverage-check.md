# Golden Path MCP Evolution — Coverage Check

**Source document:** [golden-path-mcp-evolution-proposal.md](./golden-path-mcp-evolution-proposal.md) (stakeholder proposal, 2026-06-15)  
**Compared against:** `goldenpath` repository **v0.3.7** (as of 2026-06-24)  
**Audience:** Executives, product owners, engineers, security — all levels  
**Companion documents:** [Parity analysis](./golden-path-mcp-evolution-parity-analysis.md) · [Gap analysis](./golden-path-mcp-evolution-gap-analysis.md) · [Architecture](./golden-path-mcp-evolution-architecture.md)

---

## How to read this document

This document answers one question: **“Does the project cover what the proposal asked for?”**

| If you are… | Start here |
|-------------|------------|
| **Executive / sponsor** | Coverage scorecard → Plain-English summary → Phase coverage |
| **Product / program manager** | Coverage scorecard → Requirement tables (A–L) → Phase coverage |
| **Engineer / architect** | Full requirement tables → Evidence column → Test coverage |
| **Security / compliance** | Rows in sections E, F, G, H, L |
| **New to Golden Path** | Plain-English summary → Glossary |

**Legend**

| Symbol | Meaning |
|--------|---------|
| ✅ | **Covered** — implemented and usable today |
| ⚠️ | **Partial** — exists but not fully as proposed |
| ❌ | **Not covered** — proposed but not implemented |
| ➕ | **Exceeds** — implemented beyond what the proposal required |
| ➖ | **N/A** — proposal explicitly unchanged or out of scope |

---

## Coverage scorecard

| Area | Coverage | One-line verdict |
|------|----------|------------------|
| **Layer A (paved road)** | ✅ **95%** | Bootstrap, 5 Terraform modules, 6 templates, reusable CI — shipped |
| **MCP Resources (skills/docs)** | ✅ **90%** | Virtual filesystem works; bundled skill assets URI partial |
| **MCP Tools (read)** | ✅ **100%** | All proposed v1 tools + helper tools shipped |
| **MCP Tools (write)** | ✅ **100%** | All proposed v2 tools + audit shipped |
| **Distribution model** | ⚠️ **70%** | One MCP server yes; dynamic pinned-ref channels partial |
| **Hosted MCP auth** | ⚠️ **50%** | API key yes; SSO/OIDC not in package |
| **Onboarding collapse** | ⚠️ **75%** | MCP + CLI + wizard (proposal emphasized MCP-only) |
| **Fallbacks** | ⚠️ **80%** | CLI/CI yes; static docs mirror not shipped |
| **Governance / channels** | ⚠️ **65%** | Metadata yes; enforced channel switching partial |
| **Phasing** | ✅ **85%** | Phase 1+2 largely complete; Phase 3 adoption metrics open |

**Overall coverage of proposal requirements:** **~82%**

The paved road and MCP surface area are largely covered. Remaining gaps are mostly **operational hardening** (SSO, channel mechanics, doc mirrors, publish-in-MCP) — not missing core infrastructure.

---

## Plain-English summary

### What the proposal asked for

The proposal does not change *what* Golden Path builds (templates, Terraform, CI/CD). It changes *how developers receive guidance*:

- **Before (original plan):** Skills on disk, docs on a separate site, MCP for actions — three channels that drift apart.
- **After (evolved plan):** One MCP server serves official skills, docs, and platform tools from a pinned GitHub release.

The factory line (GitHub Actions → GCP) stays the same. MCP is the **front desk**, not the factory.

### What the project covers today

| Proposal idea | Covered? |
|---------------|----------|
| Keep the factory line (Terraform + CI + Cloud Run) | ✅ Yes |
| One MCP server for skills + docs + tools | ✅ Yes |
| Developers should not edit official skills locally | ✅ Yes (via MCP Resources) |
| Deploy still works if MCP is down | ✅ Yes (push to GitHub) |
| One-click fresh laptop (MCP only) | ⚠️ Partial — still need CLI/wizard for `shop publish` |
| Company login (SSO) on hosted MCP | ⚠️ API key instead; SSO is org add-on |
| Automatic version channels (`stable` / `beta`) | ⚠️ Labels exist; switching content needs redeploy |

### One sentence for any audience

> **The proposal’s requirements are largely covered; remaining items are enterprise polish (SSO, doc mirrors, dynamic versioning), not a missing paved road.**

---

## Requirement coverage — section by section

Each row maps to a **specific claim** in the stakeholder proposal.

### A. Core thesis (proposal §9–21, §327)

| # | Proposal requirement | Status | Evidence in repo |
|---|---------------------|--------|------------------|
| A1 | Layer A unchanged | ✅ | `platform/bootstrap/`, `modules/`, `templates/`, `.github/workflows/deploy.yml` |
| A2 | Evolve B+C into one MCP server | ✅ | `mcp/goldenpath_mcp/server.py` — Resources + Tools |
| A3 | Skills/docs as read-only MCP Resources | ✅ | `@mcp.resource` for `goldenpath://skills/*`, `goldenpath://docs/*` |
| A4 | Platform actions as MCP Tools | ✅ | 13 tools in `server.py` |
| A5 | Same version for all MCP clients | ⚠️ | Same **if** same `GOLDENPATH_ROOT`/image; not dynamic multi-channel serve |
| A6 | CI path: GitHub Actions → GCP | ✅ | `deploy.yml` is `workflow_call` only; WIF in `platform/bootstrap/wif.tf` |
| A7 | MCP is front door, not deploy engine | ✅ | Documented in `mcp/guide.md`, `docs/platform/golden-path.md` |

### B. Problem the proposal solves (§25–45)

| # | Problem stated | Addressed? | How |
|---|----------------|------------|-----|
| B1 | Fresh laptop assembly burden | ⚠️ | MCP config + examples; publish still separate |
| B2 | Local skill edits / drift | ✅ | Resources read-only from repo; skills in `skills/` |
| B3 | Version skew between engineers | ⚠️ | Version tags + `GOLDENPATH_VERSION`; channel hot-swap partial |
| B4 | Wiki vs skill vs tool mismatch | ✅ | Single server serves docs + skills + tools |
| B5 | Tech lead can't verify path followed | ⚠️ | Standard templates help; no adoption telemetry dashboard |

### C. Layer A — unchanged artifacts (§214–224)

| # | Item | Status | Evidence |
|---|------|--------|----------|
| C1 | Terraform modules | ✅ | 5 modules: `cloud-run`, `secrets`, `service-identity`, `artifact-registry`, `observability` |
| C2 | Reusable GitHub Actions workflow | ✅ | `.github/workflows/deploy.yml` |
| C3 | Service templates | ➕ | **6** templates (`templates/catalog.json`) — proposal showed one family |
| C4 | Workload Identity Federation | ✅ | `platform/bootstrap/wif.tf`, `scripts/lib/wif-trust-repo.sh` |
| C5 | Acceptance test: zero manual edits to dev | ⚠️ | Design goal + Tier 2 integration test path; not proven for all enterprises |
| C6 | Success metrics tracking | ❌ | Goals in docs; no metrics dashboard in repo |

### D. MCP Resources (proposal §231–240)

| # | URI / capability | Status | Evidence |
|---|------------------|--------|----------|
| D1 | `goldenpath://skills/{name}/SKILL.md` | ✅ | `resource_skill()` in `server.py` |
| D2 | `goldenpath://skills/{name}/*` bundled assets | ⚠️ | Skill body only; no wildcard Resource tree |
| D3 | `goldenpath://docs/{path}` | ✅ | `resource_doc()` + `DOC_ALIASES` in `content.py` |
| D4 | `goldenpath://meta/version` | ✅ | `resource_meta_version()` |
| D5 | Helper `list_skills()` / `get_skill()` | ✅ | Shipped |
| D6 | Helper `list_docs()` / `get_doc()` | ➕ | Shipped (proposal said optional) |

**Skills inventory**

| Proposal example name | Actual skill folder | Status |
|----------------------|---------------------|--------|
| `scaffold-service` | `scaffold-shop-service` | ⚠️ Rename (Shop legacy) |
| `deploy-to-shop-gcp` | `deploy-to-shop-gcp` | ✅ |
| (5 core skills) | **6** skills (+ `test-coverage-gap-analysis`) | ➕ Extra skill |

**Docs served via MCP**

All `docs/**/*.md` files are listable via `list_docs()` and readable via `get_doc()` / `goldenpath://docs/{path}`. Legacy short names (e.g. `quickstart.md`) resolve through `DOC_ALIASES` in `content.py`.

### E. MCP Tools — phased (proposal §242–248)

| Phase | Proposed tool | Actual tool | Status |
|-------|---------------|-------------|--------|
| v1 | `list_services` | `list_services` | ✅ |
| v1 | `get_deploy_status` | `get_deploy_status` | ✅ |
| v1 | `get_service_config` | `get_service_config` | ✅ |
| v1 | `get_cost_estimate` | `get_cost_estimate` | ✅ |
| v2 | `scaffold_service` | `scaffold_service` | ✅ |
| v2 | `trigger_deploy` | `trigger_deploy` (`confirm=true`) | ✅ |
| v2 | `validate_service` | `validate_service_repo` | ✅ (renamed) |
| v2 | `list_templates` | `list_templates` | ✅ |
| — | — | `get_version`, `list_skills`, `get_skill`, `list_docs`, `get_doc` | ➕ Helpers |

**Write tool safeguards (proposal §198, §266)**

| Safeguard | Status | Evidence |
|-----------|--------|----------|
| Phased rollout read → write | ➕ | Both phases shipped together in v0.3.7 |
| Audit on writes | ✅ | `audit.py` → JSON stderr |
| `trigger_deploy` confirmation | ✅ | `confirm=true` required |
| No privilege escalation | ✅ | Uses caller `gcloud`/`gh` credentials |

**Explicitly outside MCP (correct per design)**

| Capability | Proposal / design | Status | Evidence |
|------------|-------------------|--------|----------|
| GCP bootstrap | Not MCP tool | ✅ | `standup-teardown-env.sh`, wizard |
| `shop publish` | Not in proposal MCP list | ✅ | CLI/wizard only; `mcp/guide.md` |
| Teardown | Not MCP tool | ✅ | `teardown-personal-test.sh` |

### F. Version channels (proposal §250–256)

| Channel | Proposal intent | Status | Evidence |
|---------|-----------------|--------|----------|
| `stable` | Prod engineers | ⚠️ | `GOLDENPATH_CHANNEL=stable` default; content pinned at build/clone |
| `beta` | Pilot team | ⚠️ | Env var supported; no separate beta content pipeline |
| `main` | Platform internal only | ⚠️ | Documented; not gated in code |
| Enforced pinning | MCP serves tag | ⚠️ | Hosted: `mcp/Dockerfile` bakes `GOLDENPATH_VERSION=v0.3.7` |

### G. Open decisions “resolved” by proposal (§123–131)

| §9 # | Decision | Proposal resolution | Current status |
|------|----------|---------------------|----------------|
| 6 | MCP hosting & transport | Hosted internal, HTTPS, **SSO (OIDC)** | ⚠️ Cloud Run + **API key**; SSO via org proxy (documented future) |
| 7 | Skill distribution | MCP Resources from pinned git | ⚠️ Local fs / Docker COPY — not live git pull |
| 5 | Developer portal | MCP docs first; Backstage deferred | ✅ Docs via MCP; no Backstage |
| 4 | Template delivery | MCP `scaffold_service` + GitHub template | ⚠️ MCP + `shop new`; GitHub template button not emphasized |

### H. Consistency & governance (§134–142)

| Concern | Proposal | Status | Evidence |
|---------|----------|--------|----------|
| Changes via platform admin PR only | GitHub PR | ✅ | Skills/docs in repo; branch protection assumed |
| Version pinning enforced | stable/beta channels | ⚠️ | Service repos pin `goldenpath_version`; MCP channel partial |
| Skill ↔ template alignment | Same release tag | ✅ | Single repo tag bundles all |
| Devs cannot bypass with local copies | Read-only MCP | ✅ | For MCP users; stdio reads local clone |
| Same resources all clients | Consistent | ✅ | Same `ContentStore` logic |

### I. Goals & non-goals (§144–159)

| Goal / non-goal | Status | Notes |
|-----------------|--------|-------|
| Time-to-first-deploy < 1 day | ⚠️ | **Target** in docs; no measured baseline in repo |
| Secure, observable default | ✅ | Modules + templates enforce baseline |
| Standardized legible services | ✅ | Template structure + `validate_service_repo` |
| AI-assisted DX | ✅ | MCP + 6 skills |
| No forced migration | ✅ | Documented opt-in |
| Common case only | ✅ | 6 templates; off-road documented |
| Humans own production | ✅ | `trigger_deploy` gated; prod CI gates in templates |

### J. Fallbacks (proposal §288–297)

| Need | Proposed fallback | Status | Evidence |
|------|-------------------|--------|----------|
| Scaffold | GitHub template or `shop new` | ✅ | `cli/shop`, wizards |
| Deploy | Push → GHA | ✅ | Service repo workflows |
| Docs | Static mirror (Pages / internal) | ❌ | Docs in repo + MCP only |
| Status | GCP console / `gcloud` | ✅ | MCP tools optional |

### K. Revised phasing (proposal §273–284)

| Phase | Exit criterion | Status |
|-------|----------------|--------|
| **0 — Align** | Decisions + pilot | ⚠️ | MCP distribution adopted in docs; pilot not in repo |
| **1 — Paved road** | Zero manual edits to dev | ⚠️ | Artifacts shipped; Tier 2 integration tests exist |
| **2 — AI DX** | Fresh machine MCP-only scaffold + deploy | ⚠️ | MCP scaffolds; **publish not in MCP** |
| **3 — Scale** | Metrics, optional portal | ❌ | No adoption dashboard |

### L. Risks & mitigations (proposal §260–269)

| Risk | Proposed mitigation | Status |
|------|---------------------|--------|
| Low adoption | Pilot + honest metrics | ⚠️ Process, not tooling |
| Template/skill drift | Single release tag | ✅ Single repo |
| MCP security | SSO + audit | ⚠️ API key + audit; SSO partial |
| Over-engineering | Defer Backstage | ✅ |
| MCP availability | Static mirror + CLI | ⚠️ CLI yes; mirror no |
| Client Resource gaps | Helper tools | ✅ |

---

## Test coverage of MCP requirements

Automated tests validate that covered requirements stay covered:

| Test area | File(s) | What it proves |
|-----------|---------|----------------|
| Content store / Resources | `tests/test_mcp_content.py` | Docs, skills, meta/version, path safety |
| MCP tools (write) | `tests/test_mcp_server_tools.py` | `scaffold_service`, `trigger_deploy` guards |
| MCP auth | `tests/test_mcp_auth.py` | API key middleware on hosted transports |
| MCP audit | `tests/test_mcp_audit.py` | JSON audit events on writes |
| GCP tools | `tests/test_mcp_gcp.py`, `tests/test_mcp_gcp_adc.py` | Read tool adapters |
| GitHub ops | `tests/test_mcp_github_ops.py` | `trigger_deploy` dispatch |
| Validation | `tests/test_mcp_validate.py` | `validate_service_repo` |
| Catalog | `tests/test_catalog_schema.py` | Template catalog shape |
| Integration (Tier 2) | `tests/integration/test_sandbox_deploy_spine.py` | End-to-end deploy spine (needs sandbox creds) |

---

## Phase coverage dashboard

```
Phase 0 — Align          [████████░░] 80%   docs closed; pilot not tracked in repo
Phase 1 — Paved road     [█████████░] 90%   Layer A shipped; acceptance test = integrate
Phase 2 — Unified MCP    [████████░░] 80%   MCP shipped; publish gap; SSO partial
Phase 3 — Scale          [███░░░░░░░] 30%   metrics + portal not started
```

| Phase | Proposal exit criterion | Covered? | Evidence |
|-------|-------------------------|----------|----------|
| 1 | Pilot deploys to dev, zero manual edits | ⚠️ | `tests/integration/` + manual sandbox |
| 2 | MCP-only laptop scaffold + deploy | ⚠️ | Scaffold ✅; publish via CLI/wizard |
| 3 | Adoption trending | ❌ | No dashboard |

---

## What exceeds the proposal (coverage bonus)

These items are **not required** by the proposal but are present in the project:

| # | Extra capability | Why it matters |
|---|-----------------|----------------|
| E1 | **6 templates** (not just Next.js family) | Framework coverage beyond “common case first” |
| E2 | **13 tools** (v1+v2 same release) | Faster Phase 2 delivery |
| E3 | **4 wizard backends** + Streamlit UI | Fallbacks richer than “optional CLI” |
| E4 | **`enterprise.env`** enterprise-agnostic config | Multi-org portability not in original Shop proposal |
| E5 | **Tier 1 + Tier 2 test pyramid** | Contract + live integration gates |
| E6 | **`test-coverage-gap-analysis` skill** | Platform quality meta-skill |
| E7 | **Hosted MCP on Cloud Run** + Terraform `mcp/infra/` | Deployable MCP, not just design |
| E8 | **DOC_ALIASES** | Backward-compatible doc URIs |

---

## Quick reference — “is it covered?”

| Stakeholder might ask… | Short answer |
|------------------------|--------------|
| "Did we build what the proposal described?" | **Mostly yes** — one MCP front door + unchanged paved road |
| "Can we deploy without MCP?" | **Yes** — push to GitHub |
| "Are skills centralized?" | **Yes** — via MCP Resources |
| "Is SSO done?" | **No** — API key; org adds SSO in front |
| "One integration for new hires?" | **Almost** — need CLI/wizard for publish |
| "Are we on stable/beta channels?" | **Labels yes, mechanics partial** |
| "Forced migration?" | **No** — opt-in preserved |

For **what differs** between proposal and project, see [parity analysis](./golden-path-mcp-evolution-parity-analysis.md).  
For **what is still missing**, see [gap analysis](./golden-path-mcp-evolution-gap-analysis.md).

---

## Glossary

| Term | For non-technical readers | Technical meaning |
|------|---------------------------|-----------------|
| **Layer A** | The factory line | Templates, Terraform modules, CI workflow |
| **Layer B** | The help desk + tools | MCP skills, docs, platform tools |
| **Layer C** | The welcome guide | Onboarding docs, support paths |
| **MCP** | AI assistant connector | Model Context Protocol server |
| **Resource** | Read-only official document | `goldenpath://` URI served by MCP |
| **Tool** | Action the AI can run | e.g. `get_deploy_status` |
| **Coverage** | How many proposal requirements are met | This document's main job |
| **WIF** | Keyless login for automation | Workload Identity Federation |

---

## Document history

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-06-24 | Initial coverage check vs v0.3.7 |

---

© 2026 Varanabox. All rights reserved.
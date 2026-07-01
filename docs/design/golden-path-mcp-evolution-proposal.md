# Golden Path — MCP-centric distribution proposal

**Status:** Proposal (evolution of draft requirements, 2026-06-15)  
**Audience:** Platform / DevEx, Eng leads, Security, SRE, pilot teams  
**Purpose:** Explain why distributing skills, docs, and platform actions through a single hosted MCP server is a better model than the original three-channel approach (local Skills + separate docs + MCP tools).

---

## Executive summary

The original Golden Path requirements correctly define **what** to build: paved-road artifacts (templates, Terraform, CI/CD) plus an AI-assisted layer (Skills + MCP) and discoverability (docs, onboarding).

The gap is **how developers receive and stay aligned with that guidance**. Local Skill installs and separate doc sites invite version skew and ad-hoc edits. Developers on fresh laptops must assemble the experience themselves.

**This proposal keeps Layer A unchanged** and evolves Layers B and C into **one Golden Path MCP server** that:

1. Serves **skills and docs as read-only MCP Resources** from a pinned GitHub release (admin-maintained).
2. Exposes **platform actions as MCP Tools** (scaffold, deploy, status, config, cost).
3. Gives every developer the **same version** of the path from **any MCP-capable client**, without copying files locally.

The paved road still runs through **GitHub Actions → GCP**. MCP is the **consistent front door**, not a replacement for CI or infrastructure.

---

## The problem with the original distribution model

The draft requirements describe Layer B as two separate systems:

| Component | Role in original plan |
|-----------|------------------------|
| **Agent Skills** | Knowledge — conventions, runbooks, when/how to deploy |
| **MCP server** | Actions and live data — status, scaffold, deploy |
| **Layer C docs** | Discoverability — Start here, quickstart, support |

Distribution is left open (§7: marketplace, API, Claude.ai, or all). In practice, that implies:

| Scenario | What goes wrong |
|----------|-----------------|
| Fresh laptop | Developer must find, clone, or install Skills; locate docs; configure MCP separately |
| Local Skills | Developer edits `SKILL.md` for a one-off need; change never flows back to platform |
| Version drift | Alice on skill pack v1.2, Bob on v1.2-with-local-tweaks, platform ships v1.4 |
| Multiple channels | Runbook in a Skill disagrees with the wiki; MCP tool behavior updated before docs |
| Tech lead review | Hard to know which “golden path” a team actually followed |

The original doc already flags **drift** between template, modules, and skills as a risk (§11). The root cause is **decentralized distribution** of knowledge artifacts, not the Skill format itself.

---

## The evolved model — one server, one version, one front door

### Core idea

| Principle | Implementation |
|-----------|----------------|
| **GitHub is the source of truth** | `skills/`, `docs/`, `templates/`, `modules/`, `workflows/` in the `goldenpath` repo; changes via PR; platform admins review/approve |
| **MCP is the distribution layer** | Hosted internal server reads a **pinned ref** (e.g. tag `v1.4.0` on channel `stable`) |
| **Developers consume read-only** | MCP Resources for skills/docs; no canonical local copies to edit |
| **Actions stay as tools** | `scaffold_service`, `get_deploy_status`, etc. — same as original §6.5 |
| **Critical path does not depend on MCP** | Push to `main` still triggers GitHub Actions → deploy; MCP assists, does not gate |

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  GitHub (admin-only writes)                                      │
│    goldenpath/                                               │
│      modules/     templates/     workflows/   ← Layer A        │
│      skills/      docs/                          ← Layer B + C   │
└────────────────────────────┬─────────────────────────────────────┘
                             │  pinned release (e.g. stable → v1.4.0)
┌────────────────────────────▼─────────────────────────────────────┐
│  Golden Path MCP Server (hosted, SSO)                            │
│                                                                  │
│  Resources (read-only virtual filesystem)                        │
│    goldenpath://skills/scaffold-service/SKILL.md                 │
│    goldenpath://skills/deploy-to-shop-gcp/SKILL.md               │
│    goldenpath://docs/getting-started/01-start-here.md                               │
│    goldenpath://docs/getting-started/03-quickstart.md                               │
│                                                                  │
│  Tools (live actions & data)                                     │
│    list_services, get_deploy_status, get_service_config,         │
│    get_cost_estimate, scaffold_service, trigger_deploy           │
└────────────────────────────┬─────────────────────────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
  Claude Code            Claude Code              Other MCP clients
       │                     │                     │
       └─────────────────────┴─────────────────────┘
                             │
                             ▼
              Service repo  →  GitHub Actions  →  GCP (Cloud Run, etc.)
              (Layer A — unchanged)
```

### Developer experience (fresh laptop)

| Step | Original plan (typical) | Evolved plan |
|------|-------------------------|--------------|
| 1 | Install Skills / plugin / clone skill repo | Add Golden Path MCP URL + SSO to client config |
| 2 | Find and bookmark docs | Docs served as MCP Resources (same server) |
| 3 | Configure MCP for deploy/status | Already configured in step 1 |
| 4 | Run `shop new` or ask Claude to scaffold | Ask Claude; skill loaded from MCP; calls `scaffold_service` |
| 5 | Push code; CI deploys | Same — unchanged |

**Onboarding collapses to one integration** with a guaranteed consistent knowledge + action surface.

---

## Comparison: original plan vs evolved plan

### Solution shape

| Dimension | Original (draft requirements) | Evolved (this proposal) |
|-----------|------------------------------|-------------------------|
| **Layer A** | Templates, modules, CI/CD | **Identical** |
| **Layer B knowledge** | Local / marketplace Skills | MCP Resources from GitHub |
| **Layer B actions** | MCP tools | **Same** MCP tools |
| **Layer C docs** | Separate site / portal | MCP Resources (+ optional static mirror) |
| **Integration count** | 3+ (skills, docs, MCP, maybe CLI) | **1** primary (MCP) + optional CLI |
| **Acceptance test** | Scaffold → `dev`, zero manual edits | **Unchanged** |

### Open decisions resolved

| §9 # | Decision | Original status | Evolved resolution |
|------|----------|-----------------|-------------------|
| 6 | MCP hosting & transport | Open | **Hosted internal MCP**, HTTPS, SSO (OIDC) |
| 7 | Skill distribution | Open | **MCP Resources** from pinned git release |
| 5 | Developer portal | Backstage vs docs-only | **MCP docs first**; Backstage deferred until adoption proves need |
| 4 | Template delivery | Template repo / CLI / Backstage | **MCP `scaffold_service`** + GitHub template (shared backend) |

Decisions 1–3, 8–10 (runtime, IaC, CI, DB, envs, off-road) are **unchanged** by this proposal.

### Consistency and governance

| Concern | Original plan | Evolved plan |
|---------|---------------|--------------|
| Who can change golden path guidance? | Unclear; local edits possible | **Platform admins via GitHub PR only** |
| Version pinning | Recommended, not enforced | **Enforced** — MCP serves `stable` / `beta` channels |
| Skill ↔ template alignment | Manual sync ownership | Same release tag bundles skills + template refs |
| Auditability of guidance changes | Git history if skills in repo | **Same**, but devs cannot bypass with local copies |
| Cross-client behavior | Varies by local skill install | **Same resources** for all MCP clients |

### Goals alignment (§2)

| Goal | How evolved plan helps |
|------|------------------------|
| Time-to-first-deploy &lt; 1 day | One MCP connection vs hunting skills/docs |
| Secure, observable default | Unchanged — still Layer A template + modules |
| Standardized, legible services | **Stronger** — one canonical instruction set |
| AI-assisted DX | **Stronger** — skills + tools co-located; skills always current on `stable` |

### Non-goals preserved (§3)

| Non-goal | Still true? |
|----------|-------------|
| No forced migration | ✓ Opt-in unchanged |
| Common case only | ✓ Still one default template family; multi-framework templates later |
| Humans own production | ✓ MCP assists; gated `trigger_deploy`; audit on writes |

---

## What “better” means — concrete benefits

### 1. Eliminates local skill drift

Skills remain authored as `SKILL.md` in GitHub — only the **delivery mechanism** changes. Developers do not maintain canonical copies on disk.

| Before | After |
|--------|-------|
| “Works on my machine” runbooks | Everyone reads `goldenpath://skills/...` at `v1.4.0` |
| Tribal knowledge in edited Skills | Off-road customizations in separate namespaces, not goldenpath official paths |

### 2. Single onboarding path

| Persona | Benefit |
|---------|---------|
| **Product engineer** | Connect MCP → ask “create a new Shop service” → done |
| **Tech lead** | Knows team sees same conventions version as platform |
| **SRE / Platform** | One release train: modules + template + skills + docs |
| **Security** | Read-only distribution; write tools audited; no shadow skill packs |

### 3. Unifies knowledge and action

Original design: *“Skills carry knowledge; MCP carries live actions.”* That separation is **logical**, not **physical**. Colocating both on one server means:

- Skills always reference tool names that exist on the same server version.
- Docs can link to resource URIs and tool names that resolve consistently.
- No “doc site updated but marketplace skill pack still on old version.”

### 4. Any machine, any application — with guardrails

| Capability | Detail |
|------------|--------|
| **Portability** | Any MCP client (Claude Code, future tools) |
| **Auth** | Caller’s SSO identity; permissions = caller’s GCP/GitHub access |
| **No privilege escalation** | MCP server does not grant broader access than the user already has |
| **Write tools phased** | Read-only tools first; `scaffold_service` / `trigger_deploy` after audit |

### 5. Simpler Layer C (without losing discoverability)

| Layer C item | Evolved approach |
|--------------|------------------|
| Start here | `goldenpath://docs/getting-started/01-start-here.md` |
| 15-minute quickstart | `goldenpath://docs/getting-started/03-quickstart.md` |
| Support channel | Unchanged — Slack / ticket queue |
| Service catalog | MCP tool `list_services` (+ portal later if needed) |
| Adoption metrics | Unchanged — time-to-deploy, % from template |

Backstage / developer portal becomes **optional Phase 3+**, not a launch dependency.

---

## What this proposal does **not** change

| Item | Why it must remain |
|------|-------------------|
| Terraform modules | Source of truth for infra; MCP invokes, does not embed |
| Reusable GitHub Actions workflow | Deploy path must work without AI |
| Service template repos | Concrete artifacts CI builds and deploys |
| Workload Identity Federation | Keyless CI — non-negotiable |
| Acceptance test (§6.2) | Zero manual edits to first `dev` deploy |
| Success metrics (§8) | Still measure deploy time, adoption, telemetry, security |

**MCP improves how developers learn and drive the path. It does not replace the path.**

---

## MCP surface area (proposed v1 → v2)

### Resources (read-only, from GitHub)

| URI pattern | Content |
|-------------|---------|
| `goldenpath://skills/{name}/SKILL.md` | Agent skill instructions |
| `goldenpath://skills/{name}/*` | Bundled scripts, templates referenced by skill |
| `goldenpath://docs/{path}` | Start here, quickstart, conventions, off-road policy |
| `goldenpath://meta/version` | Current channel, git tag, release notes link |

Optional helper tools if a client handles Resources poorly: `list_skills()`, `get_skill(name)`, `get_doc(path)`.

### Tools (phased)

| Phase | Tools | Notes |
|-------|-------|-------|
| **v1** | `list_services`, `get_deploy_status`, `get_service_config`, `get_cost_estimate` | Read-only; prove auth and audit |
| **v2** | `scaffold_service`, `trigger_deploy`, `validate_service` | Writes; confirmation + audit log |
| **v2** | `list_templates` | `nextjs`, future `streamlit`, etc. |

### Version channels

| Channel | Points to | Audience |
|---------|-----------|----------|
| `stable` | Tag e.g. `v1.4.0` | All product engineers |
| `beta` | Tag e.g. `v1.5.0-rc1` | Pilot team |
| `main` | Not default for devs | Platform internal only |

---

## Risks and mitigations

| Risk | Original §11 | Additional mitigation in evolved plan |
|------|--------------|--------------------------------------|
| Low adoption | Co-design with pilot; measure honestly | Faster onboarding (one MCP config) |
| Template / module / skill drift | Versioning + owner | **Single release tag** pins skills + template refs together |
| MCP security gap | No escalation; read-only first | Same + SSO + audit on all write tools |
| Over-engineering | Docs-only first | Defer Backstage; avoid separate skill marketplace |
| **MCP availability** | Not emphasized | Static docs mirror; CLI fallback; CI path independent of MCP |
| **Client Resource support** | N/A | Helper tools `get_skill` / `get_doc`; document tested clients |

---

## Revised phasing

| Phase | Original | Evolved |
|-------|----------|---------|
| **0 — Align** | §9 decisions, pilot, metrics | **+** Adopt MCP-centric distribution; close §6, §7 |
| **1 — Paved road** | Layer A: modules, CI, template | **Unchanged** — still the critical path |
| **2 — AI DX** | Skills authoring + MCP read tools → writes | **Unified MCP**: Resources (skills/docs) + read tools → write tools |
| **3 — Scale** | Docs, portal, rollout | MCP docs + metrics; portal only if needed |

**Phase 1 exit criterion unchanged:** pilot scaffolds and deploys to `dev` with zero manual edits — provable without MCP.

**Phase 2 exit criterion (updated):** developer on fresh machine with **only MCP configured** can scaffold and deploy guided by skills loaded from MCP Resources.

---

## Fallbacks (golden path works without MCP)

| Need | Without MCP |
|------|-------------|
| Scaffold | GitHub “Use this template” or `shop new` CLI |
| Deploy | Push to `main` → GitHub Actions |
| Docs | Public read-only mirror of `docs/` (GitHub Pages or internal static site) |
| Status | GCP console / `gcloud` (as today) |

MCP is the **preferred** experience, not a **hard dependency** for production deploys.

---

## Recommended updates to the requirements document

Replace §5 Layer B and related sections with language along these lines:

> **Layer B — Golden Path MCP Server**  
> A single hosted MCP server provides the AI-assisted developer experience:  
>
> - **Resources** — versioned skills and documentation from the `goldenpath` GitHub repository (read-only for developers; maintained by platform admins).
> - **Tools** — platform actions and live data (service catalog, deploy status, scaffolding, guarded deploy triggers).  
>  
> Skills are authored as `SKILL.md` in GitHub; they are **distributed via MCP**, not installed locally. Skills describe when and how to invoke MCP tools. Layer A artifacts (templates, modules, workflows) remain in GitHub and are referenced by both CI and MCP tools.

Close §7 (Skill distribution) as: **MCP Resources from pinned git releases, with `stable` and `beta` channels.**

---

## Summary verdict

| Question | Answer |
|----------|--------|
| Does this replace the Golden Path vision? | **No** — it strengthens distribution and consistency |
| Does it replace Layer A? | **No** |
| Is it better for consistency? | **Yes** — admin-controlled, pinned, read-only for devs |
| Is it better for fresh-laptop onboarding? | **Yes** — one MCP connection |
| Does it resolve open distribution decisions? | **Yes** — §6, §7, partially §5 |
| Main new risk? | MCP uptime — mitigated by CI-independent deploy path and doc mirrors |

**The paved road is still Terraform + CI + Cloud Run. The evolution is making that road impossible to misread: one GitHub source, one MCP front door, one version for every developer.**

---

## Appendix — glossary (additions)

| Term | Meaning |
|------|---------|
| **MCP Resource** | Read-only URI exposed by the MCP server (e.g. a skill or doc), backed by git content at a pinned ref |
| **Release channel** | Named pointer (`stable`, `beta`) to a git tag served by MCP |
| **Virtual filesystem** | MCP Resources addressable as `goldenpath://...` paths without copying files to the developer machine |
| **Official path** | Content under `goldenpath://` from platform releases; not user-editable locally |

---

## Related analysis (v0.3.8)

- [Coverage check](./golden-path-mcp-evolution-coverage-check.md) — requirement-by-requirement: does the project cover what the proposal asked for?
- [Parity analysis](./golden-path-mcp-evolution-parity-analysis.md) — side-by-side: how closely does delivery match proposal shape and intent?
- [Gap analysis](./golden-path-mcp-evolution-gap-analysis.md) — ranked gaps: what is missing and how much does it matter?
- [Architecture document](./golden-path-mcp-evolution-architecture.md) — C4 diagrams for this proposal

---

*Document version: 1.0 — 2026-06-15*

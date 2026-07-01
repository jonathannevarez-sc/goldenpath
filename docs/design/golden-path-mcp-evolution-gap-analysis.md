# Golden Path MCP Evolution — Gap Analysis

**Source document:** [golden-path-mcp-evolution-proposal.md](./golden-path-mcp-evolution-proposal.md) (stakeholder proposal, 2026-06-15)  
**Compared against:** `goldenpath` repository **v0.3.7** (as of 2026-06-24)  
**Audience:** Executives, product owners, engineers, security — all levels  
**Companion documents:** [Coverage check](./golden-path-mcp-evolution-coverage-check.md) · [Parity analysis](./golden-path-mcp-evolution-parity-analysis.md) · [Architecture](./golden-path-mcp-evolution-architecture.md)

---

## How to read this document

This document answers: **“What is still missing, and how much does it matter?”**

Gaps are ranked by **severity** (stakeholder risk), not by line count. Each gap includes **proposal expectation**, **current reality**, **impact**, and **suggested fix**.

| If you are… | Start here |
|-------------|------------|
| **Executive / sponsor** | Gap summary → High severity (G1–G4) → Messaging risks |
| **Product / program manager** | Gap summary → Medium severity → Roadmap recommendations |
| **Engineer / architect** | Full gap tables → Suggested fixes → Dependencies |
| **Security / compliance** | G1, G7, G14 → Security gap section |
| **New to Golden Path** | Plain-English summary → High severity gaps |

**Severity**

| Level | Meaning |
|-------|---------|
| 🔴 **High** | Stakeholder expectation risk — do not overclaim in decks |
| 🟡 **Medium** | Operational or adoption risk — plan before wide rollout |
| 🟢 **Low** | Polish — fix when convenient |

---

## Gap summary

| Severity | Count | Theme |
|----------|-------|-------|
| 🔴 High | 4 | SSO, dynamic channels, doc mirror, MCP-only onboarding |
| 🟡 Medium | 5 | Metrics, off-road doc, audit visibility, naming, acceptance proof |
| 🟢 Low | 4 | Skill assets URI, GitHub template UX, release notes, branding cleanup |

**Net assessment:** The paved road and MCP server are **production-usable for pilots**. Gaps are **trust and scale** issues — not “start over” issues.

---

## Plain-English summary

The project built what the proposal promised at its core: **one place to get official instructions and run platform actions**, while **deploy still works through GitHub**.

What is missing are the **enterprise finishing touches** and **one marketing claim**:

1. **Corporate login (SSO)** on the hosted server — today it is an API key.
2. **Live version channels** — today content is baked into the Docker image; switching `beta` is not a runtime flip.
3. **A backup docs website** if MCP is down.
4. **True one-step onboarding** — publishing a new service still needs the CLI or wizard, not just MCP.

None of these block a pilot team from scaffolding and deploying. They **do** block claiming “fully enterprise-ready” or “MCP-only fresh laptop” without caveats.

---

## 🔴 High severity gaps

### G1 — SSO/OIDC on hosted MCP

| Field | Detail |
|-------|--------|
| **Proposal says** | §127: MCP hosting resolved as “Hosted internal MCP, HTTPS, **SSO (OIDC)**” |
| **Reality today** | `MCP_API_KEY` enforced by `mcp/goldenpath_mcp/auth.py` on SSE/streamable-http |
| **Impact** | Security and executive stakeholders may assume corporate SSO is built-in |
| **Who feels it** | Security, enterprise IT, exec sponsors |
| **Suggested fix** | Short term: document OIDC proxy / IAP pattern in `mcp/guide.md`. Medium term: SSO middleware or Cloud Run + Identity-Aware Proxy |
| **Effort** | S (document) → M (IAP) → L (native OIDC in server) |
| **Blocks pilot?** | No — API key works for controlled pilots |

### G2 — Dynamic pinned release channels

| Field | Detail |
|-------|--------|
| **Proposal says** | §56, §139: MCP serves pinned git ref; `stable` / `beta` channels enforced |
| **Reality today** | `ContentStore` reads local filesystem; Docker **COPY** at build (`mcp/Dockerfile` sets `GOLDENPATH_VERSION=v0.3.7`) |
| **Impact** | `beta` channel is metadata-only on hosted — cannot serve different content without new image |
| **Who feels it** | Platform team running release trains; pilot teams expecting hot channel switch |
| **Suggested fix** | Option A: multi-image deploy per channel. Option B: sidecar git-sync volume. Option C: runtime fetch from GitHub API at pinned tag |
| **Effort** | M–L |
| **Blocks pilot?** | No — single `stable` image is sufficient for first pilot |

### G3 — Static docs mirror (MCP fallback)

| Field | Detail |
|-------|--------|
| **Proposal says** | §294: Docs fallback = “Public read-only mirror of `docs/` (GitHub Pages or internal static site)” |
| **Reality today** | Docs available via git clone and MCP only — no Pages/static export job in repo |
| **Impact** | MCP outage blocks doc-only users; proposal risk §268 mitigation incomplete |
| **Who feels it** | Developers without local clone; SRE during MCP incidents |
| **Suggested fix** | GitHub Pages workflow on `docs/` or internal static bucket; link from `goldenpath://meta/version` |
| **Effort** | S |
| **Blocks pilot?** | No — git clone is fallback today |

### G4 — Phase 2 exit: MCP-only deploy path

| Field | Detail |
|-------|--------|
| **Proposal says** | §284: “Developer on fresh machine with **only MCP configured** can scaffold and deploy guided by skills loaded from MCP Resources” |
| **Reality today** | `scaffold_service` works via MCP; **`shop publish`** (GitHub repo + WIF + push) is CLI/wizard only |
| **Impact** | Proposal overstates “one integration” onboarding; stakeholder decks must caveat |
| **Who feels it** | Product marketing, new-hire onboarding owners |
| **Suggested fix** | **Option A:** Update proposal exit criterion to include publish step. **Option B:** Add `publish_service` MCP tool (audited write) wrapping `shop publish` |
| **Effort** | S (doc) → M (tool) |
| **Blocks pilot?** | No — documented 7-step journey in `08-journey-mcp.md` |

---

## 🟡 Medium severity gaps

### G5 — Adoption and success metrics

| Field | Detail |
|-------|--------|
| **Proposal says** | §208, §223: Adoption metrics (time-to-deploy, % from template) |
| **Reality today** | Goals documented in `docs/platform/golden-path.md`; no dashboard or instrumentation in repo |
| **Impact** | Cannot prove ROI or Phase 3 exit criterion |
| **Suggested fix** | Define 3–5 metrics; instrument `shop new` / deploy workflow; simple Looker or spreadsheet for pilot |
| **Effort** | M |
| **Owner** | Product / platform program |

### G6 — Off-road policy document

| Field | Detail |
|-------|--------|
| **Proposal says** | §237: Docs include off-road policy; `goldenpath://docs/{path}` |
| **Reality today** | `docs/platform/golden-path.md` references `goldenpath://docs/off-road-policy.md` — **file does not exist** |
| **Impact** | Support boundaries unclear for teams leaving the paved road |
| **Suggested fix** | Author `docs/platform/off-road-policy.md`; add to `DOC_ALIASES` |
| **Effort** | S |
| **Owner** | Platform + security |

### G7 — Audit log visibility for write tools

| Field | Detail |
|-------|--------|
| **Proposal says** | §266: Audit on write tools; platform visibility |
| **Reality today** | `audit.py` writes JSON to **stderr** — visible in Cloud Run logs, no dashboard or alerts |
| **Impact** | Platform team blind to volume/anomalies of AI-driven scaffolds and deploy triggers |
| **Suggested fix** | Log-based metric on `jsonPayload.event`; Cloud Monitoring dashboard + alert policy |
| **Effort** | S–M |
| **Owner** | SRE / platform |

### G8 — Skill URI naming mismatch

| Field | Detail |
|-------|--------|
| **Proposal says** | Example skill `scaffold-service` |
| **Reality today** | Folder `scaffold-shop-service` |
| **Impact** | Confusion in diagrams, decks, and client Resource URIs |
| **Suggested fix** | Add alias Resource or rename at next major version |
| **Effort** | S |
| **Owner** | Platform / DevEx |

### G9 — Acceptance test proof for enterprises

| Field | Detail |
|-------|--------|
| **Proposal says** | §222: Zero manual edits to first `dev` deploy |
| **Reality today** | Tier 2 test `tests/integration/test_sandbox_deploy_spine.py` exists; requires sandbox GCP credentials |
| **Impact** | Enterprise buyers may not have run it; claim is design goal, not published result |
| **Suggested fix** | Pilot runbook + published timing/results doc; optional CI badge after sandbox run |
| **Effort** | M |
| **Owner** | Platform engineering |

---

## 🟢 Low severity gaps

### G10 — Bundled skill assets URI

| Field | Detail |
|-------|--------|
| **Proposal says** | `goldenpath://skills/{name}/*` for scripts/templates referenced by skills |
| **Reality today** | Only `SKILL.md` exposed as Resource |
| **Impact** | Low — skills embed instructions inline; helper tools cover most clients |
| **Suggested fix** | Add directory Resource handler or zip archive Resource |
| **Effort** | S–M |

### G11 — GitHub “Use this template” emphasis

| Field | Detail |
|-------|--------|
| **Proposal says** | Template delivery via MCP + GitHub template |
| **Reality today** | `shop new` / `scaffold_service` primary; template repo pattern not emphasized |
| **Impact** | Low — functional parity via CLI/MCP |
| **Suggested fix** | Document GitHub template repo setup in quickstart |
| **Effort** | S |

### G12 — Release notes in meta/version

| Field | Detail |
|-------|--------|
| **Proposal says** | `goldenpath://meta/version` includes release notes link |
| **Reality today** | `meta_version()` returns channel, version, counts — no `release_notes_url` |
| **Impact** | Low — developers use GitHub Releases manually |
| **Suggested fix** | Add `release_notes_url` field to `ContentStore.meta_version()` |
| **Effort** | S |

### G13 — Legacy Shop branding in identifiers

| Field | Detail |
|-------|--------|
| **Proposal says** | Shop-era naming in diagrams |
| **Reality today** | `shop-*` skills, `cli/shop`, `scaffold-shop-service` coexist with `goldenpath` branding |
| **Impact** | Low — cosmetic; does not break automation |
| **Suggested fix** | Rename in v1.0 branding pass with migration aliases |
| **Effort** | M |

---

## Security-specific gaps

| Gap | Status | Risk | Mitigation path |
|-----|--------|------|-----------------|
| SSO/OIDC (G1) | ❌ | Shared API key ≠ per-user identity | IAP or OIDC proxy |
| API key rotation | ⚠️ | Manual Secret Manager update | Rotation runbook + automation |
| Write tool audit (G7) | ⚠️ | Logs exist; no alerting | Monitoring dashboard |
| Privilege escalation | ✅ | MCP uses caller credentials | Maintain — do not add service-account broadening |
| `trigger_deploy` guard | ✅ | `confirm=true` required | Maintain |
| Read-only resources | ✅ | No write path to skills/docs | Maintain |

---

## Gap dependency map

```
G1 (SSO) ──────────────┐
G2 (channels) ─────────┼──► Enterprise "production ready" narrative
G3 (doc mirror) ───────┤
G7 (audit dashboard) ──┘

G4 (publish in MCP) ───► "One integration" onboarding claim

G5 (metrics) ──────────► Phase 3 exit / ROI proof

G6 (off-road policy) ──► Support model clarity (independent)
```

**Recommended sequencing for platform team:**

1. **G3** (doc mirror) — quick trust win  
2. **G6** (off-road policy) — unblocks support conversations  
3. **G7** (audit dashboard) — before expanding write tools  
4. **G1** (SSO/IAP) — before enterprise-wide hosted MCP  
5. **G2** (channels) — before advertising `beta`  
6. **G4 or doc update** — align messaging with reality  
7. **G5** (metrics) — parallel with pilot  

---

## Messaging risks — what not to claim yet

| Claim | Safe today? | Caveat |
|-------|-------------|--------|
| "One MCP front door for skills, docs, and tools" | ✅ Yes | |
| "Deploy does not depend on MCP" | ✅ Yes | |
| "SSO-built-in on hosted MCP" | ❌ No | API key; org adds IdP |
| "MCP-only fresh laptop onboarding" | ❌ No | Needs bootstrap + publish |
| "Beta channel for pilots" | ⚠️ Careful | Label only until G2 fixed |
| "Adoption metrics dashboard" | ❌ No | G5 |
| "Off-road policy documented" | ❌ No | G6 — file missing |
| "Zero manual edits proven" | ⚠️ Careful | Design goal; G9 |

---

## Recommendations by audience

### For executives

1. **Sponsor the pilot** — core vision is built (~82% coverage).  
2. **Fund G1 + G3 first** — SSO proxy and doc mirror are low-code, high-trust.  
3. **Ask for 90-day pilot metrics** (G5) before wide rollout.  
4. **Do not claim** MCP-only onboarding or built-in SSO without caveats.

### For product / program

1. Update stakeholder materials: version **v0.3.7**, not proposal example v1.4.0.  
2. Track **G1–G4** on public roadmap.  
3. Resolve G4 by **either** adding `publish_service` **or** revising Phase 2 exit criterion.  
4. Define Phase 3 metrics (time-to-first-dev-deploy, % templated services) before GA.

### For engineering

1. Close **G2** before advertising `beta` channel to external teams.  
2. Ship **G7** before adding new write tools.  
3. Add **G12** `release_notes_url` when tagging releases.  
4. Pin production Terraform modules to **commit SHA** (architecture recommendation — related hardening).

### For security

1. Treat `MCP_API_KEY` as a service secret — rotation runbook required.  
2. Place hosted MCP behind corporate IdP (**G1**) before broad access.  
3. Write tools are audited ✅ — add centralized visibility (**G7**) ❌.  
4. Confirm MCP cannot escalate beyond caller's GCP/GitHub IAM (verified in design).

---

## Gaps that are NOT gaps (intentional design)

These are sometimes reported as gaps but match the proposal or platform guide:

| Item | Why it is not a gap |
|------|---------------------|
| `shop publish` not in MCP | Proposal MCP tool list does not include publish; documented explicitly |
| Bootstrap not in MCP | Platform guide: GCP bootstrap is CLI/wizard |
| Teardown not in MCP | Safety — destructive ops stay in guarded scripts |
| Backstage portal missing | Proposal defers to Phase 3+ |
| 6 templates vs 1 | Exceeds proposal — not a deficiency |
| v0.3.7 vs v1.4.0 example | Same versioning model |

---

## Glossary

| Term | Plain language | In this document |
|------|----------------|------------------|
| **Gap** | Something the proposal expected that we do not have yet | Ranked by severity |
| **Severity** | How bad it is if we ignore the gap | High / Medium / Low |
| **Remediation** | How to close the gap | Suggested fix column |
| **Messaging risk** | A claim that could embarrass us in a review | Overclaiming SSO, MCP-only, etc. |
| **Pilot-safe** | OK for controlled early adopters | Most gaps are pilot-safe |

---

## Document history

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-06-24 | Initial gap analysis vs v0.3.7 (split from combined doc) |

---

© 2026 Varanabox. All rights reserved.

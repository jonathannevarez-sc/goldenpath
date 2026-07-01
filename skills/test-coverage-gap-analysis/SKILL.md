---
name: test-coverage-gap-analysis
phase: 2
description: >
  Audit Golden Path platform test coverage, find gaps, and produce a prioritized
  gap report with concrete test additions. Use when the user asks for test coverage
  analysis, coverage gaps, brutal testing review, co-tester audit, what's untested,
  or /test-coverage-gap-analysis.
distribution: mcp-resources
status: implemented
---

# Golden Path test coverage gap analysis

Systematic audit of **platform** tests in `tests/` — not scaffolded service repos (`templates/*/tests/`).

## When to use

- User wants a coverage gap report or "what's still untested"
- Before a release — verify deploy spine has regression tests
- After adding scripts, MCP tools, or wizard backends
- Co-tester / hostile QA review

## When NOT to use

- Service-repo tests after `shop new` — those live in the generated project

## Enterprise test tiers (mandatory)

| Tier | Runner | Release gate |
|------|--------|--------------|
| **1 — Contract** | `./tests/run-all-tests.sh` | Every PR — blocks merge |
| **2 — Integration** | `./tests/run-integration-tests.sh` | Release tags — blocks customer-facing promotion |

Tier 2 requires sandbox secrets (`INTEGRATION_TEST_ENABLED=1`, `GH_TOKEN`, `SHOP_GCP_DEV_PROJECT`, etc.). See `tests/README.md` § Release acceptance.

## Read first

- `tests/README.md` — enterprise test pyramid
- `tests/run-all-tests.sh` — Tier 1
- `tests/run-integration-tests.sh` — Tier 2
- `.github/workflows/tests.yml` and `integration-tests.yml`

---

## Step 1 — Run Tier 1 (contract)

```bash
./tests/run-all-tests.sh
```

Record: pytest count, Pester count, bash file results. **All must pass** — no skipped deploy-spine contracts.

---

## Step 2 — Inventory testable surface

Build two lists and diff them.

### A. Production code (platform)

| Area | Paths |
|------|-------|
| CLI | `cli/shop` |
| Shell libs | `scripts/lib/*.sh` |
| Wizard | `scripts/setup/goldenpath_setup.{py,sh}`, `goldenpath-setup.ps1`, `goldenpath_setup_app.py` |
| MCP package | `mcp/goldenpath_mcp/*.py` |
| Launchers | `scripts/goldenpath-setup*.sh` |

### B. Existing tests

| Suite | Location |
|-------|----------|
| Bash | `tests/bash/test_*.sh` |
| Python | `tests/test_*.py` |
| Pester | `tests/goldenpath-setup.tests.ps1` |

**Gap** = anything in A with no corresponding test file or no assertion of behavior (only `--help` counts as a gap).

---

## Step 3 — Brutal checks (run every audit)

Execute these probes; any failure is a **P0/P1 gap**:

### Scaffold integrity

```bash
bash tests/bash/test_shop_scaffold.sh
```

- All catalog templates must scaffold with **zero** `{{TOKEN}}` leaks
- `validate_service_repo` must return `valid: false` when tokens remain

### Safety

```bash
bash tests/bash/test_teardown_safety.sh
```

- Protected projects blocked
- `ALLOWED_TEARDOWN_PROJECTS` enforced (must pass on bash 3.2+)

### MCP security

```bash
tests/.venv/bin/python -m pytest tests/test_mcp_content.py -q -k traversal
```

- `read_skill` must reject `..`, slashes, hidden names
- `read_doc` must block path traversal (existing)

### Validator parity

```bash
tests/.venv/bin/python -m pytest tests/test_validator_parity.py -q
```

- Python `goldenpath_ops` and bash `validate_gcp_project_id` must agree on accept/reject

### Deploy spine contracts (Tier 1)

```bash
bash tests/bash/test_shop_publish_guards.sh
bash tests/bash/test_shop_doctor.sh
bash tests/bash/test_verify_deployment.sh
```

### MCP write tools

```bash
tests/.venv/bin/python -m pytest tests/test_mcp_server_tools.py -q
```

---

## Step 4 — Run Tier 2 before release

```bash
INTEGRATION_TEST_ENABLED=1 \
SHOP_GITHUB_ORG=... SHOP_GCP_DEV_PROJECT=... GCP_REGION=... GH_TOKEN=... \
  ./tests/run-integration-tests.sh
```

Tier 2 proves live `shop publish` → `shop verify` on the enterprise sandbox. **Required for customer-facing releases.**

---

## Step 5 — Separate tracks (not merge blockers)

| Area | Track |
|------|-------|
| Streamlit UI click paths | Manual QA / UI automation backlog |
| `platform/bootstrap` terraform apply | Enterprise sandbox bootstrap runbook |

---

## Step 6 — Prioritized gap report template

Deliver in this format:

```markdown
## Coverage gap report — <date>

### Summary
- Tests run: <N pytest, N bash, N Pester>
- P0 gaps: <count>
- P1 gaps: <count>

### P0 — Can break prod or safety
| Gap | Evidence | Recommended test |
|-----|----------|------------------|

### P1 — False green / deploy spine
| Gap | Evidence | Recommended test |

### P2 — Quality / drift
| Gap | Evidence | Recommended test |

### Covered (no action)
- <bullets>
```

**Severity guide:**

- **P0** — data loss, auth bypass, wrong project deleted, silent deploy failure
- **P1** — scaffold/publish/validate spine untested end-to-end
- **P2** — help-only tests, missing parity, doc drift

---

## Step 7 — Add tests (when asked to fix)

Follow existing patterns:

| Target | Pattern |
|--------|---------|
| Bash lib | `tests/bash/test_<name>.sh` + `lib/assert.sh` |
| Python module | `tests/test_<module>.py` + `conftest.py` fixtures |
| MCP tool | Mock `subprocess.run` / settings; no live GCP |
| Scaffold | Real `shop new` in temp dir + `assert_dir_has_no_tokens` |

After adding tests:

1. `./tests/run-all-tests.sh`
2. Update `tests/README.md` table
3. Re-run Step 3 probes

---

## CI alignment

| Workflow | Must match local runner |
|----------|---------------------------|
| `tests.yml` | `run-all-tests.sh` (Tier 1) |
| `integration-tests.yml` | `run-integration-tests.sh` (Tier 2 on release) |

Flag any Tier 1 deploy-spine contract missing from PR CI. Tier 2 must run on `v*` tags before customer promotion.

---

## MCP resources

- `goldenpath://docs/tests/README.md`
- `goldenpath://docs/repository-guide.md` (scripts + tests map)
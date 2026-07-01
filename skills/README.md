# Golden Path official skills

Six **agent playbooks** (`SKILL.md` files) for Claude and other MCP clients. They **instruct** — they do not execute. An agent reads them and then runs shell commands, MCP tools, or wizard scripts.

**Served as MCP resources:** `goldenpath://skills/{name}/SKILL.md`  
**Discovery:** `list_skills()` or `get_skill(name)` MCP tools (or client Resource URIs)  
**Full map:** [docs/repository-guide.md](../docs/repository-guide.md#skills--official-ai-agent-instructions-mcp-only)

## Skills vs wizard scripts

| | **Skill (`SKILL.md`)** | **Wizard script** |
|---|------------------------|-------------------|
| **Type** | Markdown playbook | Runnable program |
| **Runs alone?** | No | Yes |
| **Calls GCP/GitHub?** | No — agent does | Yes |
| **Config file** | None (agent may write `.goldenpath-setup.local.json`) | `.goldenpath-setup.local.json` |

A skill alone cannot bootstrap GCP or scaffold a repo. An agent following a skill **plus** shell/MCP achieves the same outcomes as the wizard.

## Official skills

| Skill | Path | When to use |
|-------|------|-------------|
| `goldenpath-setup-wizard` | [goldenpath-setup-wizard/SKILL.md](./goldenpath-setup-wizard/SKILL.md) | Full onboarding via wizard menu, headless commands, troubleshooting |
| `scaffold-shop-service` | [scaffold-shop-service/SKILL.md](./scaffold-shop-service/SKILL.md) | New service from templates, `shop new`, `scaffold_service` MCP tool |
| `deploy-to-shop-gcp` | [deploy-to-shop-gcp/SKILL.md](./deploy-to-shop-gcp/SKILL.md) | Deploy status, prod promotion, pipeline failures |
| `shop-terraform-conventions` | [shop-terraform-conventions/SKILL.md](./shop-terraform-conventions/SKILL.md) | Safe Terraform extensions in service `infra/` |
| `shop-observability` | [shop-observability/SKILL.md](./shop-observability/SKILL.md) | Logs, metrics, alerts for Golden Path services |
| `test-coverage-gap-analysis` | [test-coverage-gap-analysis/SKILL.md](./test-coverage-gap-analysis/SKILL.md) | Audit platform test gaps; brutal co-tester playbook |

## Distribution

Phase 2 delivers skills **only through MCP** — developers do not copy files to `~/.claude/skills/`. The MCP server reads from `GOLDENPATH_ROOT/skills/` at runtime.

See [docs/platform/golden-path.md](../docs/platform/golden-path.md) (MCP layer) and [mcp/README.md](../mcp/README.md).
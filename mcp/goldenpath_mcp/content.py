"""Read-only content loader for skills and docs (virtual filesystem)."""

from __future__ import annotations

import json
from pathlib import Path


# Stable MCP URIs (goldenpath://docs/{path}) → on-disk path under docs/
DOC_ALIASES: dict[str, str] = {
    # Canonical numbered paths
    "01-start-here.md": "getting-started/01-start-here.md",
    "02-pick-your-path.md": "getting-started/02-pick-your-path.md",
    "03-quickstart.md": "getting-started/03-quickstart.md",
    "04-journey-cli.md": "getting-started/04-journey-cli.md",
    "05-journey-wizard.md": "getting-started/05-journey-wizard.md",
    "06-wizard-powershell-advanced.md": "getting-started/06-wizard-powershell-advanced.md",
    "07-setup-wizard-usage.md": "getting-started/07-setup-wizard-usage.md",
    "08-journey-mcp.md": "getting-started/08-journey-mcp.md",
    "09-streamlit-setup-ui.md": "getting-started/09-streamlit-setup-ui.md",
    "10-shell-scripts-guide.md": "getting-started/10-shell-scripts-guide.md",
    "getting-started/01-start-here.md": "getting-started/01-start-here.md",
    "getting-started/02-pick-your-path.md": "getting-started/02-pick-your-path.md",
    "getting-started/03-quickstart.md": "getting-started/03-quickstart.md",
    "getting-started/04-journey-cli.md": "getting-started/04-journey-cli.md",
    "getting-started/05-journey-wizard.md": "getting-started/05-journey-wizard.md",
    "getting-started/06-wizard-powershell-advanced.md": "getting-started/06-wizard-powershell-advanced.md",
    "getting-started/07-setup-wizard-usage.md": "getting-started/07-setup-wizard-usage.md",
    "getting-started/08-journey-mcp.md": "getting-started/08-journey-mcp.md",
    "getting-started/09-streamlit-setup-ui.md": "getting-started/09-streamlit-setup-ui.md",
    "getting-started/10-shell-scripts-guide.md": "getting-started/10-shell-scripts-guide.md",
    # Legacy short names (stable MCP URIs)
    "start-here.md": "getting-started/01-start-here.md",
    "quickstart.md": "getting-started/03-quickstart.md",
    "SETUP-WIZARD-USAGE.md": "getting-started/07-setup-wizard-usage.md",
    "JOURNEY-CLI.md": "getting-started/04-journey-cli.md",
    "JOURNEY-MCP.md": "getting-started/08-journey-mcp.md",
    "JOURNEY-WIZARD.md": "getting-started/05-journey-wizard.md",
    "JOURNEY-POWERSHELL.md": "getting-started/06-wizard-powershell-advanced.md",
    "getting-started-platform.md": "platform/getting-started-platform.md",
    "phase-0-checklist.md": "platform/phase-0-checklist.md",
    "golden-path.md": "platform/golden-path.md",
    "golden-path-gcp-requirements.md": "platform/golden-path-gcp-requirements.md",
    "app-tech-dictionary.md": "platform/app-tech-dictionary.md",
    "sandbox-env.md": "environments/sandbox-env.md",
    "environments/sandbox-env.md": "environments/sandbox-env.md",
    "PERSONAL-GCP-TEST.md": "environments/sandbox-env.md",
    "TEARDOWN-ENV.md": "environments/sandbox-env.md",
    "golden-path-mcp-evolution-proposal.md": "design/golden-path-mcp-evolution-proposal.md",
    "design/golden-path-mcp-evolution-proposal.md": "design/golden-path-mcp-evolution-proposal.md",
    "architecture.md": "platform/architecture.md",
    "platform/architecture.md": "platform/architecture.md",
    "code-bible.md": "platform/code-bible.md",
    "platform/code-bible.md": "platform/code-bible.md",
    "problem-statement.md": "platform/problem-statement.md",
    "platform/problem-statement.md": "platform/problem-statement.md",
    "tutorial-guide.md": "platform/tutorial-guide.md",
    "platform/tutorial-guide.md": "platform/tutorial-guide.md",
    "platform/golden-path.md": "platform/golden-path.md",
    "platform/getting-started-platform.md": "platform/getting-started-platform.md",
    "platform/phase-0-checklist.md": "platform/phase-0-checklist.md",
    "platform/app-tech-dictionary.md": "platform/app-tech-dictionary.md",
    "platform/golden-path-gcp-requirements.md": "platform/golden-path-gcp-requirements.md",
    "repository-guide.md": "repository-guide.md",
    "getting-started/readme.md": "getting-started/readme.md",
    "getting-started/README.md": "getting-started/readme.md",
    "README.md": "readme.md",
    "PICK-YOUR-PATH.md": "getting-started/02-pick-your-path.md",
    "02-PICK-YOUR-PATH.md": "getting-started/02-pick-your-path.md",
    "04-JOURNEY-CLI.md": "getting-started/04-journey-cli.md",
    "05-JOURNEY-WIZARD.md": "getting-started/05-journey-wizard.md",
    "06-WIZARD-POWERSHELL-ADVANCED.md": "getting-started/06-wizard-powershell-advanced.md",
    "07-SETUP-WIZARD-USAGE.md": "getting-started/07-setup-wizard-usage.md",
    "08-JOURNEY-MCP.md": "getting-started/08-journey-mcp.md",
    "09-STREAMLIT-SETUP-UI.md": "getting-started/09-streamlit-setup-ui.md",
    "10-SHELL-SCRIPTS-GUIDE.md": "getting-started/10-shell-scripts-guide.md",
    "REPOSITORY-GUIDE.md": "repository-guide.md",
    "SANDBOX-ENV.md": "environments/sandbox-env.md",
    "GOLDEN-PATH.md": "platform/golden-path.md",
    "GETTING-STARTED-PLATFORM.md": "platform/getting-started-platform.md",
    "APP_TECH_DICTIONARY.md": "platform/app-tech-dictionary.md",
    "CODE_BIBLE.md": "platform/code-bible.md",
    "PROBLEM_STATEMENT.md": "platform/problem-statement.md",
    "TUTORIAL_GUIDE.md": "platform/tutorial-guide.md",
    "PHASE-0-CHECKLIST.md": "platform/phase-0-checklist.md",
    "ARCHITECTURE.md": "platform/architecture.md",
}


class ContentStore:
    """Serves goldenpath:// resources from the git repo on disk."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.skills_dir = repo_root / "skills"
        self.docs_dir = repo_root / "docs"
        self.catalog_path = repo_root / "templates" / "catalog.json"

    def _safe_path(self, base: Path, relative: str) -> Path:
        rel = relative.lstrip("/")
        target = (base / rel).resolve()
        if not str(target).startswith(str(base.resolve())):
            raise ValueError(f"path traversal blocked: {relative}")
        return target

    def _resolve_doc_path(self, path: str) -> str:
        rel = path.lstrip("/")
        if rel in DOC_ALIASES:
            return DOC_ALIASES[rel]
        return rel

    def read_doc(self, path: str) -> str:
        resolved = self._resolve_doc_path(path)
        target = self._safe_path(self.docs_dir, resolved)
        if not target.is_file():
            raise FileNotFoundError(f"doc not found: {path}")
        return target.read_text(encoding="utf-8")

    def list_docs(self) -> list[str]:
        if not self.docs_dir.exists():
            return []
        return sorted(
            str(p.relative_to(self.docs_dir))
            for p in self.docs_dir.rglob("*.md")
            if p.is_file()
        )

    def _validate_skill_name(self, name: str) -> None:
        if not name or name.startswith(".") or ".." in name or "/" in name or "\\" in name:
            raise ValueError(f"invalid skill name: {name}")

    def read_skill(self, name: str) -> str:
        self._validate_skill_name(name)
        target = self._safe_path(self.skills_dir, f"{name}/SKILL.md")
        if not target.is_file():
            raise FileNotFoundError(f"skill not found: {name}")
        return target.read_text(encoding="utf-8")

    def list_skills(self) -> list[str]:
        if not self.skills_dir.exists():
            return []
        return sorted(
            p.parent.name
            for p in self.skills_dir.glob("*/SKILL.md")
        )

    def read_catalog(self) -> dict:
        if not self.catalog_path.is_file():
            return {}
        return json.loads(self.catalog_path.read_text(encoding="utf-8"))

    def meta_version(self, channel: str, version: str) -> dict:
        return {
            "channel": channel,
            "version": version,
            "repo_root": str(self.repo_root),
            "skills_count": len(self.list_skills()),
            "docs_count": len(self.list_docs()),
        }
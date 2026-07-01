#!/usr/bin/env python3
"""Golden Path — shared wizard operations (pure Python).

Ports scripts/setup/modules/{Bootstrap,Scaffold,Publish,Verify}.ps1 so the
Python CLI wizard does not depend on PowerShell.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

_LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

_SETUP_DIR = Path(__file__).resolve().parent
if str(_SETUP_DIR) not in sys.path:
    sys.path.insert(0, str(_SETUP_DIR))

import wizard_defaults as wd  # noqa: E402

SKIP_PATH_FRAGMENTS = (
    "node_modules",
    "package-lock.json",
    "__pycache__",
    ".pytest_cache",
    "/.git/",
)


def find_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(8):
        if (current / "templates" / "catalog.json").is_file():
            return current
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path(__file__).resolve().parent.parent.parent


REPO_ROOT = find_repo_root()
CONFIG_PATH = REPO_ROOT / ".goldenpath-setup.local.json"
BOOTSTRAP_DIR = REPO_ROOT / "platform/bootstrap"
ENTERPRISE_ENV = wd.enterprise_env_path(REPO_ROOT)
DEFAULT_SCAFFOLD_OUTPUT = REPO_ROOT.parent


def protected_projects() -> frozenset[str]:
    return wd.protected_project_ids(REPO_ROOT)


def default_config() -> dict:
    return wd.default_wizard_config(REPO_ROOT)


def load_config(config_path: Path | str | None = None) -> dict:
    path = Path(config_path) if config_path else CONFIG_PATH
    cfg = wd.merge_saved_config(path, REPO_ROOT)
    wd.apply_enterprise_env_overrides(cfg, REPO_ROOT)
    return cfg


def save_config(cfg: dict) -> None:
    wd.apply_enterprise_env_overrides(cfg, REPO_ROOT)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


GCP_PROJECT_DISPLAY_NAME_MAX = 30


def _is_api_propagation_apply_error(detail: str) -> bool:
    """True when terraform apply failed because newly enabled APIs are not ready yet."""
    if not detail:
        return False
    markers = (
        "workloadIdentityPools.create",
        "artifactregistry.repositories.create",
        "IAM_PERMISSION_DENIED",
    )
    return any(m in detail for m in markers)


def normalize_project_display_name(
    name: str, *, fallback: str = "Golden Path Sandbox"
) -> str:
    """GCP project display names must be at most 30 characters."""
    value = (name or "").strip() or fallback
    if len(value) <= GCP_PROJECT_DISPLAY_NAME_MAX:
        return value
    return value[:GCP_PROJECT_DISPLAY_NAME_MAX]


def validate_project_id(pid: str) -> str | None:
    pid = pid.strip().lower()
    if len(pid) < 6 or len(pid) > 30:
        return "Project ID must be 6–30 characters."
    if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", pid):
        return (
            "Use lowercase letters, numbers, and hyphens; must start with a "
            "letter and not end with a hyphen."
        )
    if "--" in pid:
        return "Project ID cannot contain consecutive hyphens."
    if pid in protected_projects():
        return f"Project '{pid}' is protected and cannot be used as a sandbox."
    return None


def validate_service_name(name: str) -> str | None:
    if len(name) < 3 or len(name) > 40:
        return "Service name must be 3–40 characters."
    if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", name):
        return (
            "Use lowercase kebab-case; start with a letter, no trailing hyphen "
            "(e.g. my-streamlit-app)."
        )
    if "--" in name:
        return "Service name cannot contain consecutive hyphens."
    return None


def is_valid_wif_provider(value: str) -> bool:
    if not value or "Warning:" in value or "No outputs found" in value:
        return False
    return bool(
        re.match(
            r"^projects/\d+/locations/global/workloadIdentityPools/[^/]+/providers/",
            value.strip(),
        )
    )


def is_valid_wif_service_account(value: str) -> bool:
    if not value or "Warning:" in value or "No outputs found" in value:
        return False
    return bool(
        re.match(
            r"^github-actions@[a-z][a-z0-9-]+\.iam\.gserviceaccount\.com$",
            value.strip(),
        )
    )


def wif_credentials_stale(cfg: dict) -> bool:
    provider = cfg.get("wif_provider", "")
    sa = cfg.get("wif_service_account", "")
    if provider and not is_valid_wif_provider(provider):
        return True
    if sa and not is_valid_wif_service_account(sa):
        return True
    if not sa:
        return False
    expected = f"github-actions@{cfg['gcp_dev_project']}.iam.gserviceaccount.com"
    return sa != expected


def cmd_available(name: str) -> bool:
    return shutil.which(name) is not None


@dataclass
class CmdResult:
    exit_code: int
    stdout: str
    stderr: str


def run_cmd(
    cmd: list[str],
    cwd: str | Path | None = None,
    timeout: int = 300,
) -> CmdResult:
    _cwd = str(cwd or REPO_ROOT)
    try:
        result = subprocess.run(
            cmd,
            cwd=_cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CmdResult(
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip(),
        )
    except FileNotFoundError:
        if sys.platform == "win32":
            # .cmd/.bat wrappers (e.g. gcloud.cmd) can't be run directly —
            # retry through cmd.exe which resolves PATHEXT properly.
            try:
                result = subprocess.run(
                    ["cmd", "/c"] + list(cmd),
                    cwd=_cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return CmdResult(
                    result.returncode,
                    result.stdout.strip(),
                    result.stderr.strip(),
                )
            except Exception:
                pass
        return CmdResult(127, "", f"Command not found: {cmd[0]}")
    except subprocess.TimeoutExpired:
        return CmdResult(1, "", f"Command timed out after {timeout}s")
    except Exception as exc:
        return CmdResult(1, "", str(exc))


def run_cmd_live(
    cmd: list[str],
    cwd: str | Path | None = None,
    on_line: Callable[[str], None] | None = None,
) -> CmdResult:
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        stdout_lines: list[str] = []
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
            stripped = line.rstrip("\n")
            if on_line and stripped:
                on_line(stripped)
            stdout_lines.append(stripped)
        proc.wait()
        return CmdResult(proc.returncode or 0, "\n".join(stdout_lines).strip(), "")
    except FileNotFoundError:
        return CmdResult(127, "", f"Command not found: {cmd[0]}")
    except Exception as exc:
        return CmdResult(1, "", str(exc))


def get_scaffold_output_dir() -> Path:
    return DEFAULT_SCAFFOLD_OUTPUT


def service_dir_for(cfg: dict, name: str | None = None) -> Path | None:
    svc = name or cfg.get("last_service")
    if not svc:
        return None
    saved = cfg.get("last_service_dir")
    if saved:
        p = Path(saved)
        if p.exists():
            return p
    outside = DEFAULT_SCAFFOLD_OUTPUT / svc
    if outside.exists():
        return outside
    inside = REPO_ROOT / svc
    if inside.exists():
        return inside
    return outside


def load_catalog() -> dict:
    path = REPO_ROOT / "templates/catalog.json"
    if not path.exists():
        raise FileNotFoundError("Missing templates/catalog.json")
    return json.loads(path.read_text())


def _parse_env_file(path: Path) -> dict[str, str]:
    profile: dict[str, str] = {}
    for line in path.read_text().splitlines():
        m = re.match(r"^\s*([A-Z_]+)=(.*)$", line)
        if m:
            profile[m.group(1)] = m.group(2).strip()
    return profile


def write_bootstrap_tfvars(cfg: dict) -> None:
    ar_repo = cfg.get("artifact_registry_repo") or wd.platform_default(
        "ARTIFACT_REGISTRY_REPO", REPO_ROOT
    )
    if not ar_repo:
        raise RuntimeError(
            "set ARTIFACT_REGISTRY_REPO in config/enterprise.env"
        )
    content = f"""# Generated by Golden Path Python wizard
personal_test        = true
test_project_id      = "{cfg['gcp_project']}"
region               = "{cfg['gcp_region']}"
github_org           = "{cfg['github_org']}"
github_repo          = "{cfg['github_platform_repo']}"
artifact_registry_id = "{ar_repo}"
"""
    (BOOTSTRAP_DIR / "terraform.tfvars").write_text(content)


def bootstrap(cfg: dict) -> None:
    if not ENTERPRISE_ENV.exists():
        raise FileNotFoundError(
            f"Missing {ENTERPRISE_ENV} — copy config/enterprise.env.example"
        )
    profile = _parse_env_file(ENTERPRISE_ENV)
    parent = profile.get("PARENT_PROJECT_ID", "")
    billing = profile.get("BILLING_ACCOUNT_ID", "")
    project = cfg["gcp_project"]
    display = normalize_project_display_name(
        cfg.get("project_display_name", ""),
        fallback=project,
    )

    if project == parent:
        raise RuntimeError(
            f"Project must differ from parent billing project ({parent})"
        )

    exists = run_cmd(["gcloud", "projects", "describe", project])
    if exists.exit_code != 0:
        create = run_cmd(
            ["gcloud", "projects", "create", project, f"--name={display}"]
        )
        if create.exit_code != 0:
            raise RuntimeError(f"gcloud projects create failed: {create.stderr}")

    billing_state = run_cmd(
        [
            "gcloud",
            "billing",
            "projects",
            "describe",
            project,
            "--format=value(billingEnabled)",
        ]
    )
    if billing_state.stdout.strip() != "True":
        link = run_cmd(
            [
                "gcloud",
                "billing",
                "projects",
                "link",
                project,
                f"--billing-account=billingAccounts/{billing}",
            ]
        )
        if link.exit_code != 0:
            raise RuntimeError(f"billing link failed: {link.stderr}")

    write_bootstrap_tfvars(cfg)
    run_cmd(["gcloud", "config", "set", "project", project])
    run_cmd(
        ["gcloud", "auth", "application-default", "set-quota-project", project]
    )

    init = run_cmd(
        ["terraform", "init", "-input=false"],
        cwd=BOOTSTRAP_DIR,
        timeout=600,
    )
    if init.exit_code != 0:
        detail = init.stderr or init.stdout
        raise RuntimeError(f"terraform init failed: {detail}")

    apply = run_cmd(
        ["terraform", "apply", "-auto-approve", "-input=false"],
        cwd=BOOTSTRAP_DIR,
        timeout=900,
    )
    if apply.exit_code != 0:
        detail = apply.stderr or apply.stdout
        if _is_api_propagation_apply_error(detail):
            time.sleep(15)
            apply = run_cmd(
                ["terraform", "apply", "-auto-approve", "-input=false"],
                cwd=BOOTSTRAP_DIR,
                timeout=900,
            )
            if apply.exit_code == 0:
                return
            detail = apply.stderr or apply.stdout
        raise RuntimeError(f"terraform apply failed: {detail}")


def teardown(delete_project: bool) -> None:
    tfvars = BOOTSTRAP_DIR / "terraform.tfvars"
    if not tfvars.exists():
        raise FileNotFoundError(f"Missing {tfvars} — run bootstrap first")
    content = tfvars.read_text()
    if not re.search(r"personal_test\s*=\s*true", content):
        raise RuntimeError("terraform.tfvars must have personal_test = true")
    m = re.search(r'test_project_id\s*=\s*"([^"]+)"', content)
    if not m:
        raise RuntimeError("Could not read test_project_id from terraform.tfvars")
    project_id = m.group(1)

    init = run_cmd(
        ["terraform", "init", "-input=false"],
        cwd=BOOTSTRAP_DIR,
        timeout=600,
    )
    if init.exit_code != 0:
        raise RuntimeError("terraform init failed")

    destroy = run_cmd(
        ["terraform", "destroy", "-auto-approve", "-input=false"],
        cwd=BOOTSTRAP_DIR,
        timeout=900,
    )
    if destroy.exit_code != 0:
        raise RuntimeError("terraform destroy failed")

    if delete_project:
        if project_id in protected_projects():
            raise RuntimeError(f"Refusing to delete protected project {project_id}")
        delete = run_cmd(["gcloud", "projects", "delete", project_id, "--quiet"])
        if delete.exit_code != 0:
            raise RuntimeError("gcloud projects delete failed")


def _terraform_bootstrap_project_id() -> str | None:
    proj = run_cmd(
        ["terraform", "output", "-raw", "project_id"],
        cwd=BOOTSTRAP_DIR,
    )
    if proj.exit_code == 0 and proj.stdout:
        return proj.stdout.strip()
    tfvars = BOOTSTRAP_DIR / "terraform.tfvars"
    if tfvars.exists():
        m = re.search(r'test_project_id\s*=\s*"([^"]+)"', tfvars.read_text())
        if m:
            return m.group(1)
    return None


def get_wif_credentials(project_id: str) -> dict | None:
    tfvars = BOOTSTRAP_DIR / "terraform.tfvars"
    state_files = [
        BOOTSTRAP_DIR / "terraform.tfstate",
        BOOTSTRAP_DIR / ".terraform/terraform.tfstate",
    ]
    has_state = any(p.exists() for p in state_files)

    if tfvars.exists() and has_state:
        if not (BOOTSTRAP_DIR / ".terraform").exists():
            run_cmd(["terraform", "init", "-input=false"], cwd=BOOTSTRAP_DIR)
        state_project = _terraform_bootstrap_project_id()
        if not state_project or state_project == project_id:
            provider = run_cmd(
                ["terraform", "output", "-raw", "dev_github_wif_provider_name"],
                cwd=BOOTSTRAP_DIR,
            )
            sa = run_cmd(
                ["terraform", "output", "-raw", "dev_github_actions_sa_email"],
                cwd=BOOTSTRAP_DIR,
            )
            if (
                provider.exit_code == 0
                and sa.exit_code == 0
                and is_valid_wif_provider(provider.stdout)
                and is_valid_wif_service_account(sa.stdout)
            ):
                return {
                    "provider": provider.stdout.strip(),
                    "service_account": sa.stdout.strip(),
                    "source": "terraform",
                }

    sa = run_cmd(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "list",
            f"--project={project_id}",
            "--filter=email:github-actions@",
            "--format=value(email)",
        ]
    )
    if sa.exit_code != 0 or not sa.stdout:
        return None

    pool = run_cmd(
        [
            "gcloud",
            "iam",
            "workload-identity-pools",
            "list",
            f"--project={project_id}",
            "--location=global",
            "--format=value(name)",
        ]
    )
    if pool.exit_code != 0 or not pool.stdout:
        return None

    pool_name = re.sub(
        r".*/workloadIdentityPools/", "", pool.stdout.splitlines()[0]
    )
    provider = run_cmd(
        [
            "gcloud",
            "iam",
            "workload-identity-pools",
            "providers",
            "list",
            f"--project={project_id}",
            "--location=global",
            f"--workload-identity-pool={pool_name}",
            "--format=value(name)",
        ]
    )
    if provider.exit_code != 0 or not provider.stdout:
        return None

    return {
        "provider": provider.stdout.splitlines()[0],
        "service_account": sa.stdout.splitlines()[0],
        "source": "gcloud",
    }


def set_github_secrets(cfg: dict, repo: str) -> bool:
    if not cmd_available("gh"):
        raise RuntimeError("gh CLI required. Install: https://cli.github.com/")
    if not cfg.get("wif_provider") or not cfg.get("wif_service_account"):
        return False

    full_repo = repo if "/" in repo else f"{cfg['github_org']}/{repo}"
    r1 = run_cmd(
        [
            "gh",
            "secret",
            "set",
            "GCP_WIF_PROVIDER",
            "--body",
            cfg["wif_provider"],
            "--repo",
            full_repo,
        ]
    )
    r2 = run_cmd(
        [
            "gh",
            "secret",
            "set",
            "GCP_WIF_SERVICE_ACCOUNT",
            "--body",
            cfg["wif_service_account"],
            "--repo",
            full_repo,
        ]
    )
    if r1.exit_code != 0 or r2.exit_code != 0:
        raise RuntimeError("Failed to set secrets. Run: gh auth login")
    return True


def _should_skip_file(path: Path) -> bool:
    s = str(path)
    return any(frag in s for frag in SKIP_PATH_FRAGMENTS)


def _cfg_value(cfg: dict, key: str, default: str = "") -> str:
    val = cfg.get(key)
    return str(val) if val else default


def resolve_platform_repo(cfg: dict, service_name: str | None = None) -> str:
    """Platform repo must not be the service name (common wizard mistake)."""
    repo = (
        cfg.get("github_platform_repo")
        or wd.platform_default("PLATFORM_REPO", REPO_ROOT)
        or "goldenpath"
    )
    if service_name and repo == service_name:
        return wd.platform_default("PLATFORM_REPO", REPO_ROOT) or "goldenpath"
    return repo


def check_deploy_platform_repo(service_dir: Path, cfg: dict) -> str | None:
    deploy = service_dir / ".github/workflows/deploy.yml"
    if not deploy.exists():
        return None
    service_name = service_dir.name
    expected = resolve_platform_repo(cfg, service_name)
    org = _cfg_value(cfg, "github_org")
    wrong_ref = f"{org}/{service_name}/"
    if expected != service_name and wrong_ref in deploy.read_text():
        return (
            f"deploy.yml references platform repo '{service_name}' — "
            f"should be '{expected}' (re-scaffold or publish to auto-repair)"
        )
    return None


def recover_deploy_local(
    service_dir: Path,
    environment: str = "dev",
    image_tag: str | None = None,
) -> bool:
    script = REPO_ROOT / "scripts/lib/deploy-recover-local.sh"
    if not script.is_file():
        return False
    if sys.platform == "win32":
        bash = shutil.which("bash")
        if not bash:
            return False
        runner = [bash, str(script)]
    else:
        runner = [str(script)]
    if not image_tag:
        sha = run_cmd(["git", "rev-parse", "HEAD"], cwd=service_dir)
        if sha.exit_code != 0 or not sha.stdout:
            return False
        image_tag = sha.stdout.strip()
    result = run_cmd(runner + [str(service_dir), environment, "--image-tag", image_tag])
    return result.exit_code == 0


def apply_scaffold_tokens(
    target_dir: Path,
    service_name: str,
    cfg: dict,
    meta: dict,
) -> None:
    platform_repo = resolve_platform_repo(cfg, service_name)
    replacements = [
        ("{{SERVICE_NAME}}", service_name),
        ("{{GITHUB_ORG}}", _cfg_value(cfg, "github_org")),
        ("{{PLATFORM_REPO}}", platform_repo),
        ("{{GOLDENPATH_VERSION}}", wd.resolve_goldenpath_version(REPO_ROOT)),
        ("{{GCP_DEV_PROJECT}}", _cfg_value(cfg, "gcp_dev_project")),
        ("{{GCP_PROD_PROJECT}}", _cfg_value(cfg, "gcp_prod_project")),
        ("{{GCP_REGION}}", _cfg_value(cfg, "gcp_region") or wd.platform_default("GCP_REGION", REPO_ROOT)),
        ("{{ARTIFACT_REGISTRY_REPO}}", wd.platform_default("ARTIFACT_REGISTRY_REPO", REPO_ROOT)),
        ("{{APP_RUNTIME}}", str(meta.get("app_runtime", "node"))),
        ("{{HEALTH_CHECK_PATH}}", str(meta.get("health_check_path", "/api/health"))),
        ("{{CONTAINER_PORT}}", str(meta.get("container_port", 3000))),
    ]

    for file_path in target_dir.rglob("*"):
        if not file_path.is_file() or _should_skip_file(file_path):
            continue
        try:
            raw = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if not any(old in raw for old, _ in replacements):
            continue

        for old, new in replacements:
            raw = raw.replace(old, new)
        file_path.write_text(raw, encoding="utf-8")


def test_deploy_workflow(service_dir: Path) -> Path | None:
    deploy = service_dir / ".github/workflows/deploy.yml"
    if not deploy.exists():
        return None
    if re.search(r"\{\{[A-Z_]+\}\}", deploy.read_text()):
        return deploy
    return None


def get_service_template_hint(service_dir: Path) -> str | None:
    req = service_dir / "requirements.txt"
    if req.exists():
        content = req.read_text()
        if re.search(r"(?m)^streamlit", content):
            return "streamlit"
        if re.search(r"(?m)^fastapi", content):
            return "fastapi"

    pkg = service_dir / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
        except json.JSONDecodeError:
            data = {}
        deps = list((data.get("dependencies") or {}).keys()) + list(
            (data.get("devDependencies") or {}).keys()
        )
        if "next" in deps:
            return "nextjs"
        if "express" in deps:
            return "express"
        if "react" in deps:
            return "react-spa"
        if "svelte" in deps:
            return "svelte-spa"
    return None


def verify_gh_auth_matches_org(github_org: str) -> None:
    """Block publish when active gh user != configured GITHUB_ORG."""
    if not cmd_available("gh"):
        raise RuntimeError("gh CLI required — https://cli.github.com/")
    result = run_cmd(["gh", "auth", "status"])
    combined = f"{result.stdout}\n{result.stderr}"
    if result.exit_code != 0:
        raise RuntimeError("not logged in to GitHub — run: gh auth login")
    match = re.search(r"account (\S+)", combined)
    active = match.group(1) if match else ""
    if active and active != github_org:
        raise RuntimeError(
            f"active gh account is '{active}' but GITHUB_ORG is '{github_org}' "
            f"— run: gh auth switch --user {github_org}"
        )


def upgrade_platform_version_refs(service_dir: Path, version: str) -> None:
    """Bump pinned @vX.Y.Z and ?ref=vX.Y.Z when wizard config was stale."""
    if not version:
        return
    patterns = [
        (re.compile(r"@v\d+\.\d+\.\d+"), f"@{version}"),
        (re.compile(r"\?ref=v\d+\.\d+\.\d+"), f"?ref={version}"),
        (re.compile(r"goldenpath_version:\s*v\d+\.\d+\.\d+"), f"goldenpath_version: {version}"),
        (
            re.compile(r'goldenpath_version\s*=\s*"v\d+\.\d+\.\d+"'),
            f'goldenpath_version   = "{version}"',
        ),
    ]
    for path in service_dir.rglob("*"):
        if not path.is_file() or _should_skip_file(path):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated = raw
        for pattern, repl in patterns:
            updated = pattern.sub(repl, updated)
        if updated != raw:
            path.write_text(updated, encoding="utf-8")


def upgrade_platform_pins(service_dir: Path, cfg: dict) -> None:
    """Align workflow + Terraform pins to enterprise.env version and org."""
    version = wd.resolve_goldenpath_version(REPO_ROOT)
    org = _cfg_value(cfg, "github_org") or wd.platform_default("GITHUB_ORG", REPO_ROOT)
    platform = resolve_platform_repo(cfg, service_dir.name)
    upgrade_platform_version_refs(service_dir, version)
    if not org or not platform:
        return
    workflow_ref = (
        re.compile(
            r"uses: [^/\s]+/[^/\s]+/\.github/workflows/deploy\.yml@v\d+\.\d+\.\d+"
        ),
        f"uses: {org}/{platform}/.github/workflows/deploy.yml@{version}",
    )
    patterns = [
        workflow_ref,
        (re.compile(r"goldenpath_org:\s*\S+"), f"goldenpath_org: {org}"),
        (
            re.compile(r"github\.com/[^/]+/[^/]+\.git"),
            f"github.com/{org}/{platform}.git",
        ),
        (re.compile(r"av-sparqgit/goldenpath"), f"{org}/{platform}"),
        (re.compile(r"aanundgit/goldenpath"), f"{org}/{platform}"),
    ]
    for path in service_dir.rglob("*"):
        if not path.is_file() or _should_skip_file(path):
            continue
        if path.suffix not in (".yml", ".yaml", ".tf", ".tfvars"):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated = raw
        for pattern, repl in patterns:
            updated = pattern.sub(repl, updated)
        if updated != raw:
            path.write_text(updated, encoding="utf-8")


def check_deploy_pin_issues(service_dir: Path, cfg: dict) -> list[str]:
    issues: list[str] = []
    version = wd.resolve_goldenpath_version(REPO_ROOT)
    org = _cfg_value(cfg, "github_org") or wd.platform_default("GITHUB_ORG", REPO_ROOT)
    platform = resolve_platform_repo(cfg, service_dir.name)
    deploy = service_dir / ".github/workflows/deploy.yml"
    if not deploy.exists():
        return issues
    text = deploy.read_text(encoding="utf-8")
    if version and f"@{version}" not in text:
        issues.append(
            f"deploy.yml not pinned to {version} — run: shop upgrade {service_dir}"
        )
    expected = f"{org}/{platform}"
    if expected not in text:
        issues.append(
            f"deploy.yml platform repo is not {expected} — run: shop upgrade {service_dir}"
        )
    if re.search(r"@v0\.3\.[0-6]\b", text):
        issues.append("deploy.yml uses a removed platform tag (v0.3.0–v0.3.6)")
    return issues


def upgrade_service(service_dir: Path, cfg: dict | None = None) -> Path:
    cfg = cfg or load_config()
    upgrade_platform_pins(service_dir, cfg)
    broken = test_deploy_workflow(service_dir)
    if broken:
        raise RuntimeError(f"deploy.yml still has unreplaced tokens: {broken}")
    return service_dir.resolve()


def repair_service_tfvars(service_dir: Path, cfg: dict) -> bool:
    """Patch project_id, artifact_registry_repo, and region in infra/*.tfvars
    to match the current config.  Returns True if any file was changed."""
    replacements = {
        r'(project_id\s*=\s*")[^"]*(")'        : cfg.get("gcp_dev_project", ""),
        r'(artifact_registry_repo\s*=\s*")[^"]*(")'
                                                : cfg.get("artifact_registry_repo", "")
                                                  or cfg.get("ARTIFACT_REGISTRY_REPO", ""),
        r'(region\s*=\s*")[^"]*(")'             : cfg.get("gcp_region", ""),
    }
    prod_overrides = {
        r'(project_id\s*=\s*")[^"]*(")'        : cfg.get("gcp_prod_project", cfg.get("gcp_dev_project", "")),
    }

    changed = False
    for rel, overrides in (("infra/dev.tfvars", replacements), ("infra/prod.tfvars", {**replacements, **prod_overrides})):
        path = service_dir / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        updated = text
        for pattern, value in overrides.items():
            if value:
                updated = re.sub(pattern, lambda m, v=value: f"{m.group(1)}{v}{m.group(2)}", updated)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed = True
    return changed


def repair_scaffold_tokens(
    service_dir: Path,
    template: str,
    cfg: dict,
) -> Path:
    service_dir = service_dir.resolve()
    service_name = service_dir.name
    catalog = load_catalog()
    if template not in catalog:
        raise ValueError(f"Unknown template '{template}'")
    apply_scaffold_tokens(service_dir, service_name, cfg, catalog[template])
    upgrade_platform_pins(service_dir, cfg)
    broken = test_deploy_workflow(service_dir)
    if broken:
        raise RuntimeError(f"deploy.yml still has unreplaced tokens: {broken}")
    return service_dir


@dataclass
class ScaffoldResult:
    service_dir: Path
    service_name: str
    template: str
    health_check_path: str
    data_store_notes: list[str] | None = None


def scaffold(
    service_name: str,
    template: str,
    output_dir: Path,
    cfg: dict,
    service_config=None,
) -> ScaffoldResult:
    """Scaffold a service from a template.

    When ``service_config`` (a service_composer.ServiceConfig) is supplied and
    declares data stores, the base scaffold is extended with the store modules,
    connection layer, and Terraform wiring via data_store_generator.
    """
    catalog = load_catalog()
    if template not in catalog:
        names = ", ".join(catalog.keys())
        raise ValueError(f"Unknown template '{template}'. Available: {names}")

    err = validate_service_name(service_name)
    if err:
        raise ValueError(err)

    meta = catalog[template]
    template_dir = REPO_ROOT / "templates" / template
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")

    parent = output_dir.resolve()
    target = parent / service_name
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Target already exists: {target}")
    target.mkdir(parents=True, exist_ok=True)

    for item in template_dir.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    apply_scaffold_tokens(target, service_name, cfg, meta)
    upgrade_platform_pins(target, cfg)
    broken = test_deploy_workflow(target)
    if broken:
        raise RuntimeError(
            f"deploy.yml still has unreplaced template tokens: {broken}"
        )

    data_store_notes: list[str] = []
    if service_config is not None and getattr(service_config, "data_stores", None):
        import data_store_generator as dsg

        data_store_notes = dsg.apply_data_stores(
            target,
            service_config,
            github_org=_cfg_value(cfg, "github_org"),
            platform_repo=resolve_platform_repo(cfg, service_name),
            goldenpath_version=wd.resolve_goldenpath_version(REPO_ROOT),
        )

    if cmd_available("git"):
        run_cmd(["git", "init", "-q", "-b", "main"], cwd=target)
        run_cmd(["git", "add", "."], cwd=target)
        run_cmd(
            [
                "git",
                "commit",
                "-q",
                "-m",
                f"chore: scaffold {service_name} from golden path ({template})",
            ],
            cwd=target,
        )

    return ScaffoldResult(
        service_dir=target,
        service_name=service_name,
        template=template,
        health_check_path=str(meta.get("health_check_path", "/health")),
        data_store_notes=data_store_notes,
    )


# Runtime → nearest base template used as the source for custom scaffolds
_RUNTIME_BASE_TEMPLATE: dict[str, str] = {
    "python": "fastapi",
    "node": "express",
    "docker": "react-spa",
}


def generate_custom_template(
    name: str,
    runtime: str,
    port: int,
    health_path: str,
    output_dir: Path,
    cfg: dict,
) -> ScaffoldResult:
    """Generate a custom service scaffold from the closest matching base template.

    The base template is chosen by runtime (python→fastapi, node→express,
    docker→react-spa). Token replacement runs with the supplied port and
    health path, then a .goldenpath-custom-catalog.json entry is written
    next to the new service so the wizard can list it.
    """
    err = validate_service_name(name)
    if err:
        raise ValueError(err)

    runtime = runtime.lower().strip()
    base_template = _RUNTIME_BASE_TEMPLATE.get(runtime, "fastapi")

    catalog = load_catalog()
    if base_template not in catalog:
        base_template = next(iter(catalog))

    base_meta = dict(catalog[base_template])
    base_meta["app_runtime"] = runtime
    base_meta["container_port"] = port
    base_meta["health_check_path"] = health_path

    template_dir = REPO_ROOT / "templates" / base_template
    if not template_dir.exists():
        raise FileNotFoundError(f"Base template directory not found: {template_dir}")

    parent = output_dir.resolve()
    target = parent / name
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Target already exists and is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)

    for item in template_dir.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    # Apply tokens with the custom port/health values
    apply_scaffold_tokens(target, name, cfg, base_meta)
    upgrade_platform_pins(target, cfg)

    # Write a local catalog override so UIs can list this custom service
    custom_catalog_path = parent / ".goldenpath-custom-catalog.json"
    existing: dict = {}
    if custom_catalog_path.exists():
        try:
            existing = json.loads(custom_catalog_path.read_text())
        except json.JSONDecodeError:
            existing = {}
    existing[name] = {
        "description": f"Custom {runtime} service (port {port})",
        "app_runtime": runtime,
        "container_port": port,
        "health_check_path": health_path,
        "custom": True,
        "base_template": base_template,
    }
    custom_catalog_path.write_text(json.dumps(existing, indent=2))

    if cmd_available("git"):
        run_cmd(["git", "init", "-q", "-b", "main"], cwd=target)
        run_cmd(["git", "add", "."], cwd=target)
        run_cmd(
            ["git", "commit", "-q", "-m",
             f"chore: scaffold {name} (custom {runtime} from {base_template} base)"],
            cwd=target,
        )

    return ScaffoldResult(
        service_dir=target,
        service_name=name,
        template=base_template,
        health_check_path=health_path,
    )


# ── Data-store IAM permission gating ──────────────────────────────────────────

_PERM_PROBE_CACHE: dict[tuple, dict] = {}


def probe_data_store_permissions(
    project: str,
    store_ids: list[str],
    ip_mode: str = "public",
) -> dict[str, dict]:
    """Probe testIamPermissions for each data store's required permissions.

    Returns ``{store_id: {"granted": [...], "missing": [...],
    "missing_roles": [...], "unknown": bool}}``. When gcloud/project is
    unavailable the store is marked ``unknown`` (not blocked) so the UI can
    surface "could not verify" rather than a false negative.
    """
    import service_composer as sc

    report: dict[str, dict] = {}
    have_gcloud = bool(project) and cmd_available("gcloud")

    for sid in store_ids:
        perms = sc.data_store_permissions(sid, ip_mode)
        if not perms:
            report[sid] = {"granted": [], "missing": [], "missing_roles": [], "unknown": False}
            continue
        if not have_gcloud:
            report[sid] = {"granted": [], "missing": [], "missing_roles": [], "unknown": True}
            continue

        key = (project, sid, ip_mode)
        cached = _PERM_PROBE_CACHE.get(key)
        if cached is not None:
            report[sid] = cached
            continue

        res = run_cmd(
            [
                "gcloud",
                "projects",
                "test-iam-permissions",
                project,
                f"--permissions={','.join(perms)}",
                "--format=json",
            ],
            timeout=20,
        )
        if res.exit_code != 0:
            entry = {"granted": [], "missing": [], "missing_roles": [], "unknown": True, "error": res.stderr}
        else:
            try:
                granted = set(json.loads(res.stdout).get("permissions", [])) if res.stdout else set()
            except json.JSONDecodeError:
                granted = set()
            missing = [p for p in perms if p not in granted]
            roles = sorted({sc.role_for_permission(sid, p) for p in missing})
            entry = {
                "granted": sorted(granted),
                "missing": missing,
                "missing_roles": roles,
                "unknown": False,
            }
        _PERM_PROBE_CACHE[key] = entry
        report[sid] = entry

    return report


def _wif_sa_binding(policy_json: str, member: str, role: str) -> bool:
    if not policy_json:
        return False
    try:
        policy = json.loads(policy_json)
    except json.JSONDecodeError:
        return False
    for binding in policy.get("bindings", []):
        if binding.get("role") == role and member in binding.get("members", []):
            return True
    return False


def add_wif_trust(
    gcp_project: str,
    github_org: str,
    repo_name: str,
    on_step: Callable[[str], None] | None = None,
) -> None:
    def step(msg: str) -> None:
        print(msg, flush=True)
        if on_step:
            on_step(msg)

    # On Windows, skip the bash script — python3 is not reliably in Git Bash's PATH
    # and the pipe-based has_binding() check hangs. Use the pure-Python gcloud path.
    trust_script = REPO_ROOT / "scripts/lib/wif-trust-repo.sh"
    use_bash_script = trust_script.is_file() and sys.platform != "win32"
    if use_bash_script:
        cmd = [str(trust_script), gcp_project, github_org, repo_name]
        step("  Granting GitHub Actions access to GCP (IAM propagation takes ~2 min) ...")
        result = run_cmd_live(cmd, on_line=on_step)
        if result.exit_code != 0:
            detail = result.stderr or result.stdout or "unknown error"
            raise RuntimeError(f"WIF trust failed: {detail}")
        return

    # Pure-Python gcloud path (used on Windows and when bash script is absent)
    # run_cmd handles gcloud.cmd via cmd /c fallback on Windows automatically.
    sa = f"github-actions@{gcp_project}.iam.gserviceaccount.com"
    step("  Looking up GCP project number ...")
    num = run_cmd(
        [
            "gcloud",
            "projects",
            "describe",
            gcp_project,
            "--format=value(projectNumber)",
        ]
    )
    if num.exit_code != 0 or not num.stdout:
        raise RuntimeError(f"Could not get project number for {gcp_project}: {num.stderr or num.stdout}")
    step("  Finding workload identity pool ...")
    pool = run_cmd(
        [
            "gcloud",
            "iam",
            "workload-identity-pools",
            "list",
            f"--project={gcp_project}",
            "--location=global",
            "--format=value(name)",
        ]
    )
    if pool.exit_code != 0 or not pool.stdout:
        raise RuntimeError(f"No WIF pool in {gcp_project}: {pool.stderr or pool.stdout}")
    pool_id = re.sub(
        r".*/workloadIdentityPools/", "", pool.stdout.splitlines()[0]
    )
    member = (
        f"principalSet://iam.googleapis.com/projects/{num.stdout.strip()}"
        f"/locations/global/workloadIdentityPools/{pool_id}"
        f"/attribute.repository/{github_org}/{repo_name}"
    )
    for role in (
        "roles/iam.workloadIdentityUser",
        "roles/iam.serviceAccountTokenCreator",
    ):
        policy = run_cmd(
            [
                "gcloud",
                "iam",
                "service-accounts",
                "get-iam-policy",
                sa,
                f"--project={gcp_project}",
                "--format=json",
            ]
        )
        if _wif_sa_binding(policy.stdout, member, role):
            step(f"  {role} — already bound")
            continue
        step(f"  Binding {role} ...")
        bind = run_cmd(
            [
                "gcloud",
                "iam",
                "service-accounts",
                "add-iam-policy-binding",
                sa,
                f"--project={gcp_project}",
                f"--role={role}",
                f"--member={member}",
                "--quiet",
            ]
        )
        if bind.exit_code != 0:
            raise RuntimeError(f"WIF binding failed for {role}: {bind.stderr or bind.stdout}")
    step("  Waiting for IAM to propagate ...")
    for i in range(1, 10):
        time.sleep(5)
        step(f"  Propagation wait ... {i * 5}s / 45s")


def _platform_repo_visibility(github_org: str, platform_repo: str) -> str:
    full = f"{github_org}/{platform_repo}"
    result = run_cmd(
        ["gh", "repo", "view", full, "--json", "visibility", "-q", ".visibility"]
    )
    if result.exit_code != 0 or not result.stdout:
        return "PUBLIC"
    return result.stdout.strip().upper()


def _repo_create_visibility_flag(visibility: str) -> str:
    if visibility == "PRIVATE":
        return "--private"
    if visibility == "INTERNAL":
        return "--internal"
    return "--public"


def _service_project_from_tfvars(service_dir: Path) -> str | None:
    dev_tf = service_dir / "infra/dev.tfvars"
    if not dev_tf.exists():
        return None
    m = re.search(r'project_id\s*=\s*"([^"]+)"', dev_tf.read_text())
    return m.group(1) if m else None


def _latest_deploy_run(full_repo: str) -> dict | None:
    result = run_cmd(
        [
            "gh",
            "run",
            "list",
            "--repo",
            full_repo,
            "--workflow=deploy.yml",
            "--limit",
            "1",
            "--json",
            "databaseId,conclusion,status,event",
        ]
    )
    if result.exit_code != 0 or not result.stdout.strip():
        return None
    try:
        runs = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return runs[0] if runs else None


def _deploy_run_job_count(full_repo: str, run_id: str) -> int:
    result = run_cmd(
        [
            "gh",
            "api",
            f"repos/{full_repo}/actions/runs/{run_id}/jobs",
            "--jq",
            ".total_count",
        ]
    )
    if result.exit_code != 0 or not result.stdout.strip():
        return -1
    try:
        return int(result.stdout.strip())
    except ValueError:
        return -1


def _trigger_deploy_workflow(full_repo: str, environment: str = "dev") -> None:
    print(
        f"  Triggering deploy via workflow_dispatch ({environment}) "
        f"— first push on new repos often fails workflow validation"
    )
    run_cmd(
        [
            "gh",
            "workflow",
            "run",
            "deploy.yml",
            "--repo",
            full_repo,
            "-f",
            f"environment={environment}",
        ]
    )


def _is_workflow_startup_failure(full_repo: str, run: dict) -> bool:
    if run.get("conclusion") != "failure":
        return False
    run_id = str(run.get("databaseId", ""))
    if not run_id:
        return False
    job_count = _deploy_run_job_count(full_repo, run_id)
    return job_count == 0


def resolve_deploy_run_id(full_repo: str, initial_delay: int = 8) -> str | None:
    """Pick a deploy run to watch; dispatch if the push run failed at startup."""
    time.sleep(initial_delay)
    latest = _latest_deploy_run(full_repo)
    if not latest:
        _trigger_deploy_workflow(full_repo)
        time.sleep(5)
        latest = _latest_deploy_run(full_repo)
        return str(latest["databaseId"]) if latest else None

    if _is_workflow_startup_failure(full_repo, latest):
        _trigger_deploy_workflow(full_repo)
        time.sleep(5)
        latest = _latest_deploy_run(full_repo)
        return str(latest["databaseId"]) if latest else None

    return str(latest["databaseId"])


def wait_deploy_run(
    full_repo: str,
    initial_delay: int = 8,
    on_step: Callable[[str], None] | None = None,
) -> bool:
    def step(msg: str) -> None:
        print(msg, flush=True)
        if on_step:
            on_step(msg)

    step("  Waiting for workflow to start ...")
    run_id = resolve_deploy_run_id(full_repo, initial_delay=initial_delay)
    if not run_id:
        step("  No deploy workflow run found.")
        return False

    run_url = f"https://github.com/{full_repo}/actions/runs/{run_id}"
    step(f"  Deploy workflow: {run_url}")

    max_wait = 600
    poll_interval = 15
    elapsed = 0
    last_status = None

    while elapsed < max_wait:
        result = run_cmd(
            [
                "gh",
                "run",
                "view",
                run_id,
                "--repo",
                full_repo,
                "--json",
                "status,conclusion,name",
            ]
        )
        if result.exit_code == 0:
            try:
                data = json.loads(result.stdout)
                status_str = data.get("status", "")
                conclusion = data.get("conclusion")
                name = data.get("name", "deploy")
                if status_str != last_status:
                    step(f"  [{name}] {status_str} ...")
                    last_status = status_str
                if conclusion:
                    step(f"  [{name}] finished: {conclusion}")
                    return conclusion == "success"
            except (json.JSONDecodeError, KeyError):
                pass
        time.sleep(poll_interval)
        elapsed += poll_interval

    step(f"  Timed out after {max_wait}s — check: {run_url}")
    return False


@dataclass
class PublishResult:
    repo: str
    service_dir: Path
    gcp_project: str
    deploy_ok: bool | None = None


def publish(
    service_dir: Path,
    cfg: dict,
    wif_provider: str,
    wif_service_account: str,
    watch_deploy: bool = True,
    on_step: Callable[[str], None] | None = None,
) -> PublishResult:
    def step(msg: str) -> None:
        if on_step:
            on_step(msg)

    cfg = dict(cfg)
    wd.apply_enterprise_env_overrides(cfg, REPO_ROOT)

    service_dir = service_dir.resolve()
    service_name = service_dir.name
    full_repo = f"{cfg['github_org']}/{service_name}"
    gcp_project = cfg["gcp_dev_project"]

    verify_gh_auth_matches_org(cfg["github_org"])

    tf_project = _service_project_from_tfvars(service_dir)
    if tf_project and tf_project != gcp_project:
        step(
            f"[0/5] Updating service config from '{tf_project}' → '{gcp_project}' ..."
        )
        repair_service_tfvars(service_dir, cfg)
        run_cmd(
            ["git", "add", "infra/dev.tfvars", "infra/prod.tfvars"],
            cwd=service_dir,
        )
        run_cmd(
            ["git", "commit", "-m", f"chore: update project IDs to {gcp_project}"],
            cwd=service_dir,
        )

    upgrade_platform_pins(service_dir, cfg)

    broken = test_deploy_workflow(service_dir)
    if broken:
        template = get_service_template_hint(service_dir)
        if not template:
            raise RuntimeError(
                "deploy.yml has unreplaced {{tokens}} — re-scaffold or repair"
            )
        repair_scaffold_tokens(service_dir, template, cfg)

    if not (service_dir / ".git").exists():
        raise RuntimeError(f"Not a git repo: {service_dir}")

    # Ensure there is at least one commit (git init may have succeeded but
    # the auto-commit could have been skipped if git wasn't available earlier).
    log_check = run_cmd(["git", "log", "--oneline", "-1"], cwd=service_dir)
    if log_check.exit_code != 0 or not log_check.stdout.strip():
        step("[pre] No commits found — making initial commit ...")
        run_cmd(["git", "add", "-A"], cwd=service_dir)
        ic = run_cmd(
            ["git", "commit", "-m", f"chore: scaffold {service_name} from golden path"],
            cwd=service_dir,
        )
        if ic.exit_code != 0:
            raise RuntimeError(f"Initial commit failed: {ic.stderr or ic.stdout}")

    # Normalise to 'main'.  Use symbolic-ref (works on all git versions);
    # fall back to branch --show-current if symbolic-ref isn't available.
    ref = run_cmd(["git", "symbolic-ref", "--short", "HEAD"], cwd=service_dir)
    cur_branch = ref.stdout.strip() if ref.exit_code == 0 else ""
    if not cur_branch:
        show = run_cmd(["git", "branch", "--show-current"], cwd=service_dir)
        cur_branch = show.stdout.strip()
    if cur_branch and cur_branch != "main":
        run_cmd(["git", "branch", "-M", "main"], cwd=service_dir)

    if not wif_provider or not wif_service_account:
        raise RuntimeError(
            "WIF credentials missing — bootstrap first, then show WIF secrets"
        )

    platform_repo = resolve_platform_repo(cfg, service_name)
    visibility = _platform_repo_visibility(cfg["github_org"], platform_repo)

    remote = run_cmd(["git", "remote", "get-url", "origin"], cwd=service_dir)
    repo_existed = remote.exit_code == 0
    if not repo_existed:
        flag = _repo_create_visibility_flag(visibility)
        step(f"[1/5] Creating GitHub repo {full_repo} ({visibility}) ...")
        create = run_cmd(
            [
                "gh",
                "repo",
                "create",
                full_repo,
                flag,
                "--source=.",
                "--remote=origin",
            ],
            cwd=service_dir,
        )
        if create.exit_code != 0:
            raise RuntimeError("gh repo create failed — run: gh auth login")
    else:
        step(f"[1/5] GitHub repo exists: {full_repo}")

    step("[2/5] Setting GitHub secrets (WIF) ...")
    run_cmd(
        [
            "gh",
            "api",
            f"repos/{full_repo}",
            "-X",
            "PATCH",
            "-f",
            "default_branch=main",
        ]
    )
    s1 = run_cmd(
        [
            "gh",
            "secret",
            "set",
            "GCP_WIF_PROVIDER",
            "--body",
            wif_provider,
            "--repo",
            full_repo,
        ]
    )
    s2 = run_cmd(
        [
            "gh",
            "secret",
            "set",
            "GCP_WIF_SERVICE_ACCOUNT",
            "--body",
            wif_service_account,
            "--repo",
            full_repo,
        ]
    )
    if s1.exit_code != 0 or s2.exit_code != 0:
        raise RuntimeError("Failed to set GitHub secrets")

    if visibility == "PRIVATE":
        token = run_cmd(["gh", "auth", "token"])
        if not token.stdout:
            raise RuntimeError(
                "Platform repo is private — run 'gh auth login' for module token"
            )
        step("Setting GOLDENPATH_MODULE_TOKEN (private platform repo) ...")
        s3 = run_cmd(
            [
                "gh",
                "secret",
                "set",
                "GOLDENPATH_MODULE_TOKEN",
                "--body",
                token.stdout.strip(),
                "--repo",
                full_repo,
            ]
        )
        if s3.exit_code != 0:
            raise RuntimeError("Failed to set GOLDENPATH_MODULE_TOKEN")

    step(f"[3/5] Adding WIF trust for {full_repo} ...")
    add_wif_trust(gcp_project, cfg["github_org"], service_name, on_step=on_step)

    step("[4/5] Pushing main branch ...")
    push = run_cmd(["git", "push", "-u", "origin", "main"], cwd=service_dir)
    if push.exit_code != 0:
        detail = (push.stderr or push.stdout or "unknown error").strip()
        step(f"  Push output: {detail}")
        if "src refspec main does not match" in detail:
            # Branch still not called 'main' — force-rename whatever HEAD is
            step("[4/5] Branch name mismatch — renaming current branch to main ...")
            run_cmd(["git", "branch", "-M", "main"], cwd=service_dir)
            push = run_cmd(["git", "push", "-u", "origin", "main"], cwd=service_dir)
        elif "rejected" in detail or "fetch first" in detail or "non-fast-forward" in detail:
            # GitHub auto-initialises new repos with a README — remote has commits
            # that aren't in the local history.  Force-push is safe here because
            # the repo was just created and the scaffolded code is authoritative.
            step("[4/5] Remote has diverged history (GitHub auto-init) — force-pushing ...")
            push = run_cmd(
                ["git", "push", "-u", "origin", "main", "--force-with-lease"],
                cwd=service_dir,
            )
        if push.exit_code != 0:
            detail = (push.stderr or push.stdout or "unknown error").strip()
            raise RuntimeError(f"git push failed: {detail}")

    deploy_ok: bool | None = None
    if watch_deploy:
        step("[5/5] Waiting for deploy workflow ...")
        deploy_ok = wait_deploy_run(full_repo, on_step=on_step)
        if not deploy_ok:
            latest = _latest_deploy_run(full_repo)
            if latest and latest.get("conclusion") == "failure":
                failed_id = str(latest.get("databaseId", ""))
                if failed_id and not _is_workflow_startup_failure(full_repo, latest):
                    step("  Retrying failed workflow run ...")
                    rerun = run_cmd(
                        [
                            "gh",
                            "run",
                            "rerun",
                            failed_id,
                            "--repo",
                            full_repo,
                        ]
                    )
                    if rerun.exit_code == 0:
                        deploy_ok = wait_deploy_run(full_repo, initial_delay=10, on_step=on_step)
            if not deploy_ok:
                step("  Triggering deploy workflow manually ...")
                _trigger_deploy_workflow(full_repo)
                deploy_ok = wait_deploy_run(full_repo, initial_delay=10, on_step=on_step)

        if not deploy_ok:
            step("GitHub deploy failed — attempting local Terraform recovery ...")
            if recover_deploy_local(service_dir):
                deploy_ok = True

    return PublishResult(
        repo=full_repo,
        service_dir=service_dir,
        gcp_project=gcp_project,
        deploy_ok=deploy_ok,
    )


def service_doctor(service_dir: Path, cfg: dict) -> list[str]:
    issues: list[str] = []
    service_dir = service_dir.resolve()
    service_name = service_dir.name
    full_repo = f"{cfg['github_org']}/{service_name}"

    branch = run_cmd(["git", "branch", "--show-current"], cwd=service_dir)
    if branch.stdout.strip() != "main":
        issues.append(
            f"Local branch is '{branch.stdout.strip()}' — run: git branch -M main"
        )

    tf_project = _service_project_from_tfvars(service_dir)
    if tf_project != cfg["gcp_dev_project"]:
        issues.append(
            f"project_id mismatch: tfvars='{tf_project}' "
            f"config='{cfg['gcp_dev_project']}'"
        )

    default_branch = run_cmd(
        ["gh", "api", f"repos/{full_repo}", "--jq", ".default_branch"]
    )
    if default_branch.stdout and default_branch.stdout.strip() != "main":
        issues.append(
            f"GitHub default branch is '{default_branch.stdout.strip()}' "
            "(should be main)"
        )

    secrets = run_cmd(["gh", "secret", "list", "--repo", full_repo])
    for secret in ("GCP_WIF_PROVIDER", "GCP_WIF_SERVICE_ACCOUNT"):
        if secret not in secrets.stdout:
            issues.append(f"Missing GitHub secret: {secret}")

    broken = test_deploy_workflow(service_dir)
    if broken:
        issues.append(
            "deploy.yml has unreplaced template tokens ({{...}}) — "
            "publish will auto-repair, or re-run scaffold"
        )

    platform_issue = check_deploy_platform_repo(service_dir, cfg)
    if platform_issue:
        issues.append(platform_issue)

    issues.extend(check_deploy_pin_issues(service_dir, cfg))

    if cmd_available("gh"):
        try:
            verify_gh_auth_matches_org(cfg["github_org"])
        except RuntimeError as exc:
            issues.append(str(exc))

    return issues


def get_service_health_paths(service_dir: Path | None) -> list[str]:
    paths: list[str] = []
    if service_dir and service_dir.exists():
        template = get_service_template_hint(service_dir)
        if template:
            catalog = load_catalog()
            if template in catalog:
                paths.append(str(catalog[template]["health_check_path"]))
        deploy = service_dir / ".github/workflows/deploy.yml"
        if deploy.exists():
            m = re.search(
                r'health[_-]?check[_-]?path["\s:=]+([/\w-]+)',
                deploy.read_text(),
            )
            if m and m.group(1) not in paths:
                paths.append(m.group(1))
    for fallback in ("/api/health", "/health", "/_stcore/health"):
        if fallback not in paths:
            paths.append(fallback)
    return paths


@dataclass
class VerifyResult:
    cloud_run_service: str
    url: str | None = None
    health_ok: bool = False
    health_path: str | None = None
    status_code: int | None = None
    response_preview: str = ""
    error: str | None = None


def verify_deployment(
    cloud_run_service: str,
    cfg: dict,
    service_dir: Path | None = None,
    max_attempts: int = 8,
    retry_delay: int = 8,
    quiet: bool = False,
) -> VerifyResult:
    project = cfg["gcp_project"]
    region = cfg["gcp_region"]
    paths = (
        get_service_health_paths(service_dir)
        if service_dir
        else ["/api/health", "/health", "/_stcore/health"]
    )

    url: str | None = None
    for attempt in range(1, max_attempts + 1):
        if not quiet and attempt > 1:
            print(
                f"  Waiting for Cloud Run ({attempt}/{max_attempts})...",
                file=sys.stderr,
            )
        result = run_cmd(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                cloud_run_service,
                f"--project={project}",
                f"--region={region}",
                "--format=value(status.url)",
            ]
        )
        if result.exit_code == 0 and result.stdout:
            url = result.stdout.strip()
            break
        if attempt < max_attempts:
            time.sleep(retry_delay)

    if not url:
        return VerifyResult(
            cloud_run_service=cloud_run_service,
            error=(
                f"Service '{cloud_run_service}' not found in {project} ({region})"
            ),
        )

    health_ok = False
    health_path: str | None = None
    status_code: int | None = None
    preview = ""

    for attempt in range(1, max_attempts + 1):
        for path in paths:
            try:
                req = urllib.request.Request(
                    f"{url}{path}",
                    method="GET",
                    headers={"User-Agent": "goldenpath-setup/1.0"},
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    health_ok = True
                    health_path = path
                    status_code = resp.status
                    body = resp.read(200).decode("utf-8", errors="replace")
                    preview = body[:200]
                    break
            except (urllib.error.URLError, TimeoutError, OSError):
                if not quiet:
                    print(f"  Health {path} → not ready yet", file=sys.stderr)
        if health_ok:
            break
        if attempt < max_attempts:
            time.sleep(retry_delay)

    return VerifyResult(
        cloud_run_service=cloud_run_service,
        url=url,
        health_ok=health_ok,
        health_path=health_path,
        status_code=status_code,
        response_preview=preview,
        error=None if health_ok else f"No health endpoint responded on {url}",
    )


def show_deployment_result(
    verify: VerifyResult,
    repo: str = "",
    verbose: bool = False,
) -> None:
    print()
    print("  ┌─ Deployment summary ──────────────────────────────────────┐")
    if repo:
        print(f"  │  GitHub repo     https://github.com/{repo}")
        print(f"  │  Actions         https://github.com/{repo}/actions")
    print(f"  │  Cloud Run       {verify.cloud_run_service}")
    if verify.url:
        print(f"  │  Live URL        {verify.url}")
    else:
        print("  │  Live URL        (not found yet)")
    if verify.health_ok:
        print(
            f"  │  Health          {verify.health_path} → "
            f"HTTP {verify.status_code}"
        )
        if verbose and verify.response_preview:
            print(f"  │  Response        {verify.response_preview}")
    elif verify.url:
        print("  │  Health          not responding yet — try menu 8 in a minute")
    print("  └───────────────────────────────────────────────────────────┘")
    print()
    if verify.url and verify.health_ok:
        print("  Open your app:")
        print(f"    {verify.url}")
        print()


def generate_mcp_config(cfg: dict) -> Path:
    mcp_dir = REPO_ROOT / "mcp"
    venv_python = mcp_dir / ".venv/bin/python"
    if sys.platform == "win32":
        venv_python = mcp_dir / ".venv/Scripts/python.exe"
    if not venv_python.exists():
        if not cmd_available("python3"):
            raise RuntimeError("python3 required to create MCP venv")
        run_cmd(["python3", "-m", "venv", str(mcp_dir / ".venv")])
        pip = (
            mcp_dir / ".venv/Scripts/pip.exe"
            if sys.platform == "win32"
            else mcp_dir / ".venv/bin/pip"
        )
        run_cmd([str(pip), "install", "-r", str(mcp_dir / "requirements.txt")])

    out_path = mcp_dir / "claude-mcp.generated.json"
    goldenpath_version = wd.resolve_goldenpath_version(REPO_ROOT)
    mcp_cfg = {
        "mcpServers": {
            "goldenpath-local": {
                "command": str(venv_python),
                "args": ["-m", "goldenpath_mcp"],
                "env": {
                    "GOLDENPATH_ROOT": str(REPO_ROOT),
                    "GOLDENPATH_CHANNEL": "stable",
                    "GOLDENPATH_VERSION": goldenpath_version,
                    "GCP_PROJECT": cfg["gcp_project"],
                    "GCP_REGION": cfg["gcp_region"],
                },
            }
        }
    }
    out_path.write_text(json.dumps(mcp_cfg, indent=2))
    return out_path
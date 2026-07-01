#!/usr/bin/env python3
"""Golden Path GCP — Streamlit Setup UI
Web-based mirror of scripts/setup/goldenpath-setup.ps1

Run (recommended):
  ./scripts/goldenpath-setup-ui.sh

Or directly:
  streamlit run scripts/setup/goldenpath_setup_app.py

Docs:
  docs/getting-started/09-streamlit-setup-ui.md
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import sys

import streamlit as st

# ── Constants ──────────────────────────────────────────────────────────────────


def _find_repo_root() -> Path:
    """Walk upward from this file to locate the repository root.

    Looks for a distinctive file (templates/catalog.json) or .git directory.
    This makes the app relocatable (e.g. when under scripts/setup/).
    """
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
    # Fallback when the file lives in scripts/setup/
    p = Path(__file__).resolve()
    for _ in range(3):
        if (p / "templates").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent.parent


REPO_ROOT = _find_repo_root()
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "setup"))
import wizard_defaults as wd  # noqa: E402
import goldenpath_ops as ops  # noqa: E402
import service_composer as sc  # noqa: E402

CONFIG_PATH = REPO_ROOT / ".goldenpath-setup.local.json"
BOOTSTRAP_DIR = REPO_ROOT / "platform/bootstrap"
ENTERPRISE_ENV = REPO_ROOT / "config" / "enterprise.env"
DEFAULT_TEMPLATES = [
    "nextjs",
    "fastapi",
    "streamlit",
    "express",
    "react-spa",
    "svelte-spa",
]
DEFAULT_SCAFFOLD_OUTPUT = REPO_ROOT.parent

SETUP_STEPS = [
    ("settings", "Settings", "Settings"),
    ("prerequisites", "Prerequisites", "Prerequisites"),
    ("bootstrap", "Bootstrap", "Bootstrap"),
    ("wif", "WIF Secrets", "WIF Secrets"),
    ("scaffold", "Scaffold", "Scaffold"),
    ("publish", "Publish", "Publish"),
    ("verify", "Verify", "Verify"),
]

NAV_GROUPS = {
    "Get Started": ["Dashboard", "Guided Wizard", "Settings", "Prerequisites"],
    "Deploy": ["Bootstrap", "Scaffold", "Publish", "Verify"],
    "Manage": ["Doctor", "WIF Secrets", "MCP Config", "Teardown", "Fresh Start"],
}

# Plain-English labels for each page shown in the navigation dropdown
PAGE_LABELS: dict[str, str] = {
    "Dashboard": "Dashboard",
    "Guided Wizard": "Guided Wizard",
    "Settings": "Settings",
    "Prerequisites": "Prerequisites",
    "Bootstrap": "Set up Google Cloud (first time)",
    "WIF Secrets": "Connect GitHub to Google Cloud",
    "Scaffold": "Create a new service",
    "Publish": "Deploy your service",
    "Verify": "Check if service is live",
    "Doctor": "Diagnose a broken deploy",
    "MCP Config": "MCP Config",
    "Teardown": "Teardown",
    "Fresh Start": "Fresh Start",
}

NAV_ICONS: dict[str, str] = {
    "Dashboard": "🏠",
    "Guided Wizard": "🧙",
    "Settings": "⚙️",
    "Prerequisites": "🔧",
    "Bootstrap": "☁️",
    "Scaffold": "🏗️",
    "Publish": "🚀",
    "Verify": "🔍",
    "Doctor": "🩺",
    "WIF Secrets": "🔑",
    "MCP Config": "🤖",
    "Teardown": "🗑️",
    "Fresh Start": "↺",
}

STEP_DESCRIPTIONS: dict[str, str] = {
    "settings": "Choose your Google Cloud project and GitHub organization.",
    "prerequisites": "Install the required command-line tools.",
    "bootstrap": "Create your Google Cloud infrastructure (one-time setup).",
    "wif": "Connect GitHub to Google Cloud so deploys happen automatically.",
    "scaffold": "Generate your service from a ready-to-deploy template.",
    "publish": "Push your code to GitHub and trigger the first deploy.",
    "verify": "Confirm your service is live on the internet.",
}

STEP_ICONS: dict[str, str] = {
    "settings": "⚙️",
    "prerequisites": "🔧",
    "bootstrap": "☁️",
    "wif": "🔑",
    "scaffold": "🏗️",
    "publish": "🚀",
    "verify": "✅",
}

# Pages that require bootstrap-level IAM (Owner / Project Creator)
_BOOTSTRAP_PAGES = {"Bootstrap"}
# Pages that require at least deploy-level IAM (run.admin + WIF admin)
_DEPLOY_PAGES = {"Scaffold", "Publish", "WIF Secrets"}

PAGES = [page for group in NAV_GROUPS.values() for page in group]

SETUP_DIR = Path(__file__).resolve().parent
SPARQ_LOGO_PATH = SETUP_DIR / "assets" / "sparq-logo.svg"


@lru_cache(maxsize=1)
def sparq_logo_svg() -> str:
    """Sparq wordmark from https://www.teamsparq.com/ (homepage header SVG)."""
    if not SPARQ_LOGO_PATH.is_file():
        return ""
    svg = SPARQ_LOGO_PATH.read_text(encoding="utf-8")
    return svg.replace('width="5em"', "").replace('height="1.875em"', "")


def sparq_logo_html(*, variant: str = "sidebar") -> str:
    svg = sparq_logo_svg()
    if not svg:
        return ""
    return f'<span class="gp-sparq-logo gp-sparq-logo-{variant}" aria-hidden="true">{svg}</span>'


def sunshine_icon_html() -> str:
    return (
        '<span class="gp-sunshine-icon" aria-hidden="true">'
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="12" cy="12" r="4.5" fill="currentColor"/>'
        '<path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22'
        'M4.93 4.93l1.77 1.77M17.3 17.3l1.77 1.77'
        'M4.93 19.07l1.77-1.77M17.3 6.7l1.77-1.77"'
        ' stroke="currentColor" stroke-width="1.75" stroke-linecap="round" fill="none"/>'
        "</svg></span>"
    )


def golden_path_title_html(*, variant: str = "sidebar") -> str:
    logo = sparq_logo_html(variant=variant)
    sun = sunshine_icon_html()
    return (
        f'<span class="gp-title-with-logo">{logo}'
        f'<span class="gp-golden-path-text">{sun}<span>Golden Path</span></span>'
        f"</span>"
    )


def sidebar_brand_html() -> str:
    return f"""
<div class="gp-glass gp-sidebar-brand">
  <h2 class="gp-brand-title">{golden_path_title_html(variant="sidebar")}</h2>
  <p>GCP setup wizard</p>
</div>
    """


# ── Theme ─────────────────────────────────────────────────────────────────────


def inject_theme() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --gp-text: #0f172a;
    --gp-muted: #5b6b82;
    --gp-accent: #5b6af7;
    --gp-accent-hover: #4a58e8;
    --gp-success: #0d9b76;
    --gp-radius: 16px;
    --gp-glass: rgba(255, 255, 255, 0.58);
    --gp-glass-strong: rgba(255, 255, 255, 0.78);
    --gp-glass-border: rgba(255, 255, 255, 0.72);
    --gp-glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.08);
    --gp-blur: blur(18px) saturate(165%);
    --gp-header-height: 3.75rem;
    --gp-content-top: 6rem;
    --gp-sidebar-top: calc(var(--gp-header-height) + var(--gp-content-top));
    --gp-content-pad-x: 1rem;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background-color: #e8edf8;
    background-image:
        radial-gradient(ellipse 90% 60% at 10% 15%, rgba(91, 106, 247, 0.22), transparent 55%),
        radial-gradient(ellipse 70% 50% at 90% 10%, rgba(56, 189, 198, 0.16), transparent 50%),
        radial-gradient(ellipse 80% 55% at 50% 95%, rgba(167, 139, 250, 0.14), transparent 55%),
        linear-gradient(160deg, #eef2fb 0%, #e4eaf6 45%, #edf1f9 100%);
}

footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

header[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.12) !important;
    backdrop-filter: blur(28px) saturate(190%);
    -webkit-backdrop-filter: blur(28px) saturate(190%);
    border-bottom: 0.5px solid rgba(255, 255, 255, 0.28);
    box-shadow: none;
}

header[data-testid="stHeader"] [data-testid="stToolbar"],
header[data-testid="stHeader"] [data-testid="stToolbarActions"] {
    background: transparent !important;
    backdrop-filter: none;
}

header[data-testid="stHeader"] button {
    background: rgba(255, 255, 255, 0.22) !important;
    backdrop-filter: blur(14px) saturate(160%);
    -webkit-backdrop-filter: blur(14px) saturate(160%);
    border: 0.5px solid rgba(255, 255, 255, 0.38) !important;
    box-shadow: none !important;
    color: var(--gp-text) !important;
}

header[data-testid="stHeader"] button:hover {
    background: rgba(255, 255, 255, 0.42) !important;
}

[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 0 !important;
}

[data-testid="stSidebarHeader"] {
    position: absolute;
    top: calc(var(--gp-header-height) + 0.65rem);
    right: 0.65rem;
    left: 0;
    height: auto !important;
    margin: 0 !important;
    z-index: 30;
    justify-content: flex-end !important;
    pointer-events: none;
}

[data-testid="stLogoSpacer"] {
    display: none !important;
}

[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarHeader"] button {
    pointer-events: auto;
}

[data-testid="stSidebar"][aria-expanded="true"] {
    background: rgba(255, 255, 255, 0.42) !important;
    backdrop-filter: var(--gp-blur);
    -webkit-backdrop-filter: var(--gp-blur);
    border-right: 1px solid rgba(255, 255, 255, 0.5);
    width: 17rem !important;
    min-width: 17rem !important;
    max-width: 17rem !important;
}

[data-testid="stSidebar"][aria-expanded="false"] {
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    border-right: none !important;
    overflow: hidden !important;
    pointer-events: none !important;
}

section[data-testid="stMain"] {
    flex: 1 1 auto !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
}

[data-testid="stSidebar"] .stCaption { color: var(--gp-muted); }

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    display: flex !important;
    flex-direction: column !important;
    min-height: calc(100vh - var(--gp-sidebar-top));
    padding-top: var(--gp-sidebar-top) !important;
    padding-bottom: 1rem !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}


section[data-testid="stMain"] > div {
    padding-top: 0 !important;
}

[data-testid="stMainBlockContainer"],
.main .block-container,
section[data-testid="stMain"] .block-container {
    padding-top: var(--gp-content-top) !important;
    padding-left: var(--gp-content-pad-x) !important;
    padding-right: var(--gp-content-pad-x) !important;
    padding-bottom: 1.25rem !important;
    max-width: 100%;
}

div[data-testid="stVerticalBlock"] > div {
    gap: 0.45rem;
}

[data-testid="column"] {
    padding-left: 0.35rem !important;
    padding-right: 0.35rem !important;
}

.gp-glass {
    background: var(--gp-glass);
    backdrop-filter: var(--gp-blur);
    -webkit-backdrop-filter: var(--gp-blur);
    border: 1px solid var(--gp-glass-border);
    border-radius: var(--gp-radius);
    box-shadow: var(--gp-glass-shadow);
}

.gp-sidebar-brand {
    margin: 0 0 0.65rem;
    padding: 0.75rem 0.85rem;
}

.gp-sidebar-brand .gp-brand-title {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--gp-text);
    line-height: 1.15;
}

.gp-sidebar-brand p {
    margin: 0.15rem 0 0;
    font-size: 0.75rem;
    color: var(--gp-muted);
}

.gp-title-with-logo {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
}

.gp-golden-path-text {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
}

.gp-sparq-logo {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    color: var(--gp-text);
    line-height: 0;
}

.gp-sparq-logo svg {
    display: block;
    width: auto;
    height: 1em;
}

.gp-sunshine-icon {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    color: #f59e0b;
    line-height: 0;
}

.gp-sunshine-icon svg {
    display: block;
    width: 1em;
    height: 1em;
}

.gp-env {
    padding: 0.6rem 0.7rem;
    margin-bottom: 0.6rem;
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.2rem 0.55rem;
    font-size: 0.74rem;
    line-height: 1.35;
    color: var(--gp-text);
}

.gp-env dt {
    color: var(--gp-muted);
    font-weight: 600;
    margin: 0;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.gp-env dd {
    margin: 0;
    font-weight: 600;
    word-break: break-word;
}

.gp-pill {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    backdrop-filter: blur(8px);
}

.gp-pill-ok {
    background: rgba(16, 185, 129, 0.18);
    color: #047857;
    border: 1px solid rgba(16, 185, 129, 0.25);
}

.gp-pill-warn {
    background: rgba(251, 146, 60, 0.18);
    color: #c2410c;
    border: 1px solid rgba(251, 146, 60, 0.28);
}

.gp-glass-hero {
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
}

.gp-hero-body { flex: 1; min-width: 12rem; }

.gp-page-eyebrow {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--gp-accent);
    margin: 0 0 0.35rem;
}

.gp-page-eyebrow .gp-sparq-logo {
    color: var(--gp-text);
}

.gp-hero-title {
    margin: 0;
    font-size: 1.12rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--gp-text);
    line-height: 1.15;
}

.gp-hero-sub {
    margin: 0.25rem 0 0;
    font-size: 0.84rem;
    color: var(--gp-muted);
    line-height: 1.4;
}

.gp-callout {
    padding: 0.55rem 0.85rem;
    margin: 0;
    background: rgba(91, 106, 247, 0.12);
    border: 1px solid rgba(91, 106, 247, 0.22);
    flex: 1;
    min-width: 14rem;
    max-width: 28rem;
}

.gp-callout strong { color: var(--gp-text); }

.gp-callout p {
    margin: 0.35rem 0 0;
    color: var(--gp-muted);
    font-size: 0.92rem;
}

[data-testid="stMetric"] {
    background: var(--gp-glass-strong) !important;
    backdrop-filter: var(--gp-blur);
    -webkit-backdrop-filter: var(--gp-blur);
    border: 1px solid var(--gp-glass-border) !important;
    border-radius: 12px !important;
    padding: 0.55rem 0.75rem !important;
    box-shadow: var(--gp-glass-shadow);
}

[data-testid="stMetricLabel"] { font-size: 0.72rem !important; }
[data-testid="stMetricValue"] { font-size: 1.1rem !important; }

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--gp-glass) !important;
    backdrop-filter: var(--gp-blur);
    -webkit-backdrop-filter: var(--gp-blur);
    border: 1px solid var(--gp-glass-border) !important;
    border-radius: 12px !important;
    box-shadow: var(--gp-glass-shadow);
    padding: 0.55rem 0.75rem 0.65rem !important;
}

.gp-section-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--gp-text);
    margin: 0 0 0.35rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.gp-step-line {
    font-size: 0.84rem;
    line-height: 1.35;
    margin: 0;
    padding: 0.12rem 0;
}

.stButton {
    margin-bottom: 0.2rem;
}

.stButton > button {
    position: relative;
    overflow: hidden;
    border-radius: 14px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.01em;
    padding: 0.58rem 1.2rem !important;
    min-height: 2.7rem;
    line-height: 1.25 !important;
    background: rgba(255, 255, 255, 0.68) !important;
    backdrop-filter: blur(14px) saturate(165%) !important;
    -webkit-backdrop-filter: blur(14px) saturate(165%) !important;
    border: 1px solid rgba(255, 255, 255, 0.82) !important;
    color: var(--gp-text) !important;
    box-shadow:
        0 1px 2px rgba(15, 23, 42, 0.05),
        0 4px 16px rgba(31, 38, 135, 0.07) !important;
    transition:
        background 0.2s ease,
        border-color 0.2s ease,
        box-shadow 0.2s ease,
        transform 0.16s ease !important;
}

.stButton > button::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: linear-gradient(
        180deg,
        rgba(255, 255, 255, 0.42) 0%,
        rgba(255, 255, 255, 0) 52%
    );
    pointer-events: none;
}

.stButton > button p {
    position: relative;
    z-index: 1;
    margin: 0 !important;
    font-weight: 600 !important;
    font-size: inherit !important;
    line-height: inherit !important;
}

.stButton > button:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.94) !important;
    border-color: rgba(91, 106, 247, 0.34) !important;
    color: var(--gp-text) !important;
    box-shadow:
        0 2px 6px rgba(15, 23, 42, 0.06),
        0 10px 26px rgba(91, 106, 247, 0.14) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active:not(:disabled) {
    transform: translateY(0) !important;
    box-shadow: 0 2px 10px rgba(91, 106, 247, 0.16) !important;
}

.stButton > button:focus {
    outline: none !important;
    box-shadow:
        0 0 0 3px rgba(91, 106, 247, 0.22),
        0 4px 16px rgba(31, 38, 135, 0.08) !important;
}

.stButton > button:disabled {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
    transform: none !important;
    background: rgba(255, 255, 255, 0.42) !important;
    border-color: rgba(255, 255, 255, 0.55) !important;
    box-shadow: none !important;
    color: var(--gp-muted) !important;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #6f7cfa 0%, #5b6af7 52%, #4f5fe8 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
    color: #fff !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.24),
        0 6px 22px rgba(91, 106, 247, 0.36) !important;
}

.stButton > button[kind="primary"]::before,
.stButton > button[data-testid="baseButton-primary"]::before {
    background: linear-gradient(
        180deg,
        rgba(255, 255, 255, 0.22) 0%,
        rgba(255, 255, 255, 0) 55%
    );
}

.stButton > button[kind="primary"]:hover:not(:disabled),
.stButton > button[data-testid="baseButton-primary"]:hover:not(:disabled) {
    background: linear-gradient(135deg, #5b6af7 0%, #4f5ee8 52%, #4a58e8 100%) !important;
    border-color: rgba(255, 255, 255, 0.48) !important;
    color: #fff !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.3),
        0 10px 30px rgba(91, 106, 247, 0.44) !important;
}

.stButton > button[kind="primary"]:disabled,
.stButton > button[data-testid="baseButton-primary"]:disabled {
    background: linear-gradient(
        135deg,
        rgba(111, 124, 250, 0.45) 0%,
        rgba(91, 106, 247, 0.45) 100%
    ) !important;
    color: rgba(255, 255, 255, 0.82) !important;
}

[data-testid="column"] .stButton > button {
    padding: 0.5rem 0.7rem !important;
    font-size: 0.8rem !important;
    min-height: 2.45rem;
    border-radius: 12px !important;
}

.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.62) !important;
    backdrop-filter: blur(8px);
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.7) !important;
}

[data-testid="stAlert"] {
    border-radius: 12px;
    backdrop-filter: blur(8px);
}

div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    row-gap: 0.5rem !important;
}

div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    flex: 1 1 12rem !important;
    min-width: min(100%, 12rem) !important;
}

@media (max-width: 768px) {
    :root {
        --gp-content-pad-x: 0.75rem;
    }

    [data-testid="stMainBlockContainer"],
    .main .block-container,
    section[data-testid="stMain"] .block-container {
        padding-left: var(--gp-content-pad-x) !important;
        padding-right: var(--gp-content-pad-x) !important;
    }

    [data-testid="stSidebar"][aria-expanded="true"] {
        width: min(17rem, 92vw) !important;
        min-width: min(17rem, 92vw) !important;
        max-width: 92vw !important;
    }

    [data-testid="stSidebar"][aria-expanded="false"] {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }

    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }

    .gp-hero-title { font-size: 1.05rem; }
    .gp-glass-hero { flex-direction: column; align-items: flex-start; }
}

/* ── Sidebar navigation ──────────────────────────────────────────────────── */

.gp-nav-group {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--gp-muted);
    padding: 0.6rem 0.65rem 0.15rem;
    margin-top: 0.2rem;
    pointer-events: none;
}

/* Active page indicator — styled div, not a button */
.gp-nav-active {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.38rem 0.7rem;
    margin: 0.05rem 0;
    background: rgba(91, 106, 247, 0.1);
    border-left: 3px solid var(--gp-accent);
    border-radius: 0 8px 8px 0;
    color: var(--gp-accent);
    font-size: 0.83rem;
    font-weight: 600;
    cursor: default;
    user-select: none;
}

/* Nav buttons — override global button styles within sidebar */
[data-testid="stSidebar"] .stButton > button {
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 0.38rem 0.7rem !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    min-height: 2rem !important;
    border-radius: 8px !important;
    background: transparent !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    border: none !important;
    box-shadow: none !important;
    color: var(--gp-text) !important;
    transform: none !important;
    margin-bottom: 0.05rem !important;
}

[data-testid="stSidebar"] .stButton > button:hover:not(:disabled) {
    background: rgba(91, 106, 247, 0.07) !important;
    color: var(--gp-accent) !important;
    border: none !important;
    box-shadow: none !important;
    transform: none !important;
}

[data-testid="stSidebar"] .stButton > button::before {
    display: none !important;
}

[data-testid="stSidebar"] .stButton {
    margin-bottom: 0 !important;
}

/* Compact status strip at the bottom of the sidebar */
.gp-status-strip {
    font-size: 0.72rem;
    line-height: 1.7;
    color: var(--gp-muted);
    padding: 0.4rem 0.65rem 0.2rem;
}

.gp-status-strip strong {
    color: var(--gp-text);
    font-weight: 600;
}

/* ── Dashboard step cards ─────────────────────────────────────────────────── */

.gp-step-card {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    padding: 0.7rem 0.9rem;
    border-radius: 10px;
    background: var(--gp-glass-strong);
    backdrop-filter: var(--gp-blur);
    -webkit-backdrop-filter: var(--gp-blur);
    border: 1px solid var(--gp-glass-border);
    border-left: 3px solid transparent;
    margin-bottom: 0.4rem;
}

.gp-step-card-done {
    border-left-color: #0d9b76;
    opacity: 0.8;
}

.gp-step-card-next {
    border-left-color: var(--gp-accent);
    background: rgba(255, 255, 255, 0.88);
    box-shadow: 0 4px 18px rgba(91, 106, 247, 0.12);
}

.gp-step-icon {
    font-size: 1.2rem;
    flex-shrink: 0;
    margin-top: 0.1rem;
    line-height: 1;
}

.gp-step-body { flex: 1; }

.gp-step-body h4 {
    margin: 0;
    font-size: 0.87rem;
    font-weight: 600;
    color: var(--gp-text);
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.gp-step-body p {
    margin: 0.1rem 0 0;
    font-size: 0.76rem;
    color: var(--gp-muted);
    line-height: 1.35;
}

.gp-step-badge-done {
    font-size: 0.65rem;
    font-weight: 700;
    color: #047857;
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.22);
    border-radius: 999px;
    padding: 0.1rem 0.45rem;
    letter-spacing: 0.04em;
}

.gp-step-badge-next {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--gp-accent);
    background: rgba(91, 106, 247, 0.1);
    border: 1px solid rgba(91, 106, 247, 0.22);
    border-radius: 999px;
    padding: 0.1rem 0.45rem;
    letter-spacing: 0.04em;
}

/* ── Guided Wizard stepper ───────────────────────────────────────────────── */

.gp-wizard-stepper {
    display: flex;
    align-items: flex-start;
    margin: 0.5rem 0 1.25rem;
    overflow-x: auto;
    padding-bottom: 0.25rem;
}

.gp-wizard-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;
    flex: 1;
    min-width: 3.5rem;
    position: relative;
}

.gp-wizard-step:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 1rem;
    left: calc(50% + 1.05rem);
    right: calc(-50% + 1.05rem);
    height: 2px;
    background: rgba(91, 106, 247, 0.12);
    z-index: 0;
}

.gp-wizard-step.gp-wiz-done:not(:last-child)::after {
    background: var(--gp-accent);
}

.gp-wiz-bubble {
    width: 2.1rem;
    height: 2.1rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.78rem;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.55);
    border: 2px solid rgba(91, 106, 247, 0.18);
    color: var(--gp-muted);
    position: relative;
    z-index: 1;
}

.gp-wiz-done .gp-wiz-bubble {
    background: var(--gp-accent);
    border-color: var(--gp-accent);
    color: white;
}

.gp-wiz-current .gp-wiz-bubble {
    background: white;
    border-color: var(--gp-accent);
    color: var(--gp-accent);
    box-shadow: 0 0 0 4px rgba(91, 106, 247, 0.15);
}

.gp-wiz-label {
    font-size: 0.6rem;
    font-weight: 500;
    color: var(--gp-muted);
    text-align: center;
    line-height: 1.25;
    max-width: 4rem;
}

.gp-wiz-current .gp-wiz-label {
    color: var(--gp-accent);
    font-weight: 700;
}

.gp-wiz-done .gp-wiz-label {
    color: var(--gp-text);
    font-weight: 600;
}
</style>
        """,
        unsafe_allow_html=True,
    )


# ── GCP IAM capability detection ──────────────────────────────────────────────

_IAM_CACHE: dict[str, str] = {}

_BOOTSTRAP_ROLES = {
    "roles/owner",
    "roles/editor",
    "roles/resourcemanager.projectCreator",
    "roles/resourcemanager.organizationAdmin",
}
_DEPLOY_ROLES = {
    "roles/run.admin",
    "roles/iam.workloadIdentityPoolAdmin",
    "roles/iam.serviceAccountAdmin",
}


def detect_gcp_iam_level(project: str) -> str:
    """Return 'bootstrap', 'deploy', or 'readonly' based on current gcloud roles.

    Results are cached per-project in the process lifetime to avoid repeated
    gcloud calls on every sidebar render.
    """
    if not project or not shutil.which("gcloud"):
        return "unknown"
    cached = _IAM_CACHE.get(project)
    if cached:
        return cached

    try:
        import subprocess as _sp
        result = _sp.run(
            [
                "gcloud", "projects", "get-iam-policy", project,
                "--flatten=bindings[].members",
                "--format=value(bindings.role)",
                "--filter=bindings.members:user:",
            ],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            _IAM_CACHE[project] = "unknown"
            return "unknown"
        roles = set(result.stdout.strip().splitlines())
        if roles & _BOOTSTRAP_ROLES:
            level = "bootstrap"
        elif roles & _DEPLOY_ROLES:
            level = "deploy"
        else:
            level = "readonly"
    except Exception:
        level = "unknown"

    _IAM_CACHE[project] = level
    return level


def _iam_indicator_html(level: str) -> str:
    """Return a small HTML badge + capability list for the sidebar."""
    if level == "bootstrap":
        badge = '<span class="gp-pill gp-pill-ok">Full access</span>'
        items = "Create GCP projects, bootstrap infra, deploy, verify"
    elif level == "deploy":
        badge = '<span class="gp-pill gp-pill-warn">Deploy only</span>'
        items = "Scaffold services, deploy to Cloud Run, verify — cannot create new GCP projects"
    elif level == "readonly":
        badge = '<span class="gp-pill gp-pill-warn">Read only</span>'
        items = "View and verify existing services — contact your admin to deploy"
    else:
        return ""
    return (
        f'<div class="gp-glass gp-env" style="margin-top:0.4rem">'
        f'<dt>Permissions</dt><dd>{badge}</dd>'
        f'<dt style="grid-column:1/-1;color:var(--gp-muted);font-size:0.66rem;margin-top:0.2rem">'
        f'{items}</dt>'
        f"</div>"
    )


def render_page_header(
    title: str,
    subtitle: str = "",
    *,
    eyebrow: str = "Golden Path",
    callout_html: str = "",
) -> None:
    sub_html = f'<p class="gp-hero-sub">{subtitle}</p>' if subtitle else ""
    callout_block = callout_html or ""
    eyebrow_inner = (
        golden_path_title_html(variant="hero")
        if eyebrow == "Golden Path"
        else eyebrow
    )
    st.markdown(
        f"""
<div class="gp-glass gp-glass-hero">
  <div class="gp-hero-body">
    <p class="gp-page-eyebrow">{eyebrow_inner}</p>
    <h1 class="gp-hero-title">{title}</h1>
    {sub_html}
  </div>
  {callout_block}
</div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str):
    container = st.container(border=True)
    container.markdown(f'<p class="gp-section-title">{title}</p>', unsafe_allow_html=True)
    return container


def navigate_to(page: str) -> None:
    if page in PAGES:
        st.session_state.current_page = page
        st.rerun()


# ── Config ────────────────────────────────────────────────────────────────────


def protected_projects() -> set:
    return set(wd.protected_project_ids(REPO_ROOT))


def default_config() -> dict:
    return wd.default_wizard_config(REPO_ROOT)


def load_config() -> dict:
    # Start with enterprise.env defaults so nothing is missing.
    cfg = wd.default_wizard_config(REPO_ROOT)
    # Overlay whatever the user explicitly saved — their choices win.
    if CONFIG_PATH.is_file():
        try:
            saved = json.loads(CONFIG_PATH.read_text())
            cfg.update(saved)
        except Exception:
            pass
    if cfg.get("profile") in ("teardown", "enterprise"):
        cfg["profile"] = "sandbox"
    return cfg


def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    st.session_state.config = cfg
    invalidate_setup_status()
    st.toast("Settings saved")


# ── Validation ────────────────────────────────────────────────────────────────


def validate_project_id(pid: str) -> str | None:
    pid = pid.strip().lower()
    if len(pid) < 6 or len(pid) > 30:
        return "Project ID must be 6–30 characters."
    if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", pid):
        return "Use lowercase letters, numbers, hyphens; start with a letter, no trailing hyphen."
    if "--" in pid:
        return "Project ID cannot contain consecutive hyphens."
    if pid in protected_projects():
        return f"'{pid}' is a protected project and cannot be used as a sandbox."
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
    return bool(re.match(r"^github-actions@[a-z][a-z0-9-]+\.iam\.gserviceaccount\.com$", value.strip()))


def validate_service_name(name: str) -> str | None:
    if len(name) < 3 or len(name) > 40:
        return "Service name must be 3–40 characters."
    if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", name):
        return "Use lowercase kebab-case; start with a letter, no trailing hyphen."
    if "--" in name:
        return "Service name cannot contain consecutive hyphens."
    return None


# ── Command runner ─────────────────────────────────────────────────────────────


def run_cmd(
    cmd: list[str], cwd: str = None, timeout: int = 300
) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return 1, "", str(e)


def cmd_available(name: str) -> bool:
    return shutil.which(name) is not None


_ERROR_HINTS: list[tuple[str, str]] = [
    ("permission denied", "Your Google Cloud account may lack the required IAM role. Ask your admin for `roles/owner` or `roles/run.admin`."),
    ("quota", "You've hit a GCP quota limit. Visit the GCP console → IAM & Admin → Quotas to request an increase."),
    ("billing", "Billing is not enabled on this project. Go to GCP console → Billing and link a billing account."),
    ("already exists", "A resource with that name already exists. Try a different name, or run Teardown first."),
    ("not found", "A referenced resource was not found. Make sure Bootstrap completed successfully before this step."),
    ("timed out", "The command took too long. Check your network connection and try again."),
    ("command not found", "A required CLI tool is missing. Re-run Prerequisites to check which tools need to be installed."),
    ("authentication", "gcloud authentication failed. Run `gcloud auth login` in your terminal, then try again."),
    ("api not enabled", "A Google Cloud API is not enabled. Bootstrap should enable it automatically — try re-running Bootstrap."),
]


def _error_hint(stderr: str) -> str | None:
    lower = (stderr or "").lower()
    for keyword, hint in _ERROR_HINTS:
        if keyword in lower:
            return hint
    return None


def show_cmd_result(code: int, stdout: str, stderr: str, label: str = "Output"):
    if code != 0:
        hint = _error_hint(stderr or stdout)
        if hint:
            st.warning(f"**What to try:** {hint}")
    if stdout or stderr:
        with st.expander(f"{'❌' if code != 0 else '📋'} {label}", expanded=(code != 0)):
            if stdout:
                st.code(stdout, language="text")
            if stderr:
                st.code(stderr, language="text")


def ps_escape(value) -> str:
    return str(value).replace("'", "''")


def ps_invoke_external() -> str:
    root = ps_escape(REPO_ROOT)
    return f"""
function Invoke-External {{
    param([string]$Exe, [string[]]$ArgumentList, [string]$WorkDir = '')
    $root = '{root}'
    if ([string]::IsNullOrWhiteSpace($WorkDir)) {{ $WorkDir = $root }}
    Push-Location $WorkDir
    try {{
        $merged = & $Exe @ArgumentList 2>&1
        $exit = if ($null -ne $LASTEXITCODE) {{ $LASTEXITCODE }} else {{ 0 }}
        $stdout = @(); $stderr = @()
        foreach ($line in @($merged)) {{
            if ($line -is [System.Management.Automation.ErrorRecord]) {{ $stderr += $line.ToString() }}
            else {{ $stdout += [string]$line }}
        }}
        return [PSCustomObject]@{{ ExitCode = $exit; StdOut = ($stdout -join "`n"); StdErr = ($stderr -join "`n") }}
    }} finally {{ Pop-Location }}
}}
"""


def ps_config_block(cfg: dict) -> str:
    return f"""
$Config = @{{
  profile = '{ps_escape(cfg.get("profile", ""))}'
  gcp_dev_project = '{ps_escape(cfg["gcp_dev_project"])}'
  gcp_prod_project = '{ps_escape(cfg["gcp_prod_project"])}'
  gcp_project = '{ps_escape(cfg["gcp_project"])}'
  gcp_region = '{ps_escape(cfg["gcp_region"])}'
  github_org = '{ps_escape(cfg["github_org"])}'
  github_platform_repo = '{ps_escape(cfg["github_platform_repo"])}'
  goldenpath_version = '{ps_escape(cfg.get("goldenpath_version") or default_config().get("goldenpath_version", ""))}'
  project_display_name = '{ps_escape(cfg.get("project_display_name", cfg["gcp_project"]))}'
  wif_provider = '{ps_escape(cfg.get("wif_provider", ""))}'
  wif_service_account = '{ps_escape(cfg.get("wif_service_account", ""))}'
}}
"""


def run_pwsh(body: str, timeout: int = 300) -> tuple[int, str, str]:
    script = ps_invoke_external() + body
    return run_cmd(["pwsh", "-NoProfile", "-Command", script], timeout=timeout)


def require_pwsh(feature: str) -> bool:
    if cmd_available("pwsh"):
        return True
    st.error(f"PowerShell (`pwsh`) is required for {feature}. Install: `brew install powershell`")
    return False


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


def scaffold_output_warning(output_dir: Path) -> str | None:
    resolved = output_dir.resolve()
    root = REPO_ROOT.resolve()
    if resolved == root:
        return (
            "Do not scaffold into the platform repo root. "
            f"Use a sibling folder (default: `{DEFAULT_SCAFFOLD_OUTPUT}`)."
        )
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return (
        "Scaffolding inside `goldenpath` pollutes the platform repo. "
        f"Prefer `{DEFAULT_SCAFFOLD_OUTPUT}/<service-name>` outside this repo."
    )


def gcp_project_active(project: str) -> bool:
    if not project:
        return False
    code, out, _ = run_cmd(
        ["gcloud", "projects", "describe", project, "--format=value(lifecycleState)"]
    )
    return code == 0 and out.strip() == "ACTIVE"


def github_repo_exists(full_repo: str) -> bool:
    if not full_repo or "/" not in full_repo or not cmd_available("gh"):
        return False
    code, out, _ = run_cmd(
        ["gh", "repo", "view", full_repo, "--json", "name", "-q", ".name"]
    )
    return code == 0 and bool(out.strip())


def cloud_run_service_url(project: str, region: str, service: str) -> str | None:
    if not all((project, region, service)):
        return None
    code, out, _ = run_cmd(
        [
            "gcloud",
            "run",
            "services",
            "describe",
            service,
            f"--project={project}",
            f"--region={region}",
            "--format=value(status.url)",
        ]
    )
    if code == 0 and out.strip():
        return out.strip()
    return None


def _config_status_fingerprint(cfg: dict) -> str:
    return json.dumps(
        {
            "gcp_project": cfg.get("gcp_project"),
            "gcp_region": cfg.get("gcp_region"),
            "github_org": cfg.get("github_org"),
            "wif_provider": cfg.get("wif_provider"),
            "wif_service_account": cfg.get("wif_service_account"),
            "last_service": cfg.get("last_service"),
            "last_service_dir": cfg.get("last_service_dir"),
            "prereqs_ok": st.session_state.get("prereqs_ok", False),
        }
    )


def invalidate_setup_status() -> None:
    st.session_state.pop("setup_status_cache", None)
    st.session_state.pop("setup_status_fingerprint", None)


def compute_setup_status(cfg: dict, *, refresh: bool = False) -> dict[str, bool]:
    fingerprint = _config_status_fingerprint(cfg)
    if (
        not refresh
        and st.session_state.get("setup_status_fingerprint") == fingerprint
        and "setup_status_cache" in st.session_state
    ):
        return st.session_state.setup_status_cache

    project = cfg.get("gcp_project", "")
    svc_dir = service_dir_for(cfg)
    last_service = cfg.get("last_service", "")
    status = {
        "settings": bool(project and cfg.get("github_org")),
        "prerequisites": st.session_state.get("prereqs_ok", False),
        "bootstrap": gcp_project_active(project),
        "wif": bool(
            cfg.get("wif_provider")
            and cfg.get("wif_service_account")
            and is_valid_wif_provider(cfg["wif_provider"])
            and is_valid_wif_service_account(cfg["wif_service_account"])
        ),
        "scaffold": bool(svc_dir and svc_dir.exists()),
        "publish": bool(
            last_service
            and github_repo_exists(f"{cfg.get('github_org', '')}/{last_service}")
        ),
        "verify": bool(
            last_service
            and cloud_run_service_url(
                project, cfg.get("gcp_region", ""), f"{last_service}-dev"
            )
        ),
    }
    st.session_state.setup_status_cache = status
    st.session_state.setup_status_fingerprint = fingerprint
    return status


def next_setup_step(status: dict[str, bool]) -> str | None:
    for key, _, page in SETUP_STEPS:
        if not status.get(key):
            return page
    return None


def render_sidebar() -> str:
    cfg = st.session_state.config
    status = compute_setup_status(cfg)

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
    current = st.session_state.current_page

    with st.sidebar:
        st.markdown(sidebar_brand_html(), unsafe_allow_html=True)

        new_page = current
        for group, pages in NAV_GROUPS.items():
            st.markdown(
                f'<div class="gp-nav-group">{group}</div>',
                unsafe_allow_html=True,
            )
            for p in pages:
                icon = NAV_ICONS.get(p, "")
                label = PAGE_LABELS.get(p, p)
                if p == current:
                    st.markdown(
                        f'<div class="gp-nav-active">'
                        f'<span>{icon}</span><span>{label}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    display = f"{icon}  {label}" if icon else label
                    if st.button(display, key=f"nav_{p}", use_container_width=True):
                        new_page = p

        if new_page != current:
            st.session_state.current_page = new_page
            st.rerun()

        st.divider()

        project = cfg.get("gcp_project") or "—"
        wif_ok = status.get("wif", False)
        auth_icon = "✅" if wif_ok else "⚠️"
        auth_label = "GitHub connected" if wif_ok else "GitHub not connected"
        last_svc = cfg.get("last_service") or "—"

        st.markdown(
            f'<div class="gp-status-strip">'
            f'Project: <strong>{project}</strong><br>'
            f'{auth_icon} {auth_label}<br>'
            f'Service: <strong>{last_svc}</strong>'
            f'</div>',
            unsafe_allow_html=True,
        )

    return current


# ── Page: Dashboard ────────────────────────────────────────────────────────────


def page_dashboard():
    cfg = st.session_state.config
    refresh = st.session_state.pop("refresh_setup_status", False)
    status = compute_setup_status(cfg, refresh=refresh)
    done_count = sum(1 for key, _, _ in SETUP_STEPS if status.get(key))
    total = len(SETUP_STEPS)
    next_page = next_setup_step(status)

    # ── Hero state ────────────────────────────────────────────────────────────
    if status.get("verify"):
        render_page_header(
            "You're live!",
            "Your service is running on Google Cloud. Everything is set up.",
        )
        svc = cfg.get("last_service", "")
        project = cfg.get("gcp_project", "")
        region = cfg.get("gcp_region", "")
        url = cloud_run_service_url(project, region, f"{svc}-dev") if svc and project and region else None
        if url:
            st.success(f"**Service URL:** [{url}]({url})")
        else:
            st.success("All setup steps complete — your service is deployed on Cloud Run.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🏗️ Create another service", type="primary", use_container_width=True):
                navigate_to("Scaffold")
        with c2:
            if st.button("🔍 Verify service health", use_container_width=True):
                navigate_to("Verify")
        with c3:
            if st.button("↻ Refresh status", use_container_width=True):
                st.session_state.refresh_setup_status = True
                invalidate_setup_status()
                st.rerun()
    elif done_count == 0:
        render_page_header(
            "Welcome to Golden Path",
            "Deploy your first service to Google Cloud in minutes.",
        )
        st.info(
            "Follow the steps below to get from zero to a live service on Google Cloud. "
            "The Guided Wizard walks you through each step automatically."
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧙 Start Guided Wizard", type="primary", use_container_width=True):
                navigate_to("Guided Wizard")
        with c2:
            if st.button("⚙️ Go to Settings first", use_container_width=True):
                navigate_to("Settings")
    else:
        next_label = PAGE_LABELS.get(next_page, next_page) if next_page else "—"
        render_page_header(
            "Setup in progress",
            f"{done_count} of {total} steps complete — keep going!",
        )
        c1, c2 = st.columns(2)
        with c1:
            if next_page and st.button(f"→ Continue: {next_label}", type="primary", use_container_width=True):
                navigate_to(next_page)
        with c2:
            if st.button("🧙 Open Guided Wizard", use_container_width=True):
                navigate_to("Guided Wizard")

    st.divider()

    # ── Step cards + Quick checks ─────────────────────────────────────────────
    col_steps, col_checks = st.columns([1.85, 1], gap="medium")

    with col_steps:
        st.markdown("#### Setup checklist")
        for key, label, page in SETUP_STEPS:
            done = status.get(key, False)
            is_next = (page == next_page)
            icon = STEP_ICONS.get(key, "○")
            desc = STEP_DESCRIPTIONS.get(key, "")

            if done:
                card_cls = "gp-step-card gp-step-card-done"
                icon_display = "✅"
                badge = '<span class="gp-step-badge-done">DONE</span>'
            elif is_next:
                card_cls = "gp-step-card gp-step-card-next"
                icon_display = icon
                badge = '<span class="gp-step-badge-next">NEXT</span>'
            else:
                card_cls = "gp-step-card"
                icon_display = icon
                badge = ""

            st.markdown(
                f'<div class="{card_cls}">'
                f'<div class="gp-step-icon">{icon_display}</div>'
                f'<div class="gp-step-body">'
                f'<h4>{label}&nbsp;{badge}</h4>'
                f'<p>{desc}</p>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_checks:
        st.markdown("#### Quick checks")
        if st.button("Check Google Cloud connection", use_container_width=True, key="dash_gcp"):
            with st.spinner("Connecting to Google Cloud..."):
                invalidate_setup_status()
                if gcp_project_active(cfg.get("gcp_project", "")):
                    st.success("Google Cloud project is active")
                else:
                    st.warning("Project not found — run Setup first")

        if st.button("Check GitHub deploy auth", use_container_width=True, key="dash_wif"):
            _check_wif_status(cfg)

        if st.button("List deployed services", use_container_width=True, key="dash_run"):
            with st.spinner("Fetching services..."):
                code, out, err = run_cmd([
                    "gcloud", "run", "services", "list",
                    f"--project={cfg.get('gcp_project', '')}",
                    f"--region={cfg.get('gcp_region', '')}",
                    "--format=table(SERVICE,REGION,URL)",
                ])
            if code == 0 and out:
                st.code(out, language="text")
            elif code == 0:
                st.info("No services deployed yet.")
            else:
                st.error(err or "Could not connect to Google Cloud")

        if st.button("↻ Refresh all status", use_container_width=True, key="dash_refresh"):
            st.session_state.refresh_setup_status = True
            invalidate_setup_status()
            st.rerun()

        st.divider()
        st.caption(
            f"**Project:** {cfg.get('gcp_project', '—')}  \n"
            f"**Region:** {cfg.get('gcp_region', '—')}  \n"
            f"**GitHub:** {cfg.get('github_org', '—')}"
        )


def _check_wif_status(cfg: dict):
    with st.spinner("Looking up WIF credentials..."):
        # Try terraform output first
        code, out, err = run_cmd(
            ["terraform", "output", "-raw", "dev_github_wif_provider_name"],
            cwd=str(BOOTSTRAP_DIR),
        )
        if code == 0 and is_valid_wif_provider(out):
            st.success(f"WIF provider: `{out}`")
            return
        # Try gcloud fallback
        code, out, err = run_cmd([
            "gcloud", "iam", "service-accounts", "list",
            f"--project={cfg['gcp_project']}",
            "--filter=email:github-actions@",
            "--format=value(email)",
        ])
        if code == 0 and out:
            st.success(f"WIF service account: `{out}`")
        else:
            st.warning("WIF credentials not found — run Bootstrap first (menu 3), then WIF Secrets (menu 4).")


# ── Page: Prerequisites ────────────────────────────────────────────────────────


def _render_tool_grid(required: dict[str, str], optional: list[str]) -> bool:
    all_required_ok = True
    cols = st.columns(3)
    tools = list(required.keys()) + ["pwsh"] + optional
    for i, tool in enumerate(tools):
        with cols[i % 3]:
            if tool in required or tool == "pwsh":
                if cmd_available(tool):
                    st.success(f"{tool} — installed")
                else:
                    all_required_ok = False
                    st.error(f"{tool} — missing")
            elif cmd_available(tool):
                st.info(f"{tool} — installed (optional)")
            else:
                st.warning(f"{tool} — not found (optional)")
    return all_required_ok


def page_prerequisites(show_header: bool = True):
    if show_header:
        render_page_header(
            "Check your tools",
            "Make sure the required command-line tools are installed before you start.",
        )

    required = {
        "gcloud": "https://cloud.google.com/sdk/docs/install",
        "terraform": "https://developer.hashicorp.com/terraform/install",
        "git": "https://git-scm.com/",
        "gh": "https://cli.github.com/",
    }
    optional = ["python3", "docker"]

    with section("Installed tools"):
        _render_tool_grid(required, optional)

    if st.button("Run full checks", type="primary"):
        st.subheader("Required tools")
        all_ok = True
        for tool, url in required.items():
            if cmd_available(tool):
                code, out, _ = run_cmd([tool, "--version"])
                ver = out.splitlines()[0] if out else ""
                st.success(f"✅ **{tool}** — {ver}")
            else:
                st.error(f"❌ **{tool}** missing — [Install]({url})")
                all_ok = False

        st.subheader("Wizard backend")
        if cmd_available("pwsh"):
            st.success("✅ pwsh — required for bootstrap, scaffold, publish, teardown")
        else:
            st.error("❌ pwsh missing — [Install](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-macos)")
            all_ok = False

        st.subheader("Optional tools")
        for tool in optional:
            if cmd_available(tool):
                st.success(f"✅ {tool} (optional)")
            else:
                st.warning(f"⚠️ {tool} not found (optional — needed for MCP / Docker)")

        st.session_state.prereqs_ok = all_ok
        invalidate_setup_status()
        st.divider()
        if all_ok:
            st.success("All required tools found — you're good to go!")
        else:
            st.error("Install missing required tools before running bootstrap.")

        st.subheader("gcloud auth")
        code, out, err = run_cmd(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
        )
        if code == 0 and out:
            st.success(f"✅ gcloud account: `{out}`")
        else:
            st.warning("⚠️ Not logged in to gcloud. Run `gcloud auth login` in your terminal.")

        code, out, err = run_cmd(["gcloud", "auth", "application-default", "print-access-token"])
        if code == 0 and out:
            st.success("✅ Application Default Credentials OK")
        else:
            st.warning("⚠️ ADC not set. Run `gcloud auth application-default login` in your terminal.")


# ── Page: Bootstrap ────────────────────────────────────────────────────────────


def page_bootstrap(show_header: bool = True):
    if show_header:
        render_page_header(
            "Set up Google Cloud",
            "One-time setup that creates your cloud project and deployment infrastructure.",
        )
    cfg = st.session_state.config

    st.info(
        "This runs once per environment. It creates a secure deployment pipeline "
        "that lets your services go live on Google Cloud automatically."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Project:** `{cfg['gcp_project']}`")
        st.markdown(f"**Profile:** `{cfg['profile']}`")
        st.markdown(f"**Region:** `{cfg['gcp_region']}`")
    with col2:
        if cfg.get("sandbox_disposable"):
            st.markdown("🗑️ Disposable — can be torn down from Teardown page")
        if cfg["gcp_project"] in protected_projects():
            st.error(f"⛔ `{cfg['gcp_project']}` is a protected project.")
            return

    err = validate_project_id(cfg["gcp_project"])
    if err:
        st.error(f"Invalid project ID: {err}")
        return

    st.divider()

    with st.expander("What does this do exactly?", expanded=False):
        st.markdown("""
**In plain English:** Golden Path sets up a secure pipeline between GitHub and Google Cloud.

After this step:
- Your Google Cloud project will be ready to host services
- GitHub Actions will be able to deploy your code automatically on every push
- Docker images will be stored in a private container registry

Technically: it enables required Google Cloud APIs, creates a container registry, and sets up a secure trust link between GitHub and Google Cloud (called Workload Identity Federation) so no passwords ever need to be stored.
        """)

    confirm = st.checkbox(
        f"I'm ready — set up Google Cloud project `{cfg['gcp_project']}`"
    )
    if st.button("☁️ Set up Google Cloud", disabled=not confirm):
        if not require_pwsh("bootstrap"):
            return

        st.divider()
        st.subheader("Bootstrap output")

        with st.status("Running bootstrap (gcloud + terraform)...", expanded=True) as status:
            ps_cmd = f"""
$ErrorActionPreference = 'Stop'
. '{ps_escape(REPO_ROOT)}/scripts/setup/modules/Bootstrap.ps1'
{ps_config_block(cfg)}
try {{
  Invoke-GoldenPathBootstrap -RepoRoot '{ps_escape(REPO_ROOT)}' -Config $Config -InvokeExternal {{ param([string]$Exe,[string[]]$ArgumentList,[string]$WorkDir='') Invoke-External $Exe $ArgumentList $WorkDir }}
  Write-Host 'BootstrapOk=True'
}} catch {{
  Write-Host "BootstrapError=$($_.Exception.Message)"
  exit 1
}}
"""
            code, out, err = run_pwsh(ps_cmd, timeout=900)
            show_cmd_result(code, out, err, "Bootstrap output")
            if code != 0:
                st.error("Bootstrap failed — see output above.")
                status.update(label="Bootstrap failed", state="error")
                return
            status.update(label="Bootstrap complete!", state="complete")

        invalidate_setup_status()
        st.success("Google Cloud is set up! Next: **Connect GitHub to Google Cloud** to enable automatic deploys.")


# ── Page: WIF Secrets ─────────────────────────────────────────────────────────


def page_wif_secrets(show_header: bool = True):
    if show_header:
        render_page_header(
            "Connect GitHub to Google Cloud",
            "Get the credentials that let GitHub deploy your services automatically.",
        )
    cfg = st.session_state.config

    st.info(
        "After this step, GitHub Actions can deploy your code to Google Cloud automatically — "
        "no passwords or API keys stored anywhere. "
        "You'll copy two values and add them as GitHub repository secrets."
    )

    if st.button("🔍 Look up WIF credentials"):
        with st.spinner(f"Looking up credentials for `{cfg['gcp_dev_project']}`..."):
            wif = _get_wif_credentials(cfg["gcp_dev_project"])

        if wif:
            cfg["wif_provider"] = wif["provider"]
            cfg["wif_service_account"] = wif["sa"]
            save_config(cfg)

            st.success(f"Found via {wif['source']}")
            st.divider()
            st.subheader("Add these secrets to your GitHub repos")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Secret name**")
                st.code("GCP_WIF_PROVIDER")
                st.code("GCP_WIF_SERVICE_ACCOUNT")
            with col2:
                st.markdown("**Value**")
                st.code(wif["provider"])
                st.code(wif["sa"])

            st.divider()
            st.markdown(f"**Add to:**")
            st.markdown(f"- Platform repo: `{cfg['github_org']}/{cfg['github_platform_repo']}`")
            st.markdown("- Each service repo you scaffold")
            st.markdown(
                f"\n**Also enable reusable workflows:**  \n"
                f"GitHub → `{cfg['github_platform_repo']}` → Settings → Actions → General  \n"
                f"→ *Allow reusable workflows from this repository*"
            )
        else:
            st.error("Could not find WIF credentials. Run Bootstrap first.")

    if cfg.get("wif_provider") and cfg.get("wif_service_account"):
        st.divider()
        st.subheader("Cached credentials")
        st.code(f"GCP_WIF_PROVIDER          = {cfg['wif_provider']}")
        st.code(f"GCP_WIF_SERVICE_ACCOUNT   = {cfg['wif_service_account']}")
        st.caption(f"Saved to `.goldenpath-setup.local.json`")

    st.divider()
    st.subheader("Set secrets on a GitHub repo via gh CLI")
    repo_input = st.text_input(
        "Repo (name or org/name)",
        value=cfg.get("github_platform_repo", ""),
        key="wif_repo_input",
    )
    if st.button("📤 Set secrets via gh CLI"):
        if not cmd_available("gh"):
            st.error("gh CLI required — [Install](https://cli.github.com/)")
        elif not cfg.get("wif_provider") or not cfg.get("wif_service_account"):
            st.warning("Look up WIF credentials first (button above).")
        else:
            full_repo = (
                repo_input if "/" in repo_input
                else f"{cfg['github_org']}/{repo_input}"
            )
            with st.spinner(f"Setting secrets on {full_repo}..."):
                c1, _, e1 = run_cmd([
                    "gh", "secret", "set", "GCP_WIF_PROVIDER",
                    "--body", cfg["wif_provider"], "--repo", full_repo,
                ])
                c2, _, e2 = run_cmd([
                    "gh", "secret", "set", "GCP_WIF_SERVICE_ACCOUNT",
                    "--body", cfg["wif_service_account"], "--repo", full_repo,
                ])
            if c1 == 0 and c2 == 0:
                st.success(f"✅ Secrets set on `{full_repo}`")
            else:
                st.error(f"Failed — run `gh auth login` first\n{e1 or e2}")


def _get_wif_credentials(project_id: str) -> dict | None:
    # Try terraform state first
    if BOOTSTRAP_DIR.exists():
        c1, out1, _ = run_cmd(
            ["terraform", "output", "-raw", "dev_github_wif_provider_name"],
            cwd=str(BOOTSTRAP_DIR),
        )
        c2, out2, _ = run_cmd(
            ["terraform", "output", "-raw", "dev_github_actions_sa_email"],
            cwd=str(BOOTSTRAP_DIR),
        )
        if (
            c1 == 0
            and c2 == 0
            and is_valid_wif_provider(out1)
            and is_valid_wif_service_account(out2)
        ):
            return {"provider": out1.strip(), "sa": out2.strip(), "source": "terraform"}

    # gcloud fallback
    c, sa_out, _ = run_cmd([
        "gcloud", "iam", "service-accounts", "list",
        f"--project={project_id}",
        "--filter=email:github-actions@",
        "--format=value(email)",
    ])
    if c != 0 or not sa_out:
        return None

    c, pool_out, _ = run_cmd([
        "gcloud", "iam", "workload-identity-pools", "list",
        f"--project={project_id}", "--location=global",
        "--format=value(name)",
    ])
    if c != 0 or not pool_out:
        return None

    pool_name = re.sub(r".*/workloadIdentityPools/", "", pool_out.splitlines()[0])
    c, prov_out, _ = run_cmd([
        "gcloud", "iam", "workload-identity-pools", "providers", "list",
        f"--project={project_id}", "--location=global",
        f"--workload-identity-pool={pool_name}",
        "--format=value(name)",
    ])
    if c != 0 or not prov_out:
        return None

    return {
        "provider": prov_out.splitlines()[0],
        "sa": sa_out.splitlines()[0],
        "source": "gcloud",
    }


# ── Page: Scaffold ────────────────────────────────────────────────────────────


_SCAFFOLD_STEPS = ["Template & name", "Runtime & mode", "Data stores", "Environments & review"]


def _scaffold_draft() -> dict:
    cfg = st.session_state.config
    return st.session_state.setdefault(
        "scaffold_draft",
        {
            "service_name": "",
            "template": "nextjs",
            "runtime": "",
            "deployment_mode": "",
            "stores": {},  # {store_id: subconfig dict}
            "environments": ["dev", "prod"],
            "output_dir": str(DEFAULT_SCAFFOLD_OUTPUT),
            "project": cfg.get("gcp_dev_project", ""),
        },
    )


def _vpc_network() -> str | None:
    cfg = st.session_state.config
    return cfg.get("gcp_vpc_network") or wd.platform_default("GCP_VPC_NETWORK", REPO_ROOT) or None


def _draft_to_config(d: dict) -> "sc.ServiceConfig":
    stores = [sc.DataStoreSpec(sid, dict(conf)) for sid, conf in d.get("stores", {}).items()]
    return sc.ServiceConfig(
        service_name=d.get("service_name", ""),
        template=d.get("template", "nextjs"),
        runtime=d.get("runtime", ""),
        deployment_mode=d.get("deployment_mode", ""),
        data_stores=stores,
        environments=list(d.get("environments", [])),
        region=st.session_state.config.get("gcp_region", ""),
    )


def _iam_report_for(d: dict) -> dict:
    """Non-blocking IAM report: only includes stores we could actually verify."""
    probe = st.session_state.get("scaffold_iam_probe", {})
    report = {}
    for sid, entry in probe.items():
        if not entry.get("unknown") and entry.get("missing"):
            report[sid] = {"missing": entry["missing"]}
    return report


def page_scaffold(show_header: bool = True):
    if show_header:
        render_page_header(
            "Create a new service",
            "Compose a service from a template, runtime, deployment mode, and managed "
            "data stores — Golden Path validates every choice and generates deploy-ready "
            "code plus Terraform.",
        )
    cfg = st.session_state.config
    d = _scaffold_draft()
    step = st.session_state.get("scaffold_step", 0)

    st.markdown(_wizard_stepper_html(_SCAFFOLD_STEPS, step), unsafe_allow_html=True)

    if step == 0:
        _scaffold_step_template(d)
    elif step == 1:
        _scaffold_step_runtime_mode(d)
    elif step == 2:
        _scaffold_step_data_stores(d)
    else:
        _scaffold_step_review(d, cfg)

    _scaffold_nav(d, step)

    if step == 0:
        st.divider()
        _render_custom_template_expander(cfg)


def _scaffold_nav(d: dict, step: int) -> None:
    st.divider()
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if step > 0 and st.button("← Back", use_container_width=True, key="scaffold_back"):
            st.session_state.scaffold_step = step - 1
            st.rerun()
    with cols[1]:
        st.caption(f"Step {step + 1} of {len(_SCAFFOLD_STEPS)} · {_SCAFFOLD_STEPS[step]}")
    with cols[2]:
        if step < len(_SCAFFOLD_STEPS) - 1:
            blocked = _scaffold_step_blocked(d, step)
            if st.button("Next →", use_container_width=True, disabled=blocked, key="scaffold_next"):
                st.session_state.scaffold_step = step + 1
                st.rerun()


def _scaffold_step_blocked(d: dict, step: int) -> bool:
    if step == 0:
        return bool(
            not d["service_name"]
            or validate_service_name(d["service_name"])
            or not d["output_dir"]
        )
    if step == 1:
        return not (d["runtime"] and d["deployment_mode"])
    return False


def _scaffold_step_template(d: dict) -> None:
    templates = _load_templates() or {t: {} for t in DEFAULT_TEMPLATES}
    names = list(templates.keys())
    with section("Choose a template"):
        idx = names.index(d["template"]) if d["template"] in names else 0
        template = st.selectbox(
            "Template",
            names,
            index=idx,
            help="Not sure? Next.js is the default for most web apps.",
        )
        if template != d["template"]:
            # Reset downstream choices when the template changes.
            d.update({"template": template, "runtime": "", "deployment_mode": "", "stores": {}})
        caps = sc.template_capabilities(template, templates)
        st.caption(
            f"**{templates.get(template, {}).get('description', template)}** · "
            f"runtimes: {', '.join(caps['runtimes'])} · "
            f"modes: {', '.join(caps['deployment_modes'])}"
        )

    with section("Name & location"):
        name = st.text_input(
            "Service name",
            value=d["service_name"],
            placeholder="my-service",
            help="3–40 characters, lowercase letters, numbers, and hyphens.",
        )
        d["service_name"] = name
        name_err = validate_service_name(name) if name else None
        if name_err:
            st.error(name_err)

        out = st.text_input(
            "Where to create the service (parent folder)",
            value=d["output_dir"],
            help="A new folder is created here with your service name (kept outside this platform folder).",
        )
        d["output_dir"] = out
        output_dir = Path(out).expanduser() if out else None
        warn = scaffold_output_warning(output_dir) if output_dir else None
        if warn:
            st.warning(warn)
        if output_dir and name:
            target = output_dir / name
            if target.exists() and list(target.iterdir()):
                st.warning(f"A non-empty folder `{name}` already exists there.")

        project = st.text_input(
            "Google Cloud project (leave blank to use your saved project)",
            value=d.get("project", ""),
            key="scaffold_project",
            help="The GCP project where this service (and any data stores) will be created.",
        )
        d["project"] = project
        perr = validate_project_id(project) if project else None
        if perr:
            st.error(perr)


def _scaffold_step_runtime_mode(d: dict) -> None:
    templates = _load_templates()
    with section("Runtime"):
        runtime_opts = [o["value"] for o in sc.runtime_options(d["template"], templates)]
        if d["runtime"] not in runtime_opts:
            d["runtime"] = runtime_opts[0]
        d["runtime"] = st.radio(
            "Runtime",
            runtime_opts,
            index=runtime_opts.index(d["runtime"]),
            horizontal=True,
            help="Docker is available as a packaging option for server templates.",
        )

    with section("Deployment mode"):
        mode_opts = sc.mode_options(d["template"], templates)
        enabled = [o for o in mode_opts if o["enabled"]]
        disabled = [o for o in mode_opts if not o["enabled"]]
        values = [o["value"] for o in enabled]
        labels = {o["value"]: o["label"] for o in enabled}
        if d["deployment_mode"] not in values:
            d["deployment_mode"] = values[0]
        d["deployment_mode"] = st.radio(
            "How is this service delivered?",
            values,
            index=values.index(d["deployment_mode"]),
            format_func=lambda v: labels[v],
        )
        for o in disabled:
            st.caption(f"🔒 {o['label']} — {o['reason']}")
        if d["deployment_mode"] == sc.MODE_STATIC:
            st.info(
                "Static/SPA services are client-only and cannot hold a database "
                "connection directly. A companion BFF service to own the DB is coming "
                "in a later release."
            )


def _scaffold_step_data_stores(d: dict) -> None:
    mode = d["deployment_mode"]
    if mode == sc.MODE_STATIC:
        with section("Data stores"):
            st.info("Not available for static/SPA services (see the previous step).")
            for o in sc.data_store_options(mode):
                st.caption(f"🔒 {o['label']} — {o['reason']}")
        return

    project = d.get("project") or st.session_state.config.get("gcp_dev_project", "")
    with section("Attach managed data stores"):
        st.caption(
            "Options reflect both template capability and your real IAM permissions. "
            "Use *Check my permissions* to gate on live access."
        )
        if st.button("🔐 Check my permissions", key="scaffold_iam_check"):
            enabled_ids = [
                sid for sid, s in sc.DATA_STORES.items() if s.get("enabled")
            ]
            ip_mode = "private" if any(
                c.get("ip_mode") == "private" for c in d["stores"].values()
            ) else "public"
            with st.spinner("Checking IAM permissions on the target project…"):
                st.session_state["scaffold_iam_probe"] = ops.probe_data_store_permissions(
                    project, enabled_ids, ip_mode
                )

        iam_report = _iam_report_for(d)
        for o in sc.data_store_options(mode, iam_report, _vpc_network()):
            sid = o["value"]
            selected_now = sid in d["stores"]
            if not o["enabled"]:
                st.checkbox(o["label"], value=False, disabled=True, key=f"ds_{sid}")
                st.caption(f"🔒 {o['reason']}")
                continue
            checked = st.checkbox(o["label"], value=selected_now, key=f"ds_{sid}")
            if checked and not selected_now:
                d["stores"][sid] = _default_store_config(sid)
            elif not checked and selected_now:
                d["stores"].pop(sid, None)

        probe = st.session_state.get("scaffold_iam_probe", {})
        for sid, entry in probe.items():
            if entry.get("unknown"):
                st.caption(f"⚠️ Could not verify permissions for {sc.DATA_STORES[sid]['display_name']}.")

    for sid in list(d["stores"].keys()):
        if sid == "cloud_sql":
            _cloud_sql_subconfig(d)


def _default_store_config(sid: str) -> dict:
    if sid == "cloud_sql":
        return {
            "engine": "postgresql",
            "version": "POSTGRES_16",
            "tier": "db-f1-micro",
            "high_availability": False,
            "ip_mode": "public",
            "database_name": "appdb",
        }
    return {}


def _cloud_sql_subconfig(d: dict) -> None:
    store = sc.DATA_STORES["cloud_sql"]
    conf = d["stores"]["cloud_sql"]
    with section("Cloud SQL configuration"):
        c1, c2 = st.columns(2)
        with c1:
            engines = [e for e in store["engines"] if e.get("enabled")]
            conf["engine"] = st.selectbox(
                "Engine", [e["value"] for e in engines],
                format_func=lambda v: next(e["label"] for e in engines if e["value"] == v),
            )
            versions = next(e["versions"] for e in engines if e["value"] == conf["engine"])
            if conf.get("version") not in versions:
                conf["version"] = versions[0]
            conf["version"] = st.selectbox("Version", versions, index=versions.index(conf["version"]))
            conf["database_name"] = st.text_input("Database name", value=conf.get("database_name", "appdb"))
        with c2:
            tiers = store["tiers"]
            if conf.get("tier") not in tiers:
                conf["tier"] = store["default_tier"]
            conf["tier"] = st.selectbox("Tier", tiers, index=tiers.index(conf["tier"]))
            conf["high_availability"] = st.checkbox(
                "High availability (REGIONAL)", value=conf.get("high_availability", False)
            )
            vpc = _vpc_network()
            ip_modes = store["ip_modes"]
            disabled_private = not vpc
            ip_choice = st.radio(
                "IP mode", ip_modes,
                index=ip_modes.index(conf.get("ip_mode", "public")),
                horizontal=True,
            )
            if ip_choice == "private" and disabled_private:
                st.warning(
                    "Private IP needs a VPC network (set GCP_VPC_NETWORK in "
                    "config/enterprise.env). Falling back to public IP."
                )
                ip_choice = "public"
            conf["ip_mode"] = ip_choice
        st.caption(
            "Uses IAM database authentication — the runtime service account connects "
            "with an OAuth token; no password is created or stored."
        )


def _scaffold_step_review(d: dict, cfg: dict) -> None:
    svc = _draft_to_config(d)
    result = sc.validate_config(svc, vpc_network=_vpc_network(), iam_report=_iam_report_for(d))

    with section("Review"):
        st.markdown(
            f"- **Service**: `{d['service_name'] or '—'}`\n"
            f"- **Template**: {d['template']} · **runtime**: {d['runtime']} · "
            f"**mode**: {d['deployment_mode']}\n"
            f"- **Data stores**: "
            + (", ".join(f"{sid} ({c.get('engine','')}/{c.get('ip_mode','')})"
                         for sid, c in d["stores"].items()) or "none")
        )
        d["environments"] = st.multiselect(
            "Environments", ["dev", "prod"], default=d.get("environments", ["dev", "prod"])
        )

    if result.errors:
        with section("Fix before creating"):
            for issue in result.errors:
                icon = {"capability": "🚫", "permission": "🔒", "config": "⚠️"}.get(issue.gate, "•")
                st.error(f"{icon} **{issue.field}** — {issue.message}")

    create_disabled = not result.ok
    if st.button("Create service", type="primary", disabled=create_disabled, key="scaffold_create"):
        _do_scaffold(d, cfg, svc)


def _do_scaffold(d: dict, cfg: dict, svc: "sc.ServiceConfig") -> None:
    output_dir = Path(d["output_dir"]).expanduser()
    project = d.get("project") or cfg.get("gcp_dev_project", "")
    scaffold_cfg = {
        **cfg,
        "gcp_dev_project": project,
        "gcp_prod_project": project,
        "gcp_project": project,
    }
    with st.spinner(f"Creating `{svc.service_name}` from the {svc.template} template…"):
        try:
            result = ops.scaffold(
                svc.service_name, svc.template, output_dir, scaffold_cfg, service_config=svc
            )
        except Exception as exc:
            st.error(f"Could not create service: {exc}")
            return

    cfg["last_service"] = svc.service_name
    cfg["last_service_dir"] = str(result.service_dir)
    save_config(cfg)
    invalidate_setup_status()
    st.success(f"Service `{svc.service_name}` created at `{result.service_dir}`")
    st.caption(f"Health check path: `{result.health_check_path}`")
    for note in result.data_store_notes or []:
        st.caption(f"• generated {note}")
    st.info("Ready to go! Head to **Deploy your service** to push it to GitHub and deploy.")


def _render_custom_template_expander(cfg: dict) -> None:
    with st.expander("My template isn't listed — create a custom one"):
        st.markdown(
            "Don't see your stack above? Describe it below and Golden Path will generate "
            "a baseline project with the right Dockerfile, Cloud Run infrastructure, and "
            "GitHub Actions deploy workflow."
        )
        c1, c2 = st.columns(2)
        with c1:
            custom_name = st.text_input(
                "Service name",
                key="custom_svc_name",
                placeholder="my-custom-service",
                help="3–40 characters, lowercase kebab-case",
            )
            custom_name_err = validate_service_name(custom_name) if custom_name else None
            if custom_name_err:
                st.error(custom_name_err)
        with c2:
            custom_runtime = st.radio(
                "Runtime",
                ["python", "node", "docker"],
                key="custom_runtime",
                help="Choose the language/runtime your service uses.",
                horizontal=True,
            )
        c3, c4 = st.columns(2)
        with c3:
            custom_port = st.number_input(
                "Port your app listens on",
                min_value=1, max_value=65535, value=8080, step=1,
                key="custom_port",
            )
        with c4:
            custom_health = st.text_input(
                "Health check path",
                value="/health",
                key="custom_health",
                help="Golden Path uses this URL to confirm your service is running.",
            )

        custom_output_str = st.text_input(
            "Where to create the service (parent folder)",
            value=str(DEFAULT_SCAFFOLD_OUTPUT),
            key="custom_output_dir",
        )
        custom_output = Path(custom_output_str).expanduser() if custom_output_str else None

        gen_disabled = bool(custom_name_err or not custom_name or not custom_output_str)
        if st.button("Generate custom template", disabled=gen_disabled, key="gen_custom"):
            with st.spinner(f"Generating `{custom_name}` ({custom_runtime}, port {custom_port})..."):
                try:
                    project_to_use = cfg.get("gcp_dev_project", "")
                    gen_cfg = {
                        **cfg,
                        "gcp_dev_project": project_to_use,
                        "gcp_prod_project": project_to_use,
                        "gcp_project": project_to_use,
                    }
                    result = ops.generate_custom_template(
                        name=custom_name,
                        runtime=custom_runtime,
                        port=int(custom_port),
                        health_path=custom_health or "/health",
                        output_dir=custom_output,
                        cfg=gen_cfg,
                    )
                except Exception as exc:
                    st.error(f"Could not generate template: {exc}")
                else:
                    cfg["last_service"] = custom_name
                    cfg["last_service_dir"] = str(result.service_dir)
                    save_config(cfg)
                    invalidate_setup_status()
                    st.success(f"Custom service `{custom_name}` created at `{result.service_dir}`")
                    st.caption(f"Based on the **{result.template}** template · health: `{result.health_check_path}`")
                    st.info("Next: head to **Deploy your service** to push to GitHub and deploy.")


def _load_templates() -> dict:
    catalog_path = REPO_ROOT / "templates/catalog.json"
    if catalog_path.exists():
        try:
            return json.loads(catalog_path.read_text())
        except Exception:
            pass
    # Also try goldenpath catalog format
    for p in (REPO_ROOT / "templates").glob("*.json"):
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


# ── Page: Publish ─────────────────────────────────────────────────────────────


def page_publish(show_header: bool = True):
    if show_header:
        render_page_header(
            "Deploy your service",
            "Push your service to GitHub and watch it go live on Google Cloud.",
        )
    cfg = st.session_state.config

    st.info(
        "This creates a GitHub repository for your service, sets up the deploy pipeline, "
        "and pushes your code. The first deploy happens automatically."
    )

    default_path = service_dir_for(cfg)
    default_dir = str(default_path) if default_path else ""
    service_dir = st.text_input(
        "Service directory (absolute path)",
        value=default_dir,
        key="publish_dir",
    )

    if service_dir:
        p = Path(service_dir)
        if not p.exists():
            st.warning(f"Directory not found: `{service_dir}`")
        else:
            service_name = p.name
            st.markdown(f"Service name: **`{service_name}`**")

    st.divider()
    if not cfg.get("wif_provider") or not cfg.get("wif_service_account"):
        st.warning("WIF credentials not found. Get them from **WIF Secrets** first.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**WIF provider:** `{cfg.get('wif_provider', '—')}`")
    with col2:
        st.markdown(f"**WIF SA:** `{cfg.get('wif_service_account', '—')}`")

    if st.button("📤 Publish", disabled=not service_dir):
        if not Path(service_dir).exists():
            st.error(f"Directory not found: `{service_dir}`")
            return
        if not cfg.get("wif_provider") or not cfg.get("wif_service_account"):
            st.error("WIF credentials required — visit WIF Secrets first.")
            return

        svc_path = Path(service_dir).resolve()
        svc_name = svc_path.name

        with st.status("Publishing your service — this takes a few minutes...", expanded=True) as pub_status:
            log_lines: list[str] = []
            log_box = st.empty()

            def on_step(msg: str) -> None:
                log_lines.append(msg)
                log_box.code("\n".join(log_lines), language="text")

            try:
                pub = ops.publish(
                    svc_path,
                    cfg,
                    cfg["wif_provider"],
                    cfg["wif_service_account"],
                    watch_deploy=True,
                    on_step=on_step,
                )
                pub_status.update(label="Published!", state="complete")
            except Exception as exc:
                pub_status.update(label=f"Publish failed: {exc}", state="error")
                st.error(f"Publish failed: {exc}")
                return

        cfg["last_service"] = svc_name
        cfg["last_service_dir"] = str(svc_path)
        save_config(cfg)
        invalidate_setup_status()
        st.success(f"Published `{svc_name}`")
        st.markdown(f"🐙 [View on GitHub](https://github.com/{pub.repo})")
        st.markdown(f"⚡ [View Actions](https://github.com/{pub.repo}/actions)")

        if pub.deploy_ok is False:
            st.error("Deploy workflow failed — repo was created but Cloud Run may not be live yet.")
        elif pub.deploy_ok:
            verify = ops.verify_deployment(f"{svc_name}-dev", cfg, svc_path)
            ops.show_deployment_result(verify, pub.repo, verbose=True)
            if verify.health_ok:
                st.success("✅ Service is live and healthy")
            elif verify.url:
                st.warning("Service URL exists but health check not ready — try Verify in a minute.")


# ── Page: Verify ─────────────────────────────────────────────────────────────


def page_verify():
    render_page_header(
        "Verify",
        "Confirm your Cloud Run service is reachable and health checks pass.",
    )
    cfg = st.session_state.config

    default_svc = f"{cfg['last_service']}-dev" if cfg.get("last_service") else ""
    service_name = st.text_input("Cloud Run service name", value=default_svc)
    project = st.text_input("GCP project", value=cfg.get("gcp_project", ""))
    region = st.text_input("Region", value=cfg.get("gcp_region") or default_config().get("gcp_region", ""))

    service_path = service_dir_for(cfg)
    if service_path:
        st.caption(f"Service directory for health paths: `{service_path}`")

    if st.button("✅ Check deployment"):
        if not service_name:
            st.warning("Enter a service name.")
            return
        if not require_pwsh("verify"):
            return

        verify_cfg = {**cfg, "gcp_project": project, "gcp_region": region}
        service_dir_arg = str(service_path) if service_path else ""
        with st.spinner(f"Checking `{service_name}` in `{project}`..."):
            ps_cmd = f"""
$ErrorActionPreference = 'Continue'
. '{ps_escape(REPO_ROOT)}/scripts/setup/modules/Verify.ps1'
{ps_config_block(verify_cfg)}
$verify = Invoke-GoldenPathVerifyDeployment -CloudRunService '{ps_escape(service_name)}' `
  -ServiceDir '{ps_escape(service_dir_arg)}' -RepoRoot '{ps_escape(REPO_ROOT)}' -Config $Config `
  -InvokeExternal {{ param([string]$Exe,[string[]]$ArgumentList,[string]$WorkDir='') Invoke-External $Exe $ArgumentList $WorkDir }}
Write-Host "Url=$($verify.Url)"
Write-Host "HealthOk=$($verify.HealthOk)"
Write-Host "HealthPath=$($verify.HealthPath)"
Write-Host "StatusCode=$($verify.StatusCode)"
Write-Host "Error=$($verify.Error)"
"""
            code, out, err = run_pwsh(ps_cmd, timeout=300)

        show_cmd_result(code, out, err, "Verify output")

        url_match = re.search(r"Url=(.+)", out)
        health_ok = re.search(r"HealthOk=(True|False)", out)
        health_path = re.search(r"HealthPath=(.*)", out)
        status_code = re.search(r"StatusCode=(.*)", out)
        error_match = re.search(r"Error=(.*)", out)

        url = url_match.group(1).strip() if url_match else ""
        if not url:
            err_msg = error_match.group(1).strip() if error_match else "Service not found"
            st.error(f"Service `{service_name}` not found in `{project}` ({region}). {err_msg}")
            return

        st.success(f"✅ Service URL: [{url}]({url})")

        if health_ok and health_ok.group(1) == "True":
            path = health_path.group(1).strip() if health_path else ""
            code_val = status_code.group(1).strip() if status_code else ""
            st.success(f"✅ Health check OK → `{path}` returned HTTP {code_val}")
        else:
            st.warning("⚠️ Service URL exists but health check not ready — wait 30s and try again.")

        org = cfg.get("github_org", "")
        svc_base = service_name.removesuffix("-dev")
        if org:
            st.markdown(f"[⚡ GitHub Actions](https://github.com/{org}/{svc_base}/actions)")


# ── Page: Doctor ─────────────────────────────────────────────────────────────


def page_doctor():
    render_page_header(
        "Doctor",
        "Diagnose common deploy blockers before publishing or re-deploying.",
    )
    cfg = st.session_state.config

    default_path = service_dir_for(cfg)
    default_dir = str(default_path) if default_path else str(REPO_ROOT)
    service_dir = st.text_input("Service directory", value=default_dir)

    if st.button("🩺 Run doctor"):
        svc_path = Path(service_dir)
        if not svc_path.exists():
            st.error(f"Directory not found: `{service_dir}`")
            return

        with st.spinner("Diagnosing..."):
            issues = ops.service_doctor(svc_path.resolve(), cfg)

        st.divider()
        if not issues:
            st.success("✅ No issues found — everything looks good!")
        else:
            st.error(f"Found {len(issues)} issue(s):")
            for i, issue in enumerate(issues, 1):
                st.markdown(f"**{i}.** {issue}")
            st.info("Fix the issues above, then re-run Publish.")


# ── Page: MCP Config ─────────────────────────────────────────────────────────


def page_mcp(show_header: bool = True):
    if show_header:
        render_page_header(
            "MCP Config",
            "Generate Claude MCP configuration for local and hosted Golden Path access.",
        )
    cfg = st.session_state.config

    st.info(
        "Generates a Claude MCP configuration that lets Claude access your "
        "Golden Path environment via the local MCP server."
    )

    mcp_dir = REPO_ROOT / "mcp"
    venv_python = mcp_dir / ".venv/bin/python"

    if st.button("🤖 Generate MCP config"):
        if not venv_python.exists():
            st.warning(f"MCP venv not found at `{venv_python}`")
            st.markdown("Create it first:")
            st.code(f"cd {mcp_dir}\npython3 -m venv .venv\n.venv/bin/pip install -r requirements.txt")
            return

        goldenpath_version = cfg.get("goldenpath_version") or default_config().get("goldenpath_version", "")
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
        out_path = mcp_dir / "claude-mcp.generated.json"
        out_path.write_text(json.dumps(mcp_cfg, indent=2))

        st.success(f"✅ Written to `{out_path}`")
        st.subheader("Paste into Claude Desktop → Settings → Developer → MCP:")
        st.json(mcp_cfg)
        st.markdown(
            "**Or merge** the `goldenpath-local` key into your existing `Claude Desktop MCP config file`"
        )

    if cfg.get("wif_provider"):
        st.divider()
        st.subheader("Cloud-hosted MCP (via Cloud Run)")
        st.info("The hosted MCP server is deployed to Cloud Run via GitHub Actions.")
        mcp_svc = f"mcp-server-dev"
        code, url, _ = run_cmd([
            "gcloud", "run", "services", "describe", mcp_svc,
            f"--project={cfg['gcp_project']}",
            f"--region={cfg['gcp_region']}",
            "--format=value(status.url)",
        ])
        if code == 0 and url:
            st.success(f"MCP server URL: [{url}]({url})")
            hosted_cfg = {
                "mcpServers": {
                    "goldenpath-cloud": {
                        "url": url,
                        "transport": "streamable-http",
                    }
                }
            }
            st.json(hosted_cfg)
        else:
            st.caption("Hosted MCP server not deployed yet.")


# ── Page: Edit Settings ───────────────────────────────────────────────────────


def page_edit_settings(show_header: bool = True):
    if show_header:
        render_page_header(
            "Settings",
            "Configure your Google Cloud project, region, and GitHub organization.",
        )
    cfg = st.session_state.config

    setup_modes = [
        "Use a pre-configured sandbox project",
        "Create a new sandbox project with a custom name",
        "Use an existing Google Cloud project I already have",
    ]
    saved_profile = cfg.get("profile", "sandbox")
    if saved_profile in ("teardown", "enterprise"):
        saved_profile = "sandbox"
    default_mode = 0 if saved_profile == "sandbox" else 2
    setup_mode = st.radio(
        "Which Google Cloud project do you want to use?",
        setup_modes,
        index=default_mode,
        help="If you're not sure, choose the first option.",
    )

    if setup_mode == setup_modes[0]:
        profile = "sandbox"
        st.caption("Uses defaults from your organization's configuration.")
        suggested_project = default_config()["gcp_project"]
    elif setup_mode == setup_modes[1]:
        profile = "sandbox"
        st.caption("You'll enter a unique project name below. You can tear it down later.")
        suggested_project = f"gp-sandbox-{datetime.now().strftime('%Y%m%d')}"
    else:
        profile = "custom"
        st.caption("Use a Google Cloud project that already exists.")
        suggested_project = cfg.get("gcp_project", "")

    col1, col2 = st.columns(2)
    with col1:
        gcp_project = st.text_input(
            "Google Cloud project ID",
            value=cfg.get("gcp_project", suggested_project),
            help="Lowercase letters, numbers, and hyphens. Must be globally unique in Google Cloud.",
        )
        pid_err = validate_project_id(gcp_project) if gcp_project else "Required"
        if pid_err:
            st.error(pid_err)

        display_name = st.text_input(
            "Project display name (optional)",
            value=cfg.get("project_display_name", ""),
            help="A friendly name shown in the Google Cloud console.",
        )
        region_options = ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"]
        current_region = cfg.get("gcp_region") or default_config().get("gcp_region", "")
        if current_region and current_region not in region_options:
            region_options = [current_region, *region_options]
        gcp_region = st.selectbox(
            "Google Cloud region",
            region_options,
            index=region_options.index(current_region) if current_region in region_options else 0,
            help="The geographic region where your services will run. us-central1 is a good default.",
        )

    with col2:
        github_org = st.text_input(
            "GitHub organization or username",
            value=cfg.get("github_org", ""),
            help="Your GitHub org or personal username (e.g. my-company or johndoe).",
        )
        github_platform_repo = st.text_input(
            "Platform repository name",
            value=cfg.get("github_platform_repo", ""),
            help="The name of the Golden Path platform repository on GitHub.",
        )
        goldenpath_version = st.text_input(
            "Golden Path version",
            value=cfg.get("goldenpath_version") or default_config().get("goldenpath_version", ""),
            help="Leave as-is unless your organization has a specific version requirement.",
        )
        sandbox_disposable = profile == "sandbox"

    same_dev_prod = st.checkbox("Use same project for dev and prod", value=True)
    gcp_prod_project = gcp_project
    if not same_dev_prod:
        gcp_prod_project = st.text_input(
            "GCP prod project ID",
            value=cfg.get("gcp_prod_project", gcp_project),
        )

    if st.button("💾 Save settings", disabled=bool(pid_err)):
        # Clear WIF if project changed
        wif_provider = cfg.get("wif_provider", "")
        wif_service_account = cfg.get("wif_service_account", "")
        if gcp_project != cfg.get("gcp_project"):
            wif_provider = ""
            wif_service_account = ""
            st.warning("Project changed — WIF credentials cleared. Re-run WIF Secrets after bootstrap.")

        new_cfg = {
            **cfg,
            "profile": profile,
            "gcp_project": gcp_project,
            "project_display_name": display_name or gcp_project,
            "gcp_region": gcp_region,
            "github_org": github_org,
            "github_platform_repo": github_platform_repo,
            "goldenpath_version": goldenpath_version,
            "gcp_dev_project": gcp_project,
            "gcp_prod_project": gcp_prod_project,
            "sandbox_disposable": sandbox_disposable,
            "wif_provider": wif_provider,
            "wif_service_account": wif_service_account,
        }
        save_config(new_cfg)
        st.success("✅ Settings saved!")
        st.rerun()


# ── Page: Teardown ────────────────────────────────────────────────────────────


def page_teardown():
    render_page_header(
        "Teardown",
        "Destroy Terraform resources and optionally delete the disposable GCP project.",
    )
    cfg = st.session_state.config

    project = cfg.get("gcp_project", "")
    profile = cfg.get("profile", "")

    err = validate_project_id(project)
    if err:
        st.error(f"Cannot tear down: {err}")
        return

    if project in protected_projects():
        st.error(f"⛔ `{project}` is a protected project and cannot be torn down from this wizard.")
        return

    if cfg.get("sandbox_disposable") is not True and profile != "sandbox":
        st.warning(
            f"Profile `{profile}` is not marked as disposable. "
            "Only proceed if you're sure you want to destroy these resources."
        )

    st.error(
        f"⚠️ This will destroy all Golden Path Terraform resources in project **`{project}`**."
    )
    st.markdown("""
**Steps:**
1. `terraform destroy` in `platform/bootstrap/`
2. Optionally delete the entire GCP project (irreversible)

Protected projects (`YOUR_BILLING_ANCHOR_PROJECT`, etc.) are blocked.
    """)

    col1, col2 = st.columns(2)
    with col1:
        confirm_destroy = st.checkbox(f"Destroy Terraform resources in `{project}`")
    with col2:
        confirm_delete = st.checkbox(
            f"DELETE entire GCP project `{project}` (irreversible)",
            disabled=not confirm_destroy,
        )

    if st.button("💣 Run Teardown", disabled=not confirm_destroy):
        if not require_pwsh("teardown"):
            return

        delete_flag = "$true" if confirm_delete else "$false"
        with st.status("Running teardown...", expanded=True) as status:
            ps_cmd = f"""
$ErrorActionPreference = 'Stop'
. '{ps_escape(REPO_ROOT)}/scripts/setup/modules/Bootstrap.ps1'
try {{
  Invoke-GoldenPathTeardown -RepoRoot '{ps_escape(REPO_ROOT)}' -DeleteProject:{delete_flag} -InvokeExternal {{ param([string]$Exe,[string[]]$ArgumentList,[string]$WorkDir='') Invoke-External $Exe $ArgumentList $WorkDir }}
  Write-Host 'TeardownOk=True'
}} catch {{
  Write-Host "TeardownError=$($_.Exception.Message)"
  exit 1
}}
"""
            code, out, err = run_pwsh(ps_cmd, timeout=900)
            show_cmd_result(code, out, err, "Teardown output")
            if code != 0:
                st.error("Teardown failed — see output above.")
                status.update(label="Teardown failed", state="error")
                return
            status.update(label="Teardown complete!", state="complete")

        st.success(f"✅ Sandbox `{project}` torn down.")
        st.info("Set a new project in Settings to start fresh.")


# ── Page: Fresh Start ─────────────────────────────────────────────────────────


def page_fresh_start():
    render_page_header(
        "Fresh Start",
        "Reset local wizard state without deleting cloud or GitHub resources.",
    )
    cfg = st.session_state.config

    st.warning(
        "Resets `.goldenpath-setup.local.json` to defaults.  \n"
        "**Does NOT delete** GCP projects, GitHub repos, or Cloud Run services.  \n"
        "Use Teardown if you want to destroy GCP resources too."
    )

    st.markdown(f"**Current config:** `{CONFIG_PATH}`")

    if st.button("🔄 Reset to defaults"):
        fresh = default_config()
        save_config(fresh)
        st.session_state.config = fresh
        st.success(f"✅ Reset complete — profile: sandbox, project: {fresh['gcp_project']}")
        st.info("Next: Settings to choose a profile, then Bootstrap.")
        st.rerun()


# ── Page: Full Wizard ─────────────────────────────────────────────────────────

_WIZARD_PLAIN_LABELS = {
    "Settings": "Settings",
    "Prerequisites": "Check tools",
    "Bootstrap": "Google Cloud",
    "WIF Secrets": "GitHub link",
    "Scaffold": "Create service",
    "Publish": "Deploy",
    "MCP Config": "Claude (opt.)",
}


def _wizard_stepper_html(wizard_steps: list, current: int) -> str:
    parts = []
    for i, step in enumerate(wizard_steps):
        label = _WIZARD_PLAIN_LABELS.get(step, step)
        if i < current:
            cls = "gp-wizard-step gp-wiz-done"
            bubble = "✓"
        elif i == current:
            cls = "gp-wizard-step gp-wiz-current"
            bubble = str(i + 1)
        else:
            cls = "gp-wizard-step"
            bubble = str(i + 1)
        parts.append(
            f'<div class="{cls}">'
            f'<div class="gp-wiz-bubble">{bubble}</div>'
            f'<div class="gp-wiz-label">{label}</div>'
            f'</div>'
        )
    return f'<div class="gp-wizard-stepper">{"".join(parts)}</div>'


def page_full_wizard():
    render_page_header(
        "Guided Wizard",
        "Walk through each step in order — from settings to a live service.",
    )
    cfg = st.session_state.config

    wizard_steps = [
        "Settings",
        "Prerequisites",
        "Bootstrap",
        "WIF Secrets",
        "Scaffold",
        "Publish",
        "MCP Config",
    ]
    wizard_step = st.session_state.get("wizard_step", 0)
    total = len(wizard_steps)

    # Visual step indicator
    st.markdown(_wizard_stepper_html(wizard_steps, wizard_step), unsafe_allow_html=True)

    # Back / step counter / Skip controls
    nav_cols = st.columns([1, 4, 1])
    with nav_cols[0]:
        if wizard_step > 0 and st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = wizard_step - 1
            st.rerun()
    with nav_cols[1]:
        plain = _WIZARD_PLAIN_LABELS.get(wizard_steps[wizard_step], wizard_steps[wizard_step])
        st.markdown(
            f"<div style='text-align:center;color:#64748b;font-size:0.85rem;font-weight:600;"
            f"padding-top:0.35rem'>Step {wizard_step + 1} of {total} — {plain}</div>",
            unsafe_allow_html=True,
        )
    with nav_cols[2]:
        if wizard_step < total - 1 and st.button("Skip →", use_container_width=True):
            st.session_state.wizard_step = wizard_step + 1
            st.rerun()

    st.divider()

    if wizard_step == 0:
        st.markdown("#### 1. Configure your project")
        page_edit_settings(show_header=False)
        if st.button("Next →", key="wiz_next_0", type="primary"):
            st.session_state.wizard_step = 1
            st.rerun()

    elif wizard_step == 1:
        st.markdown("#### 2. Check your tools are installed")
        page_prerequisites(show_header=False)
        st.divider()
        if st.button("Next →", key="wiz_next_1", type="primary"):
            st.session_state.wizard_step = 2
            st.rerun()

    elif wizard_step == 2:
        st.markdown("#### 3. Set up Google Cloud")
        page_bootstrap(show_header=False)
        st.divider()
        if st.button("Next →", key="wiz_next_2", type="primary"):
            st.session_state.wizard_step = 3
            st.rerun()

    elif wizard_step == 3:
        st.markdown("#### 4. Connect GitHub to Google Cloud")
        page_wif_secrets(show_header=False)
        st.divider()
        if st.button("Next →", key="wiz_next_3", type="primary"):
            st.session_state.wizard_step = 4
            st.rerun()

    elif wizard_step == 4:
        st.markdown("#### 5. Create your service")
        page_scaffold(show_header=False)
        st.divider()
        if st.button("Next →", key="wiz_next_4", type="primary"):
            st.session_state.wizard_step = 5
            st.rerun()

    elif wizard_step == 5:
        st.markdown("#### 6. Deploy your service")
        page_publish(show_header=False)
        st.divider()
        if st.button("Next →", key="wiz_next_5", type="primary"):
            st.session_state.wizard_step = 6
            st.rerun()

    elif wizard_step == 6:
        st.markdown("#### 7. Connect Claude (optional)")
        page_mcp(show_header=False)
        st.divider()
        st.success("🎉 Wizard complete! Your service is set up.")
        st.markdown(
            "**What's next:**\n"
            "- Go to **Verify** to confirm your service is live\n"
            "- Return to **Dashboard** to see your progress overview"
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 Verify my service", type="primary", use_container_width=True):
                navigate_to("Verify")
        with c2:
            if st.button("↺ Restart wizard", use_container_width=True):
                st.session_state.wizard_step = 0
                st.rerun()


# ── App entrypoint ─────────────────────────────────────────────────────────────


def main():
    st.set_page_config(
        page_title="Golden Path · GCP Setup",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()

    if "config" not in st.session_state:
        st.session_state.config = load_config()
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 0
    if "prereqs_ok" not in st.session_state:
        st.session_state.prereqs_ok = False
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    st.session_state.config = load_config()
    page = render_sidebar()

    routes = {
        "Dashboard": page_dashboard,
        "Guided Wizard": page_full_wizard,
        "Settings": page_edit_settings,
        "Prerequisites": page_prerequisites,
        "Bootstrap": page_bootstrap,
        "WIF Secrets": page_wif_secrets,
        "Scaffold": page_scaffold,
        "Publish": page_publish,
        "Verify": page_verify,
        "Doctor": page_doctor,
        "MCP Config": page_mcp,
        "Teardown": page_teardown,
        "Fresh Start": page_fresh_start,
    }
    routes.get(page, page_dashboard)()


if __name__ == "__main__":
    main()

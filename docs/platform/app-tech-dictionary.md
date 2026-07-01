# goldenpath — app tech stack dictionary

> **Generated:** 2026-06-16 | **Version:** v0.3.7 (Phase 1 + Phase 2, enterprise-agnostic) — repo `goldenpath` (enterprise-agnostic)
>
> **How to use:** This document is a standalone, offline-ready reference for every technology used in the goldenpath platform. Browse by category, jump via the TOC, or `Ctrl+F` a term. Each entry is phrased to be directly quotable in technical articles and blog posts.

---

## Table of Contents

1. [Languages & Runtimes](#1-languages--runtimes)
   - [Bash](#bash)
   - [PowerShell (pwsh)](#powershell-pwsh)
   - [HCL (HashiCorp Configuration Language)](#hcl-hashicorp-configuration-language)
   - [Node.js](#nodejs)
   - [Python](#python)
   - [TypeScript](#typescript)
2. [Frontend Frameworks & Libraries](#2-frontend-frameworks--libraries)
   - [Next.js](#nextjs)
   - [React](#react)
   - [React DOM](#react-dom)
   - [Svelte](#svelte)
3. [Backend Frameworks & Libraries](#3-backend-frameworks--libraries)
   - [Express](#express)
   - [FastAPI](#fastapi)
   - [Streamlit](#streamlit)
   - [Uvicorn](#uvicorn)
4. [Build & Bundling Tools](#4-build--bundling-tools)
   - [@sveltejs/vite-plugin-svelte](#sveltejsvite-plugin-svelte)
   - [@vitejs/plugin-react](#vitejsplugin-react)
   - [npm](#npm)
   - [pip](#pip)
   - [Vite](#vite)
5. [MCP (Model Context Protocol) Stack](#5-mcp-model-context-protocol-stack)
   - [FastMCP](#fastmcp)
   - [MCP (Model Context Protocol)](#mcp-model-context-protocol)
   - [MCP Resources](#mcp-resources)
   - [MCP Tools](#mcp-tools)
   - [Server-Sent Events (SSE)](#server-sent-events-sse)
   - [Streamable HTTP Transport](#streamable-http-transport)
6. [Infrastructure as Code](#6-infrastructure-as-code)
   - [hashicorp/google Terraform Provider](#hashicorpgoogle-terraform-provider)
   - [Terraform](#terraform)
   - [Terraform Backend (GCS)](#terraform-backend-gcs)
   - [Terraform Modules](#terraform-modules)
   - [Workload Identity Federation (WIF)](#workload-identity-federation-wif)
7. [Google Cloud Platform Services](#7-google-cloud-platform-services)
   - [Google Artifact Registry](#google-artifact-registry)
   - [Google Cloud IAM](#google-cloud-iam)
   - [Google Cloud Logging](#google-cloud-logging)
   - [Google Cloud Monitoring](#google-cloud-monitoring)
   - [Google Cloud Run v2](#google-cloud-run-v2)
   - [Google Cloud Trace](#google-cloud-trace)
   - [Google Secret Manager](#google-secret-manager)
8. [CI/CD & Automation](#8-cicd--automation)
   - [actions/checkout](#actionscheckout)
   - [actions/setup-node](#actionssetup-node)
   - [actions/setup-python](#actionssetup-python)
   - [GitHub Actions](#github-actions)
   - [GitHub Actions Reusable Workflows](#github-actions-reusable-workflows)
   - [google-github-actions/auth](#google-github-actionsauth)
   - [google-github-actions/setup-gcloud](#google-github-actionssetup-gcloud)
   - [hashicorp/setup-terraform](#hashicorpsetup-terraform)
9. [Containerization](#9-containerization)
   - [Alpine Linux](#alpine-linux)
   - [Docker](#docker)
   - [Docker Multi-Stage Builds](#docker-multi-stage-builds)
   - [nginx](#nginx)
   - [python:3.12-slim](#python312-slim)
10. [Authentication & Security](#10-authentication--security)
    - [Application Default Credentials (ADC)](#application-default-credentials-adc)
    - [GitHub OIDC Provider](#github-oidc-provider)
    - [OIDC (OpenID Connect)](#oidc-openid-connect)
11. [Testing & Linting](#11-testing--linting)
    - [ESLint](#eslint)
    - [eslint-config-next](#eslint-config-next)
    - [httpx](#httpx)
    - [Node.js Built-in Test Runner](#nodejs-built-in-test-runner)
    - [pytest](#pytest)
    - [Ruff](#ruff)
    - [Pester](#pester)
12. [Developer Tools & CLIs](#12-developer-tools--clis)
    - [gcloud CLI](#gcloud-cli)
    - [gh CLI (GitHub CLI)](#gh-cli-github-cli)
    - [git](#git)
    - [shop CLI](#shop-cli)
    - [Setup Wizard (4 backends)](#setup-wizard-4-backends)
    - [check-repo-hygiene.sh](#check-repo-hygienesh)
13. [Type Definitions & Utilities](#13-type-definitions--utilities)
    - [@types/node](#typesnode)
    - [@types/react & @types/react-dom](#typesreact--typesreact-dom)
    - [google-auth](#google-auth)
    - [google-cloud-run (Python SDK)](#google-cloud-run-python-sdk)
14. [Platform-Specific Concepts](#14-platform-specific-concepts)
    - [Golden Path / Paved Road](#golden-path--paved-road)
    - [GOLDENPATH_MODULE_TOKEN](#goldenpath_module_token)
    - [Scale-to-Zero (Zero-Cost Profile)](#scale-to-zero-zero-cost-profile)
    - [Service Templates / Scaffolds](#service-templates--scaffolds)
    - [Skill (SKILL.md)](#skill-skillmd)
    - [Private Reusable Workflow Access](#private-reusable-workflow-access)
15. [Full Tech Stack Summary Table](#15-full-tech-stack-summary-table)
16. [How to Use This Dictionary](#16-how-to-use-this-dictionary)
17. [Limitations & Next Steps](#17-limitations--next-steps)

---

## 1. Languages & Runtimes

### Bash

**Definition:** Bash (Bourne Again SHell) is the default Unix shell and scripting language on Linux and macOS, widely used for automation, file manipulation, and glue logic between CLI tools.

**Origin/History:** Created by Brian Fox for the GNU Project in 1989 as a free replacement for the Bourne Shell (`sh`). It became the default shell on most Linux distributions and macOS (until zsh replaced it as macOS default in Catalina, 2019).

**Purpose in App:** Powers `cli/shop` (~475 lines), wizard bash backend (`goldenpath_setup.sh`), env/deploy launchers at `scripts/*.sh`, and `scripts/lib/*.sh` helpers. Orchestrates template copying, token substitution, GitHub publish, and WIF trust.

**Key Features:**

- Pipelines (`|`) chain commands without intermediate files
- `set -euo pipefail` turns on strict error handling (used in `shop`)
- Here-docs (`<<'EOF'`) for inline multi-line strings
- Subshell execution `$(...)` for capturing command output
- `find -print0 | while IFS= read -r -d '' file` for safe filename handling with spaces

**Pros:**

- Zero dependencies — available on every CI runner and developer machine
- Ideal for orchestrating other CLIs (gcloud, git, docker) with minimal overhead

**Cons:**

- No type system; silent failures without `set -e`
- Complex logic becomes hard to maintain at scale (mitigated by `scripts/lib/` shared helpers)

**Alternatives:** Python (used inline within `shop` for JSON parsing), Go (used by tools like `ko`), Makefile. Bash was chosen here for maximum portability and no install requirement.

**Resources:** `man bash`; `shellcheck` static analyzer for Bash scripts.

---

### PowerShell (pwsh)

**Definition:** PowerShell is a cross-platform task automation and configuration management framework from Microsoft, with a shell (`pwsh`) and scripting language built on .NET. PowerShell 7+ runs on macOS, Linux, and Windows.

**Origin/History:** Originally Windows-only (2006); open-sourced as PowerShell Core in 2016; unified as PowerShell 7 (2020). Install on macOS via `brew install powershell`.

**Purpose in App:** Canonical setup wizard (`scripts/setup/goldenpath-setup.ps1`) and building blocks (`scripts/setup/modules/*.ps1`). All backends share `goldenpath_ops.py` for scaffold, publish, doctor, and upgrade pins. Streamlit uses Python ops for those steps; `pwsh` modules handle bootstrap, verify, and teardown.

**Key Features:** `Invoke-GoldenPath*` functions for headless automation; dot-sourced modules; Pester tests in `tests/goldenpath-setup.tests.ps1`.

**Pros:** Rich GCP/GitHub automation; native on Windows.
**Cons:** Extra install on macOS/Linux; separate config from `shop` CLI.

**Alternatives:** Bash wizard (`goldenpath_setup.sh`), Python wizard (`goldenpath_setup.py`).

---

### HCL (HashiCorp Configuration Language)

**Definition:** HCL is a structured configuration language created by HashiCorp, designed to be human-readable while also being machine-parseable. It is the native language of Terraform and other HashiCorp tools.

**Origin/History:** Developed by HashiCorp (founded 2012) alongside Terraform. HCL 2 was introduced with Terraform 0.12 (2019), adding a richer expression syntax, `for` expressions, and `dynamic` blocks.

**Purpose in App:** All infrastructure in this platform is declared in HCL — the bootstrap (`platform/bootstrap/`), the five reusable modules (`modules/`), and the per-service `infra/main.tf` in every template. HCL describes GCP resources declaratively; Terraform handles the apply.

**Key Features:**

- Declarative `resource`, `module`, `variable`, `output`, and `locals` blocks
- `for_each` and `count` for resource iteration (used extensively in bootstrap)
- `dynamic` blocks for conditional sub-blocks (used in `cloud-run` module for `env` and `secret_env`)
- `precondition` lifecycle blocks for input validation at plan time
- Native functions: `coalesce()`, `substr()`, `replace()`, `setproduct()`

**Pros:**

- Readable by non-programmers; self-documenting with `description` fields
- Native Terraform tooling (fmt, validate, plan, apply)

**Cons:**

- Not a general-purpose language; complex logic requires workarounds
- Module `source` must be a string literal (no variables), which forces the token-replacement pattern in templates

**Alternatives:** Pulumi (TypeScript/Python/Go), CDK for Terraform (CDKTF), Google Cloud Deployment Manager YAML. HCL chosen because Terraform is the industry standard for GCP infrastructure.

**Resources:** `terraform fmt` auto-formats HCL; `terraform validate` type-checks before plan.

---

### Node.js

**Definition:** Node.js is a server-side JavaScript runtime built on Chrome's V8 engine, enabling JavaScript to run outside the browser for backend services, CLI tools, and build pipelines.

**Origin/History:** Created by Ryan Dahl in 2009. The Node.js Foundation (now OpenJS Foundation) manages it. Major LTS cadence: even-numbered versions (18, 20, 22) receive 3 years of LTS support.

**Purpose in App:** Runtime for the Express template (REST API) and Next.js template (SSR server). Also the host environment for Vite builds in the React SPA and Svelte SPA templates during CI.

**Key Features:**

- Non-blocking I/O via event loop — handles concurrent requests without threads
- npm ecosystem (largest package registry)
- Native ESM (`"type": "module"`) support — used in Express, React SPA, and Svelte SPA templates
- Built-in test runner (`node --test`) used across Node templates (no jest/mocha needed)

**Pros:**

- Single language (JS/TS) across frontend and backend
- Excellent Docker image availability (`node:20-alpine` is ~150MB)

**Cons:**

- CPU-bound work blocks the event loop
- `node_modules` size can be large; `npm ci` required for reproducible installs in CI

**Alternatives:** Deno, Bun. Node.js 20 chosen because it is the current LTS (until 2026-04-30).

**Resources:** `node --version` confirms runtime; `node --test` runs tests natively without a framework.

---

### Python

**Definition:** Python is a high-level, dynamically-typed, interpreted programming language celebrated for readable syntax, a rich standard library, and an enormous third-party ecosystem (PyPI).

**Origin/History:** Created by Guido van Rossum; first released in 1991. Python 3.0 (2008) broke backward compatibility with Python 2. Python 3.12 (released October 2023) adds significant performance improvements.

**Purpose in App:** Used for three distinct roles: (1) the FastAPI template's application code (`app/main.py`), (2) the Streamlit template's dashboard app (`app.py`), and (3) the entire MCP server package (`mcp/goldenpath_mcp/`). Python 3.11+ is required by the MCP server; templates use 3.12.

**Key Features:**

- Type hints (PEP 484+) — used throughout the MCP server (`from __future__ import annotations`)
- Dataclasses (`@dataclass(frozen=True)`) — used for immutable `Settings` in `config.py`
- `subprocess.run()` — used in `gcp.py` and `github_ops.py` for CLI delegation
- `pathlib.Path` — used throughout for safe, cross-platform path handling
- f-strings and dict unpacking (`**fields`) — used in `audit.py`

**Pros:**

- Dominant in data/ML/API tooling; Streamlit and FastAPI are Python-native
- `asyncio` support enables high-concurrency ASGI servers

**Cons:**

- Slower startup time vs. Node.js (noticeable in Cloud Run cold starts)
- Global interpreter lock (GIL) limits true CPU parallelism in CPython

**Alternatives:** Go (used by many platform CLIs), TypeScript/Node.js. Python chosen because FastAPI, Streamlit, and the MCP SDK are Python-first.

**Resources:** `python -m venv .venv` creates a local virtual environment; `pip install -e .` installs the MCP server in editable mode.

---

### TypeScript

**Definition:** TypeScript is a strongly-typed superset of JavaScript developed by Microsoft that compiles to plain JavaScript, adding optional static typing, interfaces, and generics to the language.

**Origin/History:** Released by Microsoft in 2012 (Anders Hejlsberg, lead architect of C#). Became the dominant language in the React/Next.js ecosystem by 2020. TypeScript 5.x (2023+) added decorator metadata and const type parameters.

**Purpose in App:** Used in the Next.js template — `tsconfig.json` configures strict mode, `@types/node`, `@types/react`, and `@types/react-dom` provide type definitions. The health route (`src/app/api/health/route.ts`) is typed.

**Key Features:**

- Static type checking catches bugs at compile time
- Excellent IDE autocomplete via language server (tsserver)
- Structural typing: if it has the right shape, it's compatible
- `strict` mode enables the most thorough checks

**Pros:**

- Catches an entire class of runtime errors before deployment
- Self-documenting — return types serve as living documentation

**Cons:**

- Adds a compilation step; `tsconfig.json` can be complex
- Type errors in third-party libraries can require `@ts-ignore` workarounds

**Alternatives:** JSDoc annotations (lighter weight, no compilation), plain JavaScript. TypeScript chosen because Next.js 14 recommends it by default.

**Resources:** `npx tsc --noEmit` type-checks without emitting files; `tsconfig.json` `strict: true` enables all strictness flags.

---

## 2. Frontend Frameworks & Libraries

### Next.js

**Definition:** Next.js is a React-based full-stack web framework by Vercel that provides server-side rendering (SSR), static site generation (SSG), and API routes in a unified project structure.

**Origin/History:** Created by Vercel (formerly ZEIT), first released in 2016. Version 13 (2022) introduced the App Router with React Server Components. Version 14 (2023) stabilized Server Actions and the standalone output mode.

**Purpose in App:** The default Golden Path template — `nextjs` is the template selected when no `--template` flag is provided. It scaffolds a Next.js 14 App Router project with a health endpoint at `/api/health`, a standalone Docker output, and a 3-stage multi-stage Dockerfile.

**Key Features:**

- App Router (`src/app/`) with file-system-based routing
- React Server Components render on the server, reducing client JS
- `next build --output standalone` creates a self-contained Node.js server (used in Dockerfile)
- `/api/health/route.ts` — API Route Handler pattern
- Built-in ESLint config (`eslint-config-next`) for Next.js-specific rules

**Pros:**

- Zero-config SSR + static generation + API in one framework
- Standalone build output is optimal for containers (no separate static file server needed)

**Cons:**

- Larger Docker image than a pure SPA; SSR adds latency on cold starts
- App Router has a steep learning curve vs. Pages Router

**Alternatives:** Remix, SvelteKit, Nuxt (Vue). Next.js chosen as the default because of industry adoption and the all-in-one deployment story.

**Resources:** `npm run dev` starts dev server; `npm run build && npm start` runs production locally.

---

### React

**Definition:** React is a declarative, component-based JavaScript library for building user interfaces, maintained by Meta (Facebook). It introduces a virtual DOM and a one-way data flow model.

**Origin/History:** Created by Jordan Walke at Facebook; open-sourced in 2013. React 16.8 (2019) introduced Hooks. React 18 (2022) added concurrent rendering and the `use` hook.

**Purpose in App:** Core UI library for both the Next.js template and the React SPA template. In Next.js, React 18 powers server and client components. In the React SPA, React renders the entire app client-side via Vite.

**Key Features:**

- JSX syntax: HTML-like markup embedded in JavaScript
- Component composition: build complex UIs from small, reusable pieces
- `useState`, `useEffect`, and other hooks manage local state and side effects
- Concurrent Mode (React 18): prioritizes rendering for smooth UX

**Pros:**

- Largest ecosystem of any UI library; extensive community and tooling
- Stable, predictable component model

**Cons:**

- JSX requires a build step (Babel/Vite)
- No built-in routing or state management — requires additional libraries (react-router, zustand, etc.)

**Alternatives:** Svelte (also in this platform), Vue.js, Solid.js. React chosen because of developer familiarity and Next.js integration.

**Resources:** `react-dom/client.createRoot()` mounts the app; React DevTools browser extension for debugging.

---

### React DOM

**Definition:** React DOM is the package that binds React to the browser DOM, providing the `createRoot` renderer and `hydrateRoot` for SSR hydration.

**Origin/History:** Split from the core `react` package in React 0.14 (2015) to enable React Native (which doesn't use the DOM) and other renderers.

**Purpose in App:** Used in the React SPA template (`src/main.jsx`) as the entry point: `createRoot(document.getElementById('root')).render(<App />)`. In the Next.js template, Next.js manages React DOM internally.

**Key Features:**

- `createRoot` (React 18): enables concurrent features
- `hydrateRoot`: attaches React to server-rendered HTML without re-rendering
- `flushSync`: synchronous state updates for edge cases

**Pros:** Thin abstraction — almost zero API surface beyond `createRoot`
**Cons:** Browser-only; `react-dom/server` is needed for SSR (handled by Next.js)

**Alternatives:** `react-native` for mobile, `react-three-fiber` for 3D. React DOM is the correct choice for all browser-based templates.

**Resources:** `package.json` — always version-lock `react` and `react-dom` together.

---

### Svelte

**Definition:** Svelte is a component-based JavaScript framework that compiles components to highly optimized vanilla JavaScript at build time, resulting in no runtime framework overhead in the browser.

**Origin/History:** Created by Rich Harris (New York Times), first released in 2016. Svelte 3 (2019) introduced the reactive `$:` declaration syntax. Svelte 4 (2023) focused on performance and TypeScript improvements.

**Purpose in App:** Powers the `svelte-spa` template — a client-side SPA served by nginx. Svelte compiles to static HTML/JS/CSS, which is then served as a static bundle.

**Key Features:**

- Compile-time reactivity: no virtual DOM, no diffing at runtime
- Single-file components (`.svelte`) contain script, template, and style
- Scoped CSS by default — no class-name collision risk
- `$:` reactive statements auto-rerun when dependencies change

**Pros:**

- Smallest bundle size of any major framework (no runtime shipped to browser)
- Simple, clean syntax with less boilerplate than React

**Cons:**

- Smaller ecosystem than React; fewer third-party component libraries
- Less IDE/TypeScript tooling maturity compared to React

**Alternatives:** React SPA (also in platform), Vue, Solid. Svelte included because it is the best choice for lightweight dashboards and internal tools.

**Resources:** `npm run dev` starts the Vite dev server; `.svelte` files are the primary unit of composition.

---

## 3. Backend Frameworks & Libraries

### Express

**Definition:** Express is a minimal, unopinionated web framework for Node.js that provides routing, middleware, and HTTP utility abstractions with a tiny footprint.

**Origin/History:** Created by TJ Holowaychuk in 2010, now maintained by the OpenJS Foundation. Express 4.x has been stable since 2014; version 5.x (2024) is the current major with full async support.

**Purpose in App:** Powers the `express` template — a Node.js REST API with a single health endpoint at `/api/health`. Used when teams want a lightweight Node.js API without the SSR overhead of Next.js.

**Key Features:**

- `app.get('/path', handler)` routing model
- Middleware chain: `app.use(middleware)` for request processing
- Native Node.js `http.IncomingMessage` / `http.ServerResponse` under the hood
- ESM-compatible in Express 4.21+ (`"type": "module"` in `package.json`)

**Pros:**

- Smallest possible footprint for a Node.js API
- Zero magic — every behavior is explicit middleware

**Cons:**

- No built-in validation, ORM, or authentication — requires assembling your own stack
- Async error handling requires wrapper middleware in Express 4

**Alternatives:** Fastify (faster, schema-based), Next.js API routes (if frontend is also Next.js), Hono. Express chosen for simplicity and universal familiarity.

**Resources:** `node src/index.js` runs the server; `app.listen()` binds to the port.

---

### FastAPI

**Definition:** FastAPI is a modern, high-performance Python web framework for building REST APIs, built on Python type hints and async-first design using the ASGI standard.

**Origin/History:** Created by Sebastián Ramírez (tiangolo), first released in 2018. FastAPI quickly became the most-starred Python web framework on GitHub. It is built on Starlette (ASGI toolkit) and Pydantic (data validation).

**Purpose in App:** Powers the `fastapi` template — a Python REST API with a health endpoint. FastAPI auto-generates OpenAPI docs at `/docs` from type annotations, and validates request/response models using Pydantic.

**Key Features:**

- Automatic OpenAPI (`/docs`) and JSON Schema (`/openapi.json`) generation
- `@app.get("/path")` decorator routing with type-annotated path/query parameters
- Dependency injection system via `Depends()`
- Async support (`async def`) for non-blocking I/O
- Pydantic models for request body validation

**Pros:**

- Near-zero boilerplate for a typed, documented API
- Auto-generated docs eliminate the need to maintain separate API documentation

**Cons:**

- Pydantic v2 migration (FastAPI 0.100+) has breaking changes from v1
- Slightly higher cold-start time than Flask due to Starlette initialization

**Alternatives:** Flask (lighter, synchronous), Django REST Framework (heavier, batteries-included). FastAPI chosen as the Python API standard for performance and type safety.

**Resources:** `uvicorn app.main:app --reload` runs with auto-reload; `http://localhost:8000/docs` shows Swagger UI.

---

### Streamlit

**Definition:** Streamlit is an open-source Python library that turns data scripts into interactive web apps with minimal code — no HTML, CSS, or JavaScript required.

**Origin/History:** Founded by Adrien Treuille, Thiago Teixeira, and Amanda Kelly; first released in 2019. Acquired by Snowflake in 2022. Version 1.38 (2024) added improved fragment rendering and performance optimizations.

**Purpose in App:** Powers the `streamlit` template for internal tools and dashboards. Engineers write Python scripts (`app.py`) using Streamlit's widget API; Streamlit automatically handles the web server, state management, and browser rendering.

**Key Features:**

- `st.write()`, `st.dataframe()`, `st.chart()` — one-line data display
- `st.button()`, `st.slider()`, `st.selectbox()` — reactive widgets with no JS
- Session state (`st.session_state`) for multi-step flows
- Automatic re-run on widget interaction

**Pros:**

- Data scientists can build production-grade internal tools without frontend skills
- Deep integration with pandas, matplotlib, Altair, and Plotly

**Cons:**

- Not suitable for high-concurrency public-facing apps
- Limited layout control compared to a proper frontend framework

**Alternatives:** Gradio (ML-focused), Panel, Dash (Plotly). Streamlit chosen for its adoption in data and analytics teams.

**Resources:** `streamlit run app.py` starts the server; health endpoint is `/_stcore/health` (built-in).

---

### Uvicorn

**Definition:** Uvicorn is a lightning-fast ASGI (Asynchronous Server Gateway Interface) web server for Python, designed for running async frameworks like FastAPI and Starlette.

**Origin/History:** Created by Tom Christie (also the author of Django REST Framework and Starlette), first released in 2018. ASGI itself was standardized by Django Channels.

**Purpose in App:** The production HTTP server for the FastAPI template. The Dockerfile `CMD` is `uvicorn app.main:app --host 0.0.0.0 --port 8000`. In the MCP server, Uvicorn is installed via `mcp[cli]` to support SSE transport.

**Key Features:**

- Built on `uvloop` (libuv-based event loop) and `httptools` for maximum throughput
- `--workers N` flag for multi-process mode (production)
- Supports HTTP/1.1 and WebSockets
- `--reload` flag for development auto-restart on file change

**Pros:**

- One of the fastest Python ASGI servers available
- Zero configuration for basic use — just `uvicorn module:app`

**Cons:**

- Single-process by default; needs `--workers` or `gunicorn` for CPU-bound parallelism
- Not suitable as a reverse proxy; should sit behind nginx or Cloud Run's ingress

**Alternatives:** Gunicorn (WSGI, older), Hypercorn (HTTP/2 support), Daphne. Uvicorn chosen because FastAPI officially recommends it.

**Resources:** `uvicorn --help` shows all flags; `pip show uvicorn` shows installed version.

---

## 4. Build & Bundling Tools

### @sveltejs/vite-plugin-svelte

**Definition:** The official Vite plugin for Svelte that integrates Svelte's compiler into the Vite build pipeline, enabling HMR, SSR, and production bundling for Svelte projects.

**Origin/History:** Developed by the SvelteKit team as the official bridge between Vite and Svelte. Replaced the older Rollup-based setup.

**Purpose in App:** Present in the `svelte-spa` template's `devDependencies`. It tells Vite how to compile `.svelte` files during `vite build` and `vite dev`.

**Key Features:** Single-file component compilation, hot module replacement for `.svelte` files, TypeScript support.

**Pros:** Zero configuration for standard Svelte projects.
**Cons:** Version coupling — must match Svelte major version.

**Alternatives:** `@sveltejs/kit` (for SSR), manual Rollup config. This plugin is correct for a client-only SPA.

---

### @vitejs/plugin-react

**Definition:** The official Vite plugin for React that adds JSX transformation (using the automatic React runtime) and React Fast Refresh for HMR.

**Origin/History:** Created by Evan You (also Vite's creator) as part of the Vite official plugins suite.

**Purpose in App:** Included in `react-spa` `devDependencies`. Enables `vite build` to process `.jsx` files and provides instant HMR during development.

**Key Features:** Automatic JSX runtime (no `import React` needed in every file), React Fast Refresh preserves component state across hot reloads.

**Pros:** Drop-in, zero-config for React + Vite. **Cons:** Babel-based by default (slightly slower than `@vitejs/plugin-react-swc` which uses Rust-based SWC).

**Alternatives:** `@vitejs/plugin-react-swc` (faster, uses SWC). Standard plugin chosen for broad compatibility.

---

### npm

**Definition:** npm (Node Package Manager) is the default package manager for Node.js, providing a CLI and the world's largest software registry (npmjs.com) with over 2 million packages.

**Origin/History:** Created by Isaac Schlueter in 2010 as the package manager bundled with Node.js. npm Inc. was acquired by GitHub (Microsoft) in 2020.

**Purpose in App:** Manages dependencies for all Node.js templates. `npm ci` (not `npm install`) is used in CI for reproducible, lockfile-respecting installs. The `npm run lint` and `npm test` scripts are called in the reusable CI workflow.

**Key Features:**

- `package.json` declares dependencies and scripts
- `package-lock.json` pins exact transitive dependency versions
- `npm ci` — clean install from lockfile, fails if `package.json` and lockfile diverge
- `--if-present` flag in scripts: run only if the script is defined (used in CI workflow)

**Pros:** Universal; comes with Node.js; `npm ci` is deterministic.
**Cons:** Slower than pnpm/yarn for large monorepos; `node_modules` can be very large.

**Alternatives:** pnpm (disk-efficient), Yarn Berry (workspaces). npm chosen for simplicity and zero additional tooling.

**Resources:** `npm ci` in CI; `npm install` in local dev; `npm run lint --if-present` in workflow.

---

### pip

**Definition:** pip (Package Installer for Python) is the standard package manager for Python, downloading packages from PyPI (the Python Package Index).

**Origin/History:** Replaced `easy_install` as the standard tool around 2013. Bundled with Python 3.4+. pip 23+ supports `--no-cache-dir` and `--require-hashes` for reproducible installs.

**Purpose in App:** Installs Python dependencies in all Python templates and the MCP server. `pip install --no-cache-dir -r requirements.txt` is the Dockerfile pattern used to keep image layers small.

**Key Features:**

- `requirements.txt` with pinned versions (`fastapi==0.115.0`)
- `pip install -e .` for editable installs (used for MCP server local dev via `.pth` file)
- `--no-cache-dir` reduces Docker layer size

**Pros:** Universal; works with any Python environment.
**Cons:** No lockfile format for transitive dependencies without additional tools (pip-tools, Poetry).

**Alternatives:** Poetry (lockfile + dependency resolution), uv (Rust-based, 10-100x faster). pip chosen for simplicity and Docker compatibility.

---

### Vite

**Definition:** Vite (French for "fast") is a next-generation frontend build tool that uses native ES modules for near-instant dev server startup and Rollup for optimized production bundles.

**Origin/History:** Created by Evan You (creator of Vue.js), first released in 2020. Vite 5 (2023) migrated to Rollup 4 and improved performance significantly.

**Purpose in App:** Build tool for the `react-spa` and `svelte-spa` templates. `vite build` produces a static bundle in `dist/`, which is copied into the nginx Docker image. `vite dev` provides HMR for local development.

**Key Features:**

- Dev server serves modules as native ESM — no bundling during development
- `vite build` uses Rollup for code splitting and tree-shaking
- Plugin system: `@vitejs/plugin-react` and `@sveltejs/vite-plugin-svelte`
- `vite preview` serves the production build locally for smoke testing

**Pros:**

- 10-100x faster dev server startup than webpack for large projects
- Zero-config for standard React/Svelte SPAs

**Cons:**

- Dev (ESM) and prod (Rollup bundle) environments differ slightly — rare subtle bugs
- Less mature plugin ecosystem than webpack for enterprise edge cases

**Alternatives:** webpack (Create React App), esbuild (lower-level), Parcel. Vite chosen for its developer experience and speed.

**Resources:** `vite.config.js` configures plugins; `npm run build` produces the `dist/` bundle.

---

## 5. MCP (Model Context Protocol) Stack

### FastMCP

**Definition:** FastMCP is a Python framework for building MCP (Model Context Protocol) servers with a decorator-based API, analogous to how FastAPI wraps ASGI. It is the reference Python implementation of the MCP server SDK.

**Origin/History:** Part of the official `mcp` Python SDK (`mcp[cli]` package), developed alongside the MCP specification by Anthropic. Version 1.6+ supports multiple transports.

**Purpose in App:** The core of the `goldenpath_mcp` package. `FastMCP("goldenpath")` creates the MCP app instance. `@mcp.tool()` decorators register **13 tools**; `@mcp.resource()` decorators register 3 virtual resource endpoints. `mcp.run(transport=...)` starts the server.

**Key Features:**

- `@mcp.tool()` — registers a Python function as an MCP tool callable by AI clients
- `@mcp.resource("goldenpath://path")` — registers a URI-addressable read-only resource
- Transport switching: `stdio`, `sse`, or `streamable-http` via `mcp.run(transport=...)`
- Automatic JSON schema generation from Python type annotations

**Pros:**

- Near-zero boilerplate: a function decorated with `@mcp.tool()` is instantly callable by AI
- Compatible with MCP clients (Claude Desktop, Claude Code, and other MCP-capable IDEs)

**Cons:**

- Relatively new (2024); API surface may change between minor versions
- No built-in auth middleware — must be added manually for SSE/HTTP transports

**Alternatives:** TypeScript MCP SDK, raw JSON-RPC over stdio. FastMCP chosen because the MCP SDK is Python-first for this platform.

**Resources:** `pip install mcp[cli]`; `goldenpath-mcp` entrypoint defined in `pyproject.toml`.

---

### MCP (Model Context Protocol)

**Definition:** MCP (Model Context Protocol) is an open protocol developed by Anthropic that standardizes how AI coding assistants (LLMs) discover and call tools, access resources, and use structured context from external systems.

**Origin/History:** Announced by Anthropic in November 2024. Designed to solve the "N×M integration problem" — instead of each AI tool building custom integrations with each data source, MCP provides one universal protocol. Supported by Claude Desktop, Claude Code, and a growing number of MCP-capable clients.

**Purpose in App:** The entire `mcp/` directory implements an MCP server that exposes the Golden Path platform API to AI agents. Claude (and other MCP clients) can call `scaffold_service()`, `list_templates()`, `trigger_deploy()`, etc. through standard MCP protocol messages.

**Key Features:**

- **Tools**: functions the AI can call (with parameters and return values)
- **Resources**: URI-addressed read-only content (like a virtual filesystem)
- **Prompts**: reusable prompt templates (not used in this app)
- **Transport**: stdio (local process), SSE (HTTP streaming), streamable-http

**Pros:**

- AI agents get structured, typed access to platform capabilities — no prompt engineering to extract JSON
- Completely decoupled: the MCP server is a standalone process the AI talks to

**Cons:**

- Ecosystem is very new; breaking protocol changes are possible
- Requires MCP-capable clients; traditional LLM APIs don't speak MCP

**Alternatives:** OpenAI function calling, LangChain tools, custom REST APIs. MCP chosen for standardization and native Claude MCP support.

**Resources:** MCP specification at `modelcontextprotocol.io`; `mcp dev` CLI for local testing.

---

### MCP Resources

**Definition:** MCP Resources are read-only, URI-addressable content endpoints served by an MCP server — analogous to a virtual filesystem that AI agents can browse and read.

**Purpose in App:** Three resource endpoints are registered:

- `goldenpath://meta/version` — returns channel/version metadata
- `goldenpath://docs/{path}` — serves Markdown docs from `docs/`
- `goldenpath://skills/{name}/SKILL.md` — serves agent skill instructions from `skills/`

**Key Features:** URI templating with `{path}` and `{name}` parameters; path traversal protection in `ContentStore._safe_path()`.

**Pros:** AI agents can introspect available content without knowing the filesystem structure.
**Cons:** Read-only — cannot be used to write or trigger actions.

**Resources:** See `content.py` for the `ContentStore` implementation.

---

### MCP Tools

**Definition:** MCP Tools are callable functions exposed by an MCP server that AI agents can invoke to perform actions, retrieve data, or trigger side effects — analogous to REST API endpoints for AI.

**Purpose in App:** 13 tools are registered in `server.py`:

| Tool | Type | Purpose |
|------|------|---------|
| `list_templates` | Read | Returns catalog.json |
| `list_skills` | Read | Lists available SKILL.md files |
| `get_skill` | Read | Returns a skill's full content |
| `get_doc` | Read | Returns a doc file |
| `list_docs` | Read | Lists all docs |
| `get_version` | Read | Returns channel/version |
| `list_services` | Read | Lists Cloud Run services |
| `get_deploy_status` | Read | Gets Cloud Run service status |
| `get_service_config` | Read | Gets Cloud Run config |
| `get_cost_estimate` | Read | Returns cost guidance |
| `scaffold_service` | **Write** (audited) | Calls shop CLI |
| `validate_service_repo` | Read | Validates directory structure |
| `trigger_deploy` | **Write** (audited) | Dispatches GitHub Actions |

**Key Features:** Write tools require `confirm=true`; all writes emit a JSON audit record via `audit.py`.

---

### Server-Sent Events (SSE)

**Definition:** SSE is an HTTP/1.1 standard for server-to-client streaming over a persistent HTTP connection, using `Content-Type: text/event-stream`. It is one-directional (server pushes to client) and simpler than WebSockets.

**Origin/History:** Part of the HTML5 specification (W3C, 2009). Natively supported in all modern browsers via `EventSource` API.

**Purpose in App:** One of three supported MCP transports. When `MCP_TRANSPORT=sse`, the MCP server runs as an HTTP server on `MCP_HOST:MCP_PORT` (default `0.0.0.0:8080`), enabling remote MCP clients to connect over a network. **Cloud Run hosting should use streamable-http at `/mcp`** — raw SSE is unreliable behind the load balancer (see `mcp/README.md`).

**Pros:** Works over standard HTTP; no WebSocket upgrade required; compatible with load balancers and Cloud Run.
**Cons:** One-directional; client must send requests over separate HTTP POST.

**Alternatives:** WebSockets (bidirectional), stdio (local only), streamable-http. SSE chosen for Cloud Run compatibility.

---

### Streamable HTTP Transport

**Definition:** Streamable HTTP is an MCP transport mode where both requests and responses are streamed over standard HTTP connections, enabling use in environments where SSE is not ideal.

**Purpose in App:** Third transport option in `server.py` (`MCP_TRANSPORT=streamable-http`). Used when clients need bidirectional streaming but SSE's one-directional limitation is an issue.

**Key Features:** Standard HTTP semantics; works with HTTP/2 multiplexing.
**Alternatives:** stdio (local), SSE (streaming push). Streamable HTTP is the most flexible option for networked deployments.

---

## 6. Infrastructure as Code

### hashicorp/google Terraform Provider

**Definition:** The `hashicorp/google` Terraform provider is the official plugin that maps Terraform HCL resource definitions to Google Cloud Platform API calls, managing the full lifecycle of GCP resources.

**Origin/History:** Maintained by HashiCorp and Google jointly. The provider is versioned separately from Terraform itself. Version 5.x (2023) introduced `google_cloud_run_v2_*` resources (replacing the deprecated v1 resources).

**Purpose in App:** Used in every Terraform configuration (bootstrap and all modules). All GCP resources (`google_cloud_run_v2_service`, `google_iam_workload_identity_pool`, `google_artifact_registry_repository`, etc.) are managed through this provider. Pinned to `>= 5.30.0`.

**Key Features:**

- `google_cloud_run_v2_service` — manages Cloud Run services with full v2 API support
- `google_iam_workload_identity_pool` and `_provider` — WIF setup
- `google_project_service` — enables GCP APIs programmatically
- `google_secret_manager_secret` and `_iam_member` — secrets + access control
- `google_monitoring_dashboard` and `google_monitoring_alert_policy`

**Pros:** Comprehensive GCP coverage; daily releases track new GCP features.
**Cons:** Breaking changes between major versions; `google_cloud_run_v2` replaced `google_cloud_run_service` in v5.

**Resources:** `terraform providers lock -platform=linux_amd64` pins provider checksums; `.terraform.lock.hcl` stores them.

---

### Terraform

**Definition:** Terraform is an open-source Infrastructure as Code (IaC) tool by HashiCorp that allows engineers to define, provision, and manage infrastructure across multiple cloud providers using a declarative configuration language (HCL).

**Origin/History:** Created by Mitchell Hashimoto and Armon Dadgar at HashiCorp; first released in 2014. HashiCorp changed Terraform's license to BSL 1.1 in 2023, prompting the OpenTF/OpenTofu fork. Terraform 1.5+ added `check` blocks and `import` enhancements.

**Purpose in App:** The exclusive infrastructure provisioning tool. The bootstrap Terraform sets up the GCP projects; each service repo's `infra/` directory contains Terraform that calls the platform modules. The CI workflow runs `terraform init`, `terraform plan`, and `terraform apply` on every deploy.

**Key Features:**

- `plan` shows a diff of changes before applying — safe preview
- `apply` executes the plan against the real infrastructure
- State file tracks what Terraform has created (critical for updates/deletes)
- Module system enables reuse: `source = "git::https://github.com/..."` fetches modules from git tags

**Pros:**

- Provider-agnostic: same workflow for GCP, AWS, Azure, Kubernetes
- `terraform plan` output is the primary audit trail for infrastructure changes

**Cons:**

- State file must be stored safely (remote backend recommended)
- Slow for large state files; `terraform apply` is synchronous

**Alternatives:** Pulumi (code-first IaC), Google Cloud Deployment Manager, CDK for Terraform. Terraform chosen because it is the industry standard for GCP infrastructure management.

**Resources:** `terraform fmt -recursive` formats all `.tf` files; `terraform validate` checks syntax before plan.

---

### Terraform Backend (GCS)

**Definition:** A Terraform backend defines where Terraform stores its state file. The GCS backend stores state in a Google Cloud Storage bucket, enabling team collaboration and locking.

**Purpose in App:** Commented out in `platform/bootstrap/versions.tf` — the platform currently uses local state. The `tfstate_bucket_name` variable exists to facilitate migration when a team is ready. When enabled, the backend configuration uses a GCS bucket with prefix-based state paths.

**Key Features:** State locking prevents concurrent applies; versioning on the GCS bucket enables state rollback.

**Pros:** Required for team workflows; prevents state divergence between engineers.
**Cons:** Chicken-and-egg problem — the bucket must exist before Terraform can use it as a backend.

**Resources:** `terraform init -migrate-state` migrates existing local state to remote.

---

### Terraform Modules

**Definition:** Terraform modules are reusable, self-contained packages of Terraform configuration that accept input variables and produce outputs, enabling DRY infrastructure composition.

**Origin/History:** Modules have been part of Terraform since early versions. Git-based module sources (`git::https://...?ref=tag`) were stabilized in Terraform 0.12.

**Purpose in App:** Five modules live in `modules/`: `artifact-registry`, `cloud-run`, `observability`, `secrets`, `service-identity`. Service repos reference them via git tag (`ref=v0.2.0`), ensuring all services use the same, versioned infrastructure definitions. The `_shared/infra/main.tf` template wires all five modules together.

**Key Features:**

- Input `variable` blocks define the module's interface
- `output` blocks expose values to the caller (e.g., `module.identity.email`)
- `source = "git::https://github.com/org/repo.git//modules/cloud-run?ref=v0.2.0"` pins to a git tag
- Module composition: `module.cloud_run.name` is passed to `module.observability`

**Pros:** Version-pinned modules enforce consistency across all service repos.
**Cons:** Module `source` must be a string literal — no variable interpolation allowed — which necessitates the `goldenpath` token replacement in templates.

---

### Workload Identity Federation (WIF)

**Definition:** Workload Identity Federation (WIF) is a GCP feature that allows external identities (e.g., GitHub Actions OIDC tokens) to authenticate to GCP services without long-lived service account keys.

**Origin/History:** Released by Google Cloud in 2021 as a response to the well-known security risk of storing service account JSON keys in CI systems.

**Purpose in App:** The keystone security mechanism of the platform. The bootstrap creates a WIF pool and provider that trust `token.actions.githubusercontent.com`. GitHub Actions exchanges a short-lived OIDC JWT for a GCP service account token via `google-github-actions/auth@v2`. No credentials are ever stored in GitHub Secrets — only the WIF provider resource name and service account email.

**Key Features:**

- OIDC attribute mapping: maps GitHub claims (`repository`, `ref`, `actor`) to GCP IAM conditions
- `attribute_condition`: `assertion.repository.startsWith('org/')` — trusts all org repos
- Short-lived tokens: OIDC tokens expire in 10 minutes; WIF tokens expire in 1 hour
- `roles/iam.workloadIdentityUser` allows token exchange
- `roles/iam.serviceAccountTokenCreator` allows Docker push via access token

**Pros:** Eliminates the #1 CI security risk (leaked SA keys); no credential rotation required.
**Cons:** Initial setup is more complex than a simple SA key; WIF pool must exist before CI can authenticate.

**Alternatives:** Service Account JSON key (anti-pattern; insecure). WIF is the correct and recommended approach.

**Resources:** `gcloud iam workload-identity-pools describe` inspects the pool; `wif.tf` is the authoritative source.

---

## 7. Google Cloud Platform Services

### Google Artifact Registry

**Definition:** Google Artifact Registry is a fully managed, regional Docker image and package registry on GCP that replaced Google Container Registry (GCR) as the recommended image storage solution.

**Origin/History:** GA in 2021. Replaced GCR (`gcr.io`) as the recommended registry. Supports Docker, Maven, npm, Python, and other formats.

**Purpose in App:** The exclusive Docker image registry. The CI workflow builds and pushes images to `{region}-docker.pkg.dev/{project}/{repo}/{name}:{sha}`. The `cloud-run` Terraform module enforces this with a `precondition` that rejects non-Artifact-Registry image URIs.

**Key Features:**

- Regional storage: images are stored in the same region as Cloud Run services
- IAM-based access: `roles/artifactregistry.writer` for CI push, `roles/artifactregistry.reader` for Cloud Run runtime
- Vulnerability scanning (optional, not configured in this platform)
- Retention policies for cleanup

**Pros:** Native GCP integration; no separate registry credentials; regional co-location reduces pull latency.
**Cons:** Slightly higher cost than GCR for high-volume registries.

**Resources:** `gcloud artifacts repositories list --project=PROJECT` lists repos.

---

### Google Cloud IAM

**Definition:** Google Cloud IAM (Identity and Access Management) is GCP's authorization system that controls who (identity) can do what (role) on which resource.

**Purpose in App:** Governs all access in the platform. The bootstrap assigns four roles to the `github-actions` SA: `roles/run.admin`, `roles/artifactregistry.writer`, `roles/iam.serviceAccountUser`, `roles/secretmanager.admin`. The `secrets` module grants `roles/secretmanager.secretAccessor` to the runtime SA.

**Key Features:** Role bindings, service accounts, custom roles, `principalSet://` for federated identities (used for WIF member references).

**Resources:** `gcloud projects get-iam-policy PROJECT` shows current bindings.

---

### Google Cloud Logging

**Definition:** Google Cloud Logging is a fully managed, real-time log management service that ingests, indexes, and stores logs from GCP services and custom applications.

**Purpose in App:** Enabled via `logging.googleapis.com` in the bootstrap API list. Cloud Run services automatically emit structured logs. The MCP server's `audit.py` writes JSON to stderr, which Cloud Run captures and routes to Cloud Logging as structured log entries.

**Key Features:** Log-based metrics, log sinks (export to BigQuery/GCS), structured JSON logs.

**Resources:** `gcloud logging read "resource.type=cloud_run_revision" --project=PROJECT` queries logs.

---

### Google Cloud Monitoring

**Definition:** Google Cloud Monitoring (formerly Stackdriver Monitoring) is GCP's observability platform providing metrics, dashboards, alerting, and SLO management.

**Purpose in App:** The `observability` Terraform module creates a monitoring dashboard with request count and p95 latency charts, plus a `high_error_rate` alert policy that fires when 5xx responses exceed 10 per minute for 5 minutes.

**Key Features:** `google_monitoring_dashboard` with mosaic layout, `google_monitoring_alert_policy` with `condition_threshold`, auto-close after 30 minutes of no data.

**Resources:** Cloud Console → Monitoring → Dashboards shows the provisioned dashboards.

---

### Google Cloud Run v2

**Definition:** Google Cloud Run is a fully managed, serverless container platform on GCP that automatically scales containers from zero to thousands of instances based on incoming requests.

**Origin/History:** Launched in 2019 (GA). Cloud Run v2 API (2022) adds support for VPC connectors, sidecars, and improved scaling controls. The `google_cloud_run_v2_service` Terraform resource maps to the v2 API.

**Purpose in App:** The exclusive compute platform for all services. Every deployed service runs as a Cloud Run service named `{service_name}-{environment}`. The `cloud-run` module configures scaling (min/max instances), health probes, resource limits, environment variables, and Secret Manager references.

**Key Features:**

- Scale-to-zero: `min_instance_count = 0` means no idle cost
- Request-based CPU billing: CPU only allocated during request handling
- `INGRESS_TRAFFIC_ALL`: accepts traffic from the internet (public services)
- Startup and liveness probes via HTTP GET to the health endpoint
- Secret injection: `value_source.secret_key_ref` mounts Secret Manager values as environment variables
- Labels: `managed_by = "goldenpath"` used by `gcp.py` to filter services

**Pros:** Zero infrastructure management; automatic HTTPS; pay-per-request pricing model.
**Cons:** Cold starts (1-3 seconds) when scaling from zero; maximum request timeout of 60 minutes.

**Resources:** `gcloud run services list --project=PROJECT --region=REGION` lists services.

---

### Google Cloud Trace

**Definition:** Google Cloud Trace is a distributed tracing system that captures latency data from applications and GCP services to identify performance bottlenecks.

**Purpose in App:** Enabled via `cloudtrace.googleapis.com` in the bootstrap. Cloud Run automatically sends trace data. Not explicitly instrumented in application code in the current templates but available for future use.

---

### Google Secret Manager

**Definition:** Google Secret Manager is a secure, managed storage service for API keys, passwords, certificates, and other sensitive configuration values, with versioning and fine-grained IAM access control.

**Purpose in App:** Stores per-service application secrets. The `secrets` Terraform module creates secrets named `{service}-{env}-{id}` and grants `roles/secretmanager.secretAccessor` to the service's runtime SA. Secrets are injected into Cloud Run containers via `secret_key_ref` in the `cloud-run` module.

**Key Features:** Automatic replication, version history, `latest` version alias, audit logging for every secret access.

**Pros:** Secrets never appear in environment variable definitions or Docker images — pulled at container startup.
**Cons:** Slight startup latency to fetch secrets; requires `secretmanager.googleapis.com` API enabled.

---

## 8. CI/CD & Automation

### actions/checkout

**Definition:** `actions/checkout` is the official GitHub Actions action that checks out the repository code into the runner workspace, making it available for subsequent steps.

**Origin/History:** Maintained by GitHub; v4 uses Node.js 20 runtime.

**Purpose in App:** First step of every job in the reusable deploy workflow. Required for Docker build, Terraform apply, and test steps.

**Key Features:** `fetch-depth: 1` for shallow clone (faster); handles submodules and LFS.

---

### actions/setup-node

**Definition:** The official GitHub Action for installing a specific version of Node.js on the CI runner, with optional npm cache restoration.

**Purpose in App:** Installed conditionally (`if: inputs.app_runtime == 'node'`) in the deploy workflow. Pins Node.js to `inputs.node_version` (default `20`) and caches the `npm` cache for faster installs.

---

### actions/setup-python

**Definition:** The official GitHub Action for installing a specific Python version on the CI runner, with optional pip cache restoration.

**Purpose in App:** Installed conditionally (`if: inputs.app_runtime == 'python'`). Pins Python to `inputs.python_version` (default `3.12`) and caches `pip` downloads.

---

### GitHub Actions

**Definition:** GitHub Actions is GitHub's native CI/CD platform that runs automated workflows on events (push, PR, schedule, manual dispatch) using YAML-defined job definitions on hosted or self-hosted runners.

**Origin/History:** Announced at GitHub Universe 2018; GA in November 2019. Became the dominant CI platform for GitHub-hosted projects by 2022.

**Purpose in App:** The exclusive CI/CD engine. Every service repo references the reusable `deploy.yml` from the `goldenpath` platform repo. Dev deploys trigger on `push` to `main`; prod deploys via `workflow_dispatch` with `environment=prod`.

**Key Features:**

- `workflow_call` trigger enables reusable workflows across repositories
- `permissions: id-token: write` is required for WIF OIDC token generation
- `environment:` block enforces deployment environment protection rules
- Secrets passed via `${{ secrets.NAME }}` are masked in logs

**Pros:** Native GitHub integration; free for public repos; large marketplace of actions.
**Cons:** YAML verbosity; debugging requires pushing commits or using `act` locally.

**Resources:** `gh run list` shows recent workflow runs; `gh run watch` streams live output.

---

### GitHub Actions Reusable Workflows

**Definition:** Reusable workflows are a GitHub Actions feature that allows a workflow YAML file to be called by other repositories via `uses: org/repo/.github/workflows/file.yml@ref`, enabling centralized CI logic shared across many repos.

**Origin/History:** Introduced in GitHub Actions in November 2021.

**Purpose in App:** The core distribution mechanism for the Golden Path CI. The single `deploy.yml` in `goldenpath` is referenced by every service repo. When the platform team updates the workflow (e.g., adds a new security scan), all service repos benefit on their next deploy without any changes. Service repos pin to `@v0.2.0` for stability.

**Key Features:**

- `on: workflow_call:` declares the workflow as reusable
- `inputs:` and `secrets:` define the contract
- `${{ inputs.service_name }}` accesses caller-provided values
- Cross-repo `uses:` with `@tag` pins to a specific version

**Pros:** Single source of truth for CI; consistent behavior across all services.
**Cons:** The calling repo must have Actions access to the `goldenpath` repo.

---

### google-github-actions/auth

**Definition:** The official Google-maintained GitHub Action for authenticating to GCP using Workload Identity Federation (OIDC), exchanging a GitHub OIDC token for a GCP service account access token.

**Origin/History:** Released by Google in 2021 alongside WIF GA. Version 2 supports both WIF and direct SA key authentication (key auth is discouraged).

**Purpose in App:** Step 4 of the deploy pipeline. Takes `workload_identity_provider` (the WIF pool provider resource name) and `service_account` (the CI SA email) as inputs, sets `GOOGLE_CREDENTIALS` in the environment, and configures `gcloud` automatically.

**Key Features:** Generates a short-lived (1 hour) access token; sets `CLOUDSDK_AUTH_ACCESS_TOKEN` for gcloud; supports file-based credential export.

---

### google-github-actions/setup-gcloud

**Definition:** GitHub Action that installs and configures the Google Cloud SDK (`gcloud` CLI) on the CI runner.

**Purpose in App:** Step 5 — enables `gcloud run services describe` for URL resolution and `gcloud auth print-access-token` for Docker registry login.

---

### hashicorp/setup-terraform

**Definition:** Official HashiCorp GitHub Action that installs a specific version of Terraform on the CI runner.

**Purpose in App:** Installs Terraform `1.5.7` (pinned) before the init/plan/apply steps. Pinning prevents unexpected behavior from Terraform version upgrades.

---

## 9. Containerization

### Alpine Linux

**Definition:** Alpine Linux is an ultra-minimal Linux distribution (~5MB) built on musl libc and BusyBox, widely used as a Docker base image for its small size and security surface.

**Origin/History:** Originally designed for embedded systems; adopted as a Docker base image standard around 2015 due to its size advantages.

**Purpose in App:** Used as the base for the Next.js template Dockerfile: `node:20-alpine`. The 3-stage build (`deps`, `builder`, `runner`) all use Alpine for minimal layer sizes.

**Pros:** ~150MB for `node:20-alpine` vs. ~950MB for `node:20`. **Cons:** musl libc can cause compatibility issues with some native Node.js addons.

---

### Docker

**Definition:** Docker is a platform for building, distributing, and running applications in lightweight, portable containers — isolated processes that package an application and its dependencies together.

**Origin/History:** Released by dotCloud (later renamed Docker Inc.) in 2013. Containerization transformed software deployment and led directly to Kubernetes and the cloud-native movement.

**Purpose in App:** Every service template includes a `Dockerfile`. The CI workflow runs `docker build` and `docker push` on every commit. The MCP server itself ships as a Docker image (`mcp/Dockerfile`) for Cloud Run SSE deployment.

**Key Features:**

- `COPY --from=stage` for multi-stage builds
- `USER` instruction for non-root runtime (used in all templates)
- `EXPOSE` documents the container port
- `ENV` sets environment variables baked into the image

**Pros:** Portable; reproducible; the exact same image runs in dev and prod.
**Cons:** Images can grow large without careful `.dockerignore` and layer optimization.

**Resources:** `docker build -t name .` builds; `docker run -p 3000:3000 name` runs locally.

---

### Docker Multi-Stage Builds

**Definition:** Multi-stage builds are a Docker pattern where a single `Dockerfile` contains multiple `FROM` stages, each producing an intermediate image, with only selected artifacts copied into the final lean image.

**Purpose in App:** Used in the Next.js template: stage 1 (`deps`) installs `node_modules`; stage 2 (`builder`) runs `npm run build`; stage 3 (`runner`) copies only the `standalone` output — no source code, no dev dependencies, no build tools. Result: a minimal production image.

**Key Features:** `COPY --from=deps` copies from a named previous stage; each stage is independent; only the final stage becomes the published image.

**Pros:** Final image excludes build tools, source code, and test dependencies — dramatically smaller and more secure.
**Cons:** Longer build times; cache invalidation requires care.

---

### nginx

**Definition:** nginx (pronounced "engine-x") is a high-performance, event-driven web server and reverse proxy, widely used for serving static files and load balancing.

**Origin/History:** Created by Igor Sysoev in 2004 to solve the C10k problem (handling 10,000 concurrent connections). Now maintained by F5.

**Purpose in App:** The production server for `react-spa` and `svelte-spa` templates. After `vite build` produces a static `dist/`, Docker copies it into `nginx:alpine` and serves it. The `nginx.conf` serves `index.html` as the SPA fallback (`try_files $uri $uri/ /index.html`) and exposes a `/health` endpoint.

**Key Features:**

- `try_files $uri $uri/ /index.html` — SPA client-side routing support
- `location /health { return 200 'ok'; }` — lightweight health check for Cloud Run probes
- `access_log off` on health endpoint — prevents noise in logs

**Pros:** Tiny runtime footprint; battle-tested for static file serving at massive scale.
**Cons:** No dynamic rendering; requires a separate API backend.

---

### python:3.12-slim

**Definition:** `python:3.12-slim` is an official Docker image from the Python Docker Hub repository — a Debian-based Python image with only the minimal packages needed to run Python, excluding documentation, tests, and most development tools.

**Purpose in App:** Base image for both the FastAPI template and the MCP server Dockerfile. `slim` reduces image size by ~60% vs. the full `python:3.12` image while retaining pip and standard library.

**Pros:** ~130MB vs. ~900MB for full Python image; includes Debian's glibc (better native extension compatibility than Alpine's musl).
**Cons:** Larger than `python:3.12-alpine` but more compatible.

---

## 10. Authentication & Security

### Application Default Credentials (ADC)

**Definition:** Application Default Credentials (ADC) is a GCP authentication strategy where client libraries automatically find credentials from a predefined chain: environment variables, `~/.config/gcloud/application_default_credentials.json`, and attached service accounts.

**Purpose in App:** Used for local development and testing. Platform engineers run `gcloud auth application-default login` before running `terraform apply` or the `standup-teardown-env.sh` scripts. The MCP server's `gcp.py` also relies on ADC when run locally.

**Key Features:** Transparent to application code; `GOOGLE_APPLICATION_CREDENTIALS` env var overrides the default location.

---

### GitHub OIDC Provider

**Definition:** GitHub's OIDC provider issues short-lived JSON Web Tokens (JWTs) to GitHub Actions workflows, containing claims about the repository, branch, and actor that triggered the run.

**Origin/History:** GitHub launched OIDC support for Actions in 2021, enabling keyless cloud authentication patterns.

**Purpose in App:** The issuer trusted by the WIF pool provider. `oidc { issuer_uri = "https://token.actions.githubusercontent.com" }` in `wif.tf` tells GCP to trust tokens from GitHub. The `permissions: id-token: write` in the workflow grants the job the right to request an OIDC token.

**Key Features:** Claims include `sub` (job identity), `repository` (org/repo), `ref` (branch/tag), `actor` (GitHub username).

---

### OIDC (OpenID Connect)

**Definition:** OpenID Connect is an identity layer built on top of OAuth 2.0 that enables parties to verify identity claims via digitally signed JWTs, without exchanging credentials.

**Origin/History:** Published by the OpenID Foundation in 2014. Built on top of OAuth 2.0 (RFC 6749). Adopted universally for SSO and federated identity.

**Purpose in App:** The underlying protocol for WIF. GitHub issues OIDC JWTs; GCP's WIF pool validates the signature against GitHub's public keys, extracts claims, and maps them to GCP IAM principals.

**Key Features:** JWTs contain verifiable, signed claims; short TTL (10 minutes for GitHub); public key discovery via `/.well-known/openid-configuration`.

---

## 11. Testing & Linting

### ESLint

**Definition:** ESLint is the dominant JavaScript/TypeScript static analysis tool that enforces code quality rules, catches common bugs, and maintains style consistency.

**Origin/History:** Created by Nicholas C. Zakas in 2013 as a more configurable alternative to JSHint. ESLint 8 (2021) is the version used here; ESLint 9 (2024) introduced the new flat config format.

**Purpose in App:** Used in the Next.js template. `npm run lint` calls `next lint` which uses `eslint-config-next`. The CI workflow runs `npm run lint --if-present`.

**Key Features:** Pluggable rules; `.eslintrc.json` config; `--fix` auto-corrects many issues.

---

### eslint-config-next

**Definition:** The official ESLint configuration for Next.js, bundling rules for React, React Hooks, accessibility (`jsx-a11y`), and Next.js-specific patterns.

**Purpose in App:** Referenced in `.eslintrc.json` as `"extends": "next/core-web-vitals"`. Enforces Core Web Vitals best practices in addition to standard React rules.

---

### httpx

**Definition:** httpx is a modern, async-capable Python HTTP client library — a drop-in replacement for the `requests` library with HTTP/2 support and async/await syntax.

**Purpose in App:** Installed in the CI Python test step (`pip install pytest httpx`) for integration testing of FastAPI services. The `tests/test_health.py` in the FastAPI template uses `httpx.AsyncClient` to hit the health endpoint.

**Pros:** Supports both sync and async; HTTP/2; type annotations. **Cons:** Slightly more complex than `requests` for simple use cases.

---

### Node.js Built-in Test Runner

**Definition:** Node.js 18+ ships a native test runner accessible via `node --test`, providing `describe`, `it`, and `assert` without any external testing library.

**Purpose in App:** Used in Express (`node --test tests/health.test.js`), React SPA, Svelte SPA, and Next.js (`node --test tests/health.test.mjs`). Eliminates the need for jest, mocha, or vitest in simple service health checks.

**Key Features:** `--test` flag; TAP-compatible output; parallel test execution; no config required.

**Pros:** Zero dependencies; included in Node.js 18+. **Cons:** Less feature-rich than jest for complex test suites.

---

### pytest

**Definition:** pytest is the de-facto standard testing framework for Python, providing a simple `assert`-based syntax, fixtures, parametrize, and a rich plugin ecosystem.

**Purpose in App:** Installed in CI for Python templates (`pip install pytest httpx`). `pytest -q` runs tests in the `tests/` directory. Test discovery is automatic for files matching `test_*.py`.

**Key Features:** Fixture dependency injection, `parametrize` for data-driven tests, `--tb=short` for compact tracebacks.

---

### Ruff

**Definition:** Ruff is an extremely fast Python linter written in Rust, capable of replacing Flake8, isort, pyupgrade, and dozens of other tools with a single binary.

**Origin/History:** Created by Charlie Marsh at Astral; first released in 2022. Became the most popular Python linter by 2024 due to 10-100x speed advantage over pure Python linters.

**Purpose in App:** Run in CI for Python templates: `pip install ruff && ruff check . --ignore E501 || true`. The `|| true` means lint failures do not block deployment (warnings only).

**Key Features:** Checks hundreds of rules in milliseconds; auto-fix with `--fix`; `pyproject.toml` configuration.

**Pros:** Single tool replaces many; Rust-speed means negligible CI time impact.
**Cons:** `|| true` in current CI means lint is advisory only — should be enforced.

---

### Pester

**Definition:** Pester is the de-facto testing and mocking framework for PowerShell, providing `Describe`/`It` blocks analogous to Jest or pytest.

**Origin/History:** Created by Scott Muc; Pester 5 (2020) rewrote the framework for PowerShell 7+ with improved discovery and mocking.

**Purpose in App:** `tests/goldenpath-setup.tests.ps1` validates PowerShell wizard logic (service name validation, config loading, module functions). Run via `tests/Run-SetupWizardTests.ps1` or `Invoke-Pester`.

**Key Features:** `Should` assertions; mocks for `gh`, `gcloud`, and external calls; integrates with CI when `pwsh` is available.

**Pros:** Only practical way to unit-test PowerShell wizard modules.
**Cons:** Requires `pwsh` + Pester install; not run in default GitHub Actions service deploy workflow.

---

## 12. Developer Tools & CLIs

### gcloud CLI

**Definition:** The `gcloud` CLI is the official Google Cloud command-line tool for managing GCP resources, authenticating to GCP, and interacting with Cloud Run, IAM, Artifact Registry, and other services.

**Purpose in App:** Used in two contexts: (1) the CI workflow (`gcloud auth print-access-token`, `gcloud run services describe`), and (2) the MCP server's `gcp.py` (`subprocess.run(["gcloud", ...])`). All GCP read operations in the MCP server delegate to gcloud rather than using the Python SDK directly.

**Key Features:** `--format=json` outputs JSON for programmatic parsing; `gcloud auth application-default login` sets up ADC; `gcloud run services describe` returns full service metadata.

---

### gh CLI (GitHub CLI)

**Definition:** `gh` is GitHub's official command-line tool for interacting with GitHub repositories, pull requests, issues, Actions, and APIs.

**Purpose in App:** Used in `github_ops.py` to dispatch GitHub Actions workflows: `gh api repos/{repo}/actions/workflows/{workflow}/dispatches -X POST`. The token is passed via `GH_TOKEN` environment variable.

**Key Features:** `gh api` makes authenticated GitHub API calls; `gh run list` shows workflow runs; `gh auth login` authenticates interactively.

---

### git

**Definition:** Git is the distributed version control system that tracks file changes, enables branching/merging, and underlies GitHub, GitLab, and most modern source control workflows.

**Purpose in App:** Used in three ways: (1) the `shop` CLI runs `git init && git add . && git commit` to create the initial commit in a scaffolded service repo; (2) the CI workflow uses `git config` to configure HTTPS auth for private Terraform module fetches; (3) Terraform uses `git::https://...?ref=tag` to fetch modules from the platform repo.

**Key Features:** `git config --global url."https://token@github.com/".insteadOf` — rewrites module source URLs for authenticated HTTPS access without modifying HCL.

---

### shop CLI

**Definition:** `cli/shop` is the Golden Path terminal CLI (Bash, ~475 lines) for scaffolding and deploying services. It reads `templates/catalog.json`, copies templates, replaces tokens, and orchestrates GitHub + GCP publish flows. Separate from the setup wizard — uses `.goldenpath-cli.local.json`.

**Origin/History:** Phase 1 (`shop new`, `shop list`); extended with `publish`, `verify`, `doctor`, `upgrade`, `config` for one-command deploy. Platform pin from `GOLDENPATH_VERSION` in `enterprise.env` (currently `v0.3.7`).

**Purpose in App:**

| Command | Purpose |
|---------|---------|
| `shop list` | Show templates from `catalog.json` |
| `shop config init\|show\|set` | Manage `.goldenpath-cli.local.json` |
| `shop new <name> [--template T]` | Scaffold + `git init -b main` |
| `shop publish <dir>` | Create **public** GitHub repo, WIF secrets, IAM trust, push `main`, watch deploy, verify health (fails if unhealthy). Wizard publish sets `GOLDENPATH_MODULE_TOKEN` when platform repo is private. |
| `shop verify <dir>` | Poll Cloud Run health via `scripts/lib/verify-deployment.sh` |
| `shop doctor <dir>` | Diagnose branch, secrets, tfvars project mismatch |

Also callable from MCP `scaffold_service` (wraps `shop new`).

**Key Features:**

- Token replacement via `scripts/lib/scaffold-tokens.sh` (shared with bash wizard)
- Sources `wif-trust-repo.sh` for per-repo WIF IAM bindings
- Private platform repo: auto-sets `GOLDENPATH_MODULE_TOKEN` from `gh auth token`
- Validates service name (lowercase kebab-case, 3–40 chars)

**Pros:** Full CLI path without PowerShell; proven streamlit e2e on `goldenpath-test`.
**Cons:** Do not mix with wizard config (`.goldenpath-setup.local.json`).

---

### Setup Wizard (4 backends)

**Definition:** The setup wizard is an interactive onboarding system with four parallel runtimes sharing menu options 1–15 and `.goldenpath-setup.local.json`.

**Purpose in App:**

| Backend | Entry | Implementation |
|---------|-------|----------------|
| PowerShell | `./scripts/goldenpath-setup-ps.sh` | `scripts/setup/goldenpath-setup.ps1` + `modules/*.ps1` |
| Bash | `./scripts/goldenpath-setup-bash.sh` | `goldenpath_setup.sh` + `goldenpath_setup_ops.sh` |
| Python | `./scripts/goldenpath-setup-py.sh` | `goldenpath_setup.py` + `goldenpath_ops.py` |
| Streamlit | `./scripts/goldenpath-setup-ui.sh` | `goldenpath_setup_app.py` (browser UI) |

Root `scripts/*.sh` files are thin launchers; logic lives in `scripts/setup/`. Bash/Python backends avoid `pwsh`. All backends share `goldenpath_ops` for scaffold, publish, doctor, and upgrade pins. Streamlit uses Python ops for scaffold/publish/doctor; `pwsh` modules remain for bootstrap, verify, and teardown.

**Alternatives:** `shop` CLI path — faster for experienced users; different config file.

---

### check-repo-hygiene.sh

**Definition:** `scripts/check-repo-hygiene.sh` is a platform-repo health script that detects accidental service scaffolds at repo root, validates workflow layout, and explains why `scripts/*.sh` launchers look like duplicates.

**Purpose in App:** Run `./scripts/check-repo-hygiene.sh` for hygiene check; `--explain` prints launcher → implementation map. Prevents platform repo pollution (e.g. stray `src/`, `package.json` at root).

**Key Features:** Checks README title, reusable `deploy.yml` shape, local temp files to delete; verifies launcher wiring to `setup/`, `env/`, `deploy/`.

---

## 13. Type Definitions & Utilities

### @types/node

**Definition:** TypeScript type definitions for the Node.js built-in APIs (`fs`, `path`, `http`, `process`, `Buffer`, etc.), published on the `@types` scope on npm.

**Purpose in App:** `devDependency` in the Next.js template. Enables TypeScript to understand Node.js globals without requiring explicit imports.

---

### @types/react & @types/react-dom

**Definition:** TypeScript type definitions for React and React DOM, published as `@types/react` and `@types/react-dom` on npm.

**Purpose in App:** `devDependencies` in the Next.js template. Provide full TypeScript autocompletion and type checking for JSX, hooks, event handlers, and component props.

---

### google-auth

**Definition:** The `google-auth` Python library provides authentication utilities for Google APIs, including OAuth 2.0, service account credentials, and Application Default Credentials.

**Purpose in App:** Listed as a dependency in `mcp/requirements.txt` (`google-auth>=2.29.0`). Provides the credential objects used by `google-cloud-run` SDK calls.

---

### google-cloud-run (Python SDK)

**Definition:** The `google-cloud-run` Python client library provides a programmatic interface to the Cloud Run Admin API for listing services, creating revisions, and managing traffic.

**Purpose in App:** Listed as a dependency in `mcp/requirements.txt` (`google-cloud-run>=0.10.0`). Included for potential future use — the current `gcp.py` uses `gcloud` CLI subprocess calls rather than the SDK directly, as the CLI is simpler and uses the caller's ADC transparently.

---

## 14. Platform-Specific Concepts

### Golden Path / Paved Road

**Definition:** A "Golden Path" (also called "paved road") is a platform engineering pattern where the platform team provides an opinionated, pre-configured, fully-supported default path for building and deploying services. It is not mandatory, but it is the easiest, safest, and most supported way to get something to production.

**Origin/History:** Popularized by Netflix, Spotify, and other large engineering organizations as an alternative to "platform mandates." The concept balances developer freedom with operational consistency.

**Purpose in App:** The entire philosophy of this platform. The Golden Path removes friction (no Dockerfile to write, no Terraform to learn, no CI to configure) while encoding best practices (WIF, scale-to-zero, Secret Manager, monitoring) by default.

---

### GOLDENPATH_MODULE_TOKEN

**Definition:** `GOLDENPATH_MODULE_TOKEN` is an optional GitHub Actions secret (or PAT — Personal Access Token) that the reusable CI workflow uses to authenticate Terraform's fetch of the goldenpath modules over HTTPS when the platform repo is private.

**Origin/History:** Added in recent commits (`be679d1`). Terraform module sources using `git::https://github.com/private-org/repo` require authentication; the `git config url.insteadOf` technique rewrites the URL to inject the token.

**Purpose in App:** Allows service repos to fetch versioned Terraform modules from a private `goldenpath` repo without storing a static credential. Falls back to `github.token` if not set (works when both repos are in the same org with Actions access enabled).

---

### Scale-to-Zero (Zero-Cost Profile)

**Definition:** Scale-to-zero is a Cloud Run configuration where `min_instance_count = 0`, meaning the service has no running instances when idle. Instances start on the first request (cold start) and shut down after a period of inactivity.

**Purpose in App:** The default cost profile for all Golden Path services (`zero_cost = true` in Cloud Run module). CPU billing is request-based (`cpu_idle = true`), meaning cost is near-zero for low-traffic services. The `cloud-run` module implements this as a conditional: when `zero_cost = true`, set `min_instances = 0`, `max_instances = var.max_instances_zero_cost`, `cpu = "0.5"`, `cpu_idle = true`, `startup_cpu_boost = false`.

---

### Service Templates / Scaffolds

**Definition:** Service templates are pre-built, token-parameterized project directories that represent the starting point for a new service. The `shop new` CLI copies a template and replaces tokens to produce a ready-to-deploy repository.

**Purpose in App:** Six templates in `templates/`: `nextjs`, `fastapi`, `streamlit`, `express`, `react-spa`, `svelte-spa`. Each contains a `Dockerfile`, `infra/` Terraform, `.github/workflows/deploy.yml`, `src/`, and `tests/`. Tokens (`{{SERVICE_NAME}}`, `{{GITHUB_ORG}}`, etc.) are replaced at scaffold time by `sed`.

---

### Skill (SKILL.md)

**Definition:** A Skill is a Markdown file (`SKILL.md`) that contains structured instructions for an AI agent, telling it exactly how to perform a platform workflow (scaffold, deploy, observe). Skills are served as MCP resources at `goldenpath://skills/{name}/SKILL.md`.

**Origin/History:** A convention established for this platform in Phase 2. Analogous to a runbook, but written specifically for AI agents rather than humans.

**Purpose in App:** Five official skills:

| Skill | Purpose |
|-------|---------|
| `goldenpath-setup-wizard` | Full wizard onboarding playbook |
| `scaffold-shop-service` | New service scaffold |
| `deploy-to-shop-gcp` | Deploy + troubleshoot |
| `shop-terraform-conventions` | Safe infra extensions |
| `shop-observability` | Logs, metrics, alerts |

When an AI agent loads a skill via `get_skill("deploy-to-shop-gcp")`, it receives the full runbook — troubleshooting tables, step-by-step instructions, and MCP tool names to call.

---

### Private Reusable Workflow Access

**Definition:** When a platform repo hosting a reusable GitHub Actions workflow is **private**, caller repos must also be **private** (same owner) and have workflow access granted, or GitHub returns "workflow was not found."

**Purpose in App:** When the platform repo is **private**, service repos must also be private (same owner) with workflow access granted. **Wizard publish** (menu **7**) matches platform visibility and sets `GOLDENPATH_MODULE_TOKEN` for module/workflow fetch. **`shop publish`** always creates a **public** repo today — use the wizard for private internal services. Pin workflows with `GOLDENPATH_VERSION` from `enterprise.env`.

**Key Features:** WIF trust per repo via `scripts/lib/wif-trust-repo.sh`; no long-lived GCP keys in GitHub.

**Pros:** Secure private platform; keyless CI via WIF.
**Cons:** Public service repos cannot call private reusable workflows — common pitfall caught by `shop doctor` / publish fixes.

---

## 15. Full Tech Stack Summary Table

| Element | Category | Brief Description | Version |
|---------|----------|-------------------|---------|
| Bash | Language/Runtime | Shell scripting for CLI + scripts | System (3.2+) |
| HCL | Language | Terraform configuration language | HCL 2 |
| Node.js | Language/Runtime | Server-side JavaScript runtime | 20 (LTS) |
| Python | Language/Runtime | Interpreted language for APIs + MCP | 3.11+ (MCP), 3.12 (templates) |
| TypeScript | Language | Typed JavaScript superset | ^5.4.0 |
| Next.js | Frontend Framework | React SSR + App Router framework | ^14.2.0 |
| React | Frontend Library | Declarative UI component library | ^18.3.0 |
| React DOM | Frontend Library | React browser renderer | ^18.3.0 |
| Svelte | Frontend Framework | Compile-time reactive UI framework | ^4.2.0 |
| Express | Backend Framework | Minimal Node.js web framework | ^4.21.0 |
| FastAPI | Backend Framework | Python ASGI REST API framework | 0.115.0 |
| Streamlit | Backend Framework | Python data app framework | 1.38.0 |
| Uvicorn | ASGI Server | Python ASGI HTTP server | 0.30.6 |
| @sveltejs/vite-plugin-svelte | Build Tool | Svelte compiler for Vite | ^3.1.0 |
| @vitejs/plugin-react | Build Tool | React JSX + HMR for Vite | ^4.3.0 |
| npm | Package Manager | Node.js package manager | bundled with Node 20 |
| pip | Package Manager | Python package manager | bundled with Python 3 |
| Vite | Build Tool | Next-gen frontend bundler | ^5.4.0 |
| FastMCP | MCP Framework | Python MCP server framework | >=1.6.0 |
| MCP | Protocol | AI tool/resource protocol | 1.6+ |
| SSE | Transport | Server-Sent Events HTTP stream | HTTP/1.1 standard |
| Terraform | IaC | Infrastructure as Code tool | >=1.5.0 |
| hashicorp/google | Terraform Provider | GCP resources for Terraform | >=5.30.0 |
| Workload Identity Federation | Auth | Keyless GCP CI authentication | GCP GA (2021) |
| Google Artifact Registry | GCP Service | Docker image registry | GA |
| Google Cloud IAM | GCP Service | Identity and access management | GA |
| Google Cloud Logging | GCP Service | Log management | GA |
| Google Cloud Monitoring | GCP Service | Metrics, dashboards, alerting | GA |
| Google Cloud Run v2 | GCP Service | Serverless container platform | v2 GA (2022) |
| Google Cloud Trace | GCP Service | Distributed tracing | GA |
| Google Secret Manager | GCP Service | Secrets storage and injection | GA |
| GitHub Actions | CI/CD | Automated workflow engine | N/A (hosted) |
| Reusable Workflows | CI/CD Pattern | Cross-repo workflow sharing | Actions feature (2021) |
| google-github-actions/auth | CI Action | WIF OIDC authentication | v2 |
| google-github-actions/setup-gcloud | CI Action | gcloud CLI installer | v2 |
| hashicorp/setup-terraform | CI Action | Terraform installer | v3 |
| Alpine Linux | Container Base | Minimal Linux for Docker | node:20-alpine |
| Docker | Containerization | Container build + distribution | N/A |
| Multi-Stage Builds | Docker Pattern | Minimal production images | Docker feature |
| nginx | Web Server | Static file server + reverse proxy | nginx:alpine |
| python:3.12-slim | Container Base | Debian Python minimal image | 3.12-slim |
| ADC | Auth | Application Default Credentials | GCP SDK feature |
| OIDC | Protocol | OpenID Connect identity protocol | 2014 standard |
| ESLint | Linter | JavaScript/TypeScript static analysis | ^8.57.0 |
| eslint-config-next | ESLint Config | Next.js lint rules | ^14.2.0 |
| httpx | Python Library | Async HTTP client for tests | bundled with mcp[cli] |
| Node test runner | Test Framework | Built-in Node.js test runner | Node 18+ |
| pytest | Test Framework | Python test framework | installed in CI |
| Ruff | Linter | Python linter (Rust-based) | installed in CI |
| gcloud CLI | Dev Tool | Google Cloud SDK CLI | system |
| gh CLI | Dev Tool | GitHub CLI | system |
| git | Dev Tool | Version control system | system |
| PowerShell (pwsh) | Language/Runtime | Setup wizard + PS modules | 7+ |
| Pester | Test Framework | PowerShell wizard unit tests | 5+ |
| shop CLI | Platform Tool | Scaffold + publish CLI (Bash) | `goldenpath_ops_cli.py`; pin `v0.3.7` |
| Setup Wizard | Platform Tool | 4 backends (PS/bash/py/Streamlit) | — |
| check-repo-hygiene.sh | Platform Tool | Repo layout health check | — |
| Private workflow access | Platform Concept | Private caller repos for private platform | — |
| google-auth | Python Library | GCP authentication library | >=2.29.0 |
| google-cloud-run SDK | Python Library | Cloud Run Admin API client | >=0.10.0 |
| Golden Path | Platform Concept | Opinionated developer platform pattern | — |
| GOLDENPATH_MODULE_TOKEN | Platform Config | Private module fetch PAT | — |
| Scale-to-Zero | GCP Pattern | Cloud Run zero idle cost profile | — |
| Skill (SKILL.md) | Platform Concept | AI agent runbook served via MCP | — |

---

## 16. How to Use This Dictionary

**For developers onboarding to the platform:**
Browse Section 14 (Platform-Specific Concepts) first to understand the Golden Path model, then read Section 6 (Infrastructure as Code) and Section 8 (CI/CD) to understand the deployment pipeline.

**For technical writers and bloggers:**
Each entry includes an "Origin/History" section designed to be directly quoted. For example: *"FastMCP, part of the official MCP SDK released by Anthropic in 2024, wraps an MCP server in a decorator-based Python API analogous to FastAPI."* Cross-reference entries — e.g., the WIF entry connects to OIDC, GitHub OIDC Provider, and google-github-actions/auth.

**For offline use:**
All definitions are self-contained. Version numbers are accurate as of 2026-06-16. Use `Ctrl+F` to find a specific technology; the TOC links to every section.

**For platform engineers evaluating replacements:**
Each entry lists alternatives with a note on why the current technology was chosen. The "Cons" sections identify legitimate weaknesses to address in Phase 3.

**Citing from this document:**
> *"Per the goldenpath platform analysis (2026): [quote]. Source: docs/app-tech-dictionary.md"*

---

## 17. Limitations & Next Steps

| Gap | Details | Suggested Action |
|-----|---------|-----------------|
| **Ruff version unpinned** | `pip install ruff` in CI installs latest, which may change behavior | Pin `ruff==X.Y.Z` in template `requirements-dev.txt` |
| **No lockfile for Python templates** | `requirements.txt` uses `==` for direct deps but not transitive | Add `pip-compile` or migrate to Poetry/uv for lockfile support |
| **google-cloud-run SDK unused** | Included in `requirements.txt` but `gcp.py` uses gcloud CLI subprocess instead | Either remove the dependency or migrate to SDK calls for testability |
| **ESLint 9 flat config** | Templates use ESLint 8 + `.eslintrc.json`; ESLint 9 uses `eslint.config.js` | Plan migration to ESLint 9 flat config with Next.js 15 upgrade |
| **No `@types/react` for React SPA** | The `react-spa` template uses JSX without TypeScript — no type checking | Add TypeScript + `@types/react` to the React SPA template as an option |
| **Hosted MCP auth** | `MCP_API_KEY` enforced via `auth.py` `ApiKeyMiddleware` on SSE/streamable-http only | Ensure key is set at Cloud Run deploy; stdio local mode has no API key gate |
| **Svelte 5 not yet adopted** | Platform uses Svelte 4; Svelte 5 (Runes API) was released in 2024 | Evaluate Svelte 5 migration for the svelte-spa template |
| **Full smoke matrix incomplete** | Streamlit e2e passed via CLI; `nextjs` + API templates pending cold pilot | Run `shop publish` for each template family; see [tests/README.md](../../tests/README.md) |
| **Doc drift** | Older docs referenced removed `docs/delivery/` paths | Use `docs/getting-started/`, `docs/environments/`, and `config/README.md` |

---

© 2026 Varanabox. All rights reserved.

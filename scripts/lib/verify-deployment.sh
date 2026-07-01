#!/usr/bin/env bash
# Cloud Run URL + health verification (shared by shop CLI and bash tooling).
# Usage: verify-deployment.sh <cloud-run-service> <gcp-project> <region> [service-dir] [repo-root]
set -euo pipefail

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
log() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }

[[ $# -ge 3 ]] || die "usage: verify-deployment.sh <service> <project> <region> [service-dir] [repo-root]"

SERVICE="$1"
PROJECT="$2"
REGION="$3"
SERVICE_DIR="${4:-}"
REPO_ROOT="${5:-}"

MAX_ATTEMPTS="${VERIFY_MAX_ATTEMPTS:-8}"
RETRY_DELAY="${VERIFY_RETRY_DELAY:-8}"

health_paths() {
  python3 - "$SERVICE_DIR" "$REPO_ROOT" <<'PY'
import json, os, re, sys

service_dir = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else ""
repo_root = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else ""
paths = []

def template_hint(d):
    req = os.path.join(d, "requirements.txt")
    if os.path.isfile(req):
        text = open(req).read()
        if re.search(r"(?m)^streamlit", text): return "streamlit"
        if re.search(r"(?m)^fastapi", text): return "fastapi"
    pkg = os.path.join(d, "package.json")
    if os.path.isfile(pkg):
        data = json.load(open(pkg))
        deps = set((data.get("dependencies") or {}) | (data.get("devDependencies") or {}))
        for name, key in [("nextjs", "next"), ("express", "express"), ("react-spa", "react"), ("svelte-spa", "svelte")]:
            if key in deps: return name
    return None

if service_dir and repo_root:
    catalog_path = os.path.join(repo_root, "templates", "catalog.json")
    tmpl = template_hint(service_dir)
    if tmpl and os.path.isfile(catalog_path):
        cat = json.load(open(catalog_path))
        if tmpl in cat:
            paths.append(cat[tmpl]["health_check_path"])
    deploy = os.path.join(service_dir, ".github", "workflows", "deploy.yml")
    if os.path.isfile(deploy):
        m = re.search(r'health[_-]?check[_-]?path["\s:=]+([/\w-]+)', open(deploy).read())
        if m and m.group(1) not in paths:
            paths.append(m.group(1))

for p in ("/api/health", "/health", "/_stcore/health"):
    if p not in paths:
        paths.append(p)
print("\n".join(paths))
PY
}

get_url() {
  gcloud run services describe "$SERVICE" \
    --project="$PROJECT" --region="$REGION" \
    --format='value(status.url)' 2>/dev/null || true
}

URL=""
attempt=1
while [[ $attempt -le $MAX_ATTEMPTS ]]; do
  [[ $attempt -gt 1 ]] && log "waiting for Cloud Run ($attempt/$MAX_ATTEMPTS)..."
  URL="$(get_url)"
  [[ -n "$URL" ]] && break
  [[ $attempt -lt $MAX_ATTEMPTS ]] && sleep "$RETRY_DELAY"
  attempt=$((attempt + 1))
done

if [[ -z "$URL" ]]; then
  printf 'VERIFY_URL=\nVERIFY_HEALTH_OK=false\nVERIFY_ERROR=service not found\n'
  exit 1
fi

HEALTH_OK=false
HEALTH_PATH=""
STATUS_CODE=""
PREVIEW=""

PATHS=()
while IFS= read -r _path; do
  [[ -n "$_path" ]] && PATHS+=("$_path")
done < <(health_paths)
attempt=1
while [[ $attempt -le $MAX_ATTEMPTS ]]; do
  for path in "${PATHS[@]}"; do
    [[ -z "$path" ]] && continue
    resp="$(curl -fsS -m 20 -w '\n%{http_code}' "${URL}${path}" 2>/dev/null || true)"
    code="${resp##*$'\n'}"
    body="${resp%$'\n'*}"
    if [[ "$code" =~ ^[23] ]]; then
      HEALTH_OK=true
      HEALTH_PATH="$path"
      STATUS_CODE="$code"
      PREVIEW="${body:0:200}"
      break 2
    fi
    warn "health ${path} not ready yet"
  done
  [[ $attempt -lt $MAX_ATTEMPTS ]] && sleep "$RETRY_DELAY"
  attempt=$((attempt + 1))
done

printf 'VERIFY_URL=%s\n' "$URL"
printf 'VERIFY_HEALTH_OK=%s\n' "$HEALTH_OK"
printf 'VERIFY_HEALTH_PATH=%s\n' "$HEALTH_PATH"
printf 'VERIFY_STATUS_CODE=%s\n' "$STATUS_CODE"
printf 'VERIFY_PREVIEW=%s\n' "$PREVIEW"
[[ "$HEALTH_OK" == "true" ]]
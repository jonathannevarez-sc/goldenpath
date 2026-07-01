#!/usr/bin/env bash
# Ensure active `gh` account matches configured GITHUB_ORG before publish.
# Usage: gh-auth-check.sh <expected-org-or-user>
set -euo pipefail

die() { printf 'error: %s\n' "$*" >&2; exit 1; }

[[ $# -eq 1 ]] || die "usage: gh-auth-check.sh <github-org-or-user>"

EXPECTED="$1"
command -v gh >/dev/null 2>&1 || die "gh CLI required — https://cli.github.com/"

ACTIVE="$(gh auth status 2>&1 | sed -n 's/.*account \([^ ]*\).*/\1/p' | head -1)"
[[ -n "$ACTIVE" ]] || die "not logged in to GitHub — run: gh auth login"

if [[ "$ACTIVE" != "$EXPECTED" ]]; then
  die "active gh account is '${ACTIVE}' but GITHUB_ORG is '${EXPECTED}' — run: gh auth switch --user ${EXPECTED}"
fi
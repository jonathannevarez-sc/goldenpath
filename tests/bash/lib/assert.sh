#!/usr/bin/env bash
# Minimal assertion helpers for Golden Path bash tests.
set -euo pipefail

TESTS_RUN=0
TESTS_FAILED=0
CURRENT_TEST=""
CURRENT_FAILED=0

test_start() {
  CURRENT_TEST="$1"
  CURRENT_FAILED=0
  TESTS_RUN=$((TESTS_RUN + 1))
}

test_end() {
  if [[ "${CURRENT_FAILED}" -eq 0 ]]; then
    printf '  ok: %s\n' "${CURRENT_TEST}"
  else
    printf '  FAIL: %s\n' "${CURRENT_TEST}"
  fi
}

assert_eq() {
  local expected="$1"
  local actual="$2"
  local message="${3:-}"
  if [[ "$expected" != "$actual" ]]; then
    CURRENT_FAILED=1
    TESTS_FAILED=$((TESTS_FAILED + 1))
    [[ -n "$message" ]] && printf '        %s\n' "$message"
    printf '        expected: %q\n' "$expected"
    printf '        actual:   %q\n' "$actual"
  fi
}

assert_match() {
  local pattern="$1"
  local actual="$2"
  local message="${3:-}"
  if ! [[ "$actual" =~ $pattern ]]; then
    CURRENT_FAILED=1
    TESTS_FAILED=$((TESTS_FAILED + 1))
    [[ -n "$message" ]] && printf '        %s\n' "$message"
    printf '        pattern: %q\n' "$pattern"
    printf '        actual:  %q\n' "$actual"
  fi
}

assert_exit() {
  local expected="$1"
  shift
  set +e
  "$@" >/dev/null 2>&1
  local code=$?
  set -e
  assert_eq "$expected" "$code" "exit code for: $*"
}

assert_file_exists() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    CURRENT_FAILED=1
    TESTS_FAILED=$((TESTS_FAILED + 1))
    printf '        missing file: %s\n' "$path"
  fi
}

assert_dir_has_no_tokens() {
  local dir="$1"
  local hits
  hits="$(find "$dir" -type f \
    ! -path '*/.git/*' ! -path '*/node_modules/*' ! -path '*/__pycache__/*' \
    -exec grep -l '{{[A-Z_]\+}}' {} + 2>/dev/null || true)"
  if [[ -n "$hits" ]]; then
    CURRENT_FAILED=1
    TESTS_FAILED=$((TESTS_FAILED + 1))
    printf '        unreplaced tokens in:\n%s\n' "$hits"
  fi
}

test_summary() {
  printf '\nBash tests: %s run, %s failed\n' "$TESTS_RUN" "$TESTS_FAILED"
  [[ "$TESTS_FAILED" -eq 0 ]]
}

# PATH for tests: keep common CLI tools but hide the real gh (present on GitHub Actions).
bash_test_path_without_gh() {
  local tmp="$1"
  local empty="${tmp}/empty-bin"
  local safe="${tmp}/safe-bin"
  mkdir -p "${empty}" "${safe}"
  local cmd path
  for cmd in bash git python3 grep sed dirname basename head read printf env cat cp rm mkdir mktemp; do
    path="$(command -v "$cmd" 2>/dev/null)" || continue
    ln -sf "$path" "${safe}/$(basename "$path")"
  done
  printf '%s:%s:/bin:/usr/sbin:/sbin' "${empty}" "${safe}"
}

# Stub gh for doctor tests (no live GitHub API).
bash_test_install_mock_gh() {
  local bin="$1"
  mkdir -p "${bin}"
  cat > "${bin}/gh" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"secret"* && "$*" == *"list"* ]]; then
  printf '%s\n' GCP_WIF_PROVIDER GCP_WIF_SERVICE_ACCOUNT
  exit 0
fi
if [[ "$*" == *"api"* && "$*" == *"repos/"* ]]; then
  echo "main"
  exit 0
fi
exit 0
EOF
  chmod +x "${bin}/gh"
}
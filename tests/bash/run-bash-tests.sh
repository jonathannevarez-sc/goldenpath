#!/usr/bin/env bash
# Run all Golden Path bash unit tests.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "Golden Path — Bash test runner"
echo "=============================="
echo ""

failed=0
for test_file in "${SCRIPT_DIR}"/test_*.sh; do
  [[ -f "$test_file" ]] || continue
  echo "Running $(basename "$test_file")"
  if bash "$test_file"; then
    echo ""
  else
    failed=$((failed + 1))
    echo ""
  fi
done

if [[ "$failed" -gt 0 ]]; then
  echo "${failed} bash test file(s) failed."
  exit 1
fi

echo "All bash test files passed."
exit 0
#!/usr/bin/env bash
# Alias: PowerShell wizard backend. Implementation: setup/goldenpath-setup.ps1
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/goldenpath-setup.sh" --backend ps "$@"
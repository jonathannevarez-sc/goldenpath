#!/usr/bin/env bash
# Alias: Python wizard backend. Implementation: setup/goldenpath_setup.py
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/goldenpath-setup.sh" --backend py "$@"
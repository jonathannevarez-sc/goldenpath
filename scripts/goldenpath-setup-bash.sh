#!/usr/bin/env bash
# Alias: bash wizard backend. Implementation: setup/goldenpath_setup.sh
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/goldenpath-setup.sh" --backend bash "$@"
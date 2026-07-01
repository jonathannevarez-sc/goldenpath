#!/usr/bin/env bash
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/deploy/import-mcp-infra-state.sh" "$@"
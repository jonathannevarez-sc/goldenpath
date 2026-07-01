#!/usr/bin/env bash
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/deploy/deploy-mcp-cloudrun.sh" "$@"
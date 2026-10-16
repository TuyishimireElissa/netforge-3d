#!/usr/bin/env bash
# Start the loopback-only desktop simulator bridge. No real networking tools.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
exec python3 -m backend.server "$@"

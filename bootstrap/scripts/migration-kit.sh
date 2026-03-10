#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="${SCRIPT_DIR}/../../migration-orchestrator/scripts/bootstrap/migration-kit.sh"

exec bash "${TARGET_SCRIPT}" "$@"

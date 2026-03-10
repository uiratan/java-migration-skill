#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage:
  migration-kit.sh start [repo-root]
  migration-kit.sh resume [repo-root]
  migration-kit.sh status [repo-root]

Commands:
  start   initialize the first-run output contract in docs/java-migration
  resume  show the minimum context required to resume the next session
  status  show whether docs/java-migration already exists and its current state
EOF
}

ROOT_DIR="${2:-.}"
MIGRATION_DIR="${ROOT_DIR%/}/docs/java-migration"
STATE_DIR="${MIGRATION_DIR}/state"

command_name="${1:-}"

case "${command_name}" in
  start)
    bash "${SCRIPT_DIR}/init-migration-kit.sh" "${ROOT_DIR}"
    echo
    bash "${SCRIPT_DIR}/show-next-session-context.sh" "${ROOT_DIR}"
    ;;
  resume)
    bash "${SCRIPT_DIR}/show-next-session-context.sh" "${ROOT_DIR}"
    ;;
  status)
    if [[ ! -d "${MIGRATION_DIR}" ]]; then
      echo "Migration output not initialized: ${MIGRATION_DIR}"
      echo "Run: ${SCRIPT_DIR}/migration-kit.sh start ${ROOT_DIR}"
      exit 0
    fi

    if [[ -f "${STATE_DIR}/project.state.json" && -f "${STATE_DIR}/active-milestone.json" && -f "${STATE_DIR}/session-handoff.md" ]]; then
      bash "${SCRIPT_DIR}/show-next-session-context.sh" "${ROOT_DIR}"
    else
      echo "Migration output reserved but not initialized: ${MIGRATION_DIR}"
      echo "Run: ${SCRIPT_DIR}/migration-kit.sh start ${ROOT_DIR}"
      exit 0
    fi
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    echo "Unknown command: ${command_name}" >&2
    usage >&2
    exit 1
    ;;
esac

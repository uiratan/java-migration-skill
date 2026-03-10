#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  validate-maven-scopes.sh --root PATH --scope PATH [--scope PATH ...]
                           [--goal GOAL]
                           [--run-dir DIR]

Examples:
  validate-maven-scopes.sh --root . --scope module-a
  validate-maven-scopes.sh --root . --scope module-a --scope module-b --goal compile
EOF
}

require_tool() {
  local tool="$1"
  if ! command -v "${tool}" >/dev/null 2>&1; then
    echo "Required tool not found: ${tool}" >&2
    exit 1
  fi
}

timestamp_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

ROOT_DIR="."
GOAL="test-compile"
RUN_DIR=""
declare -a SCOPES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT_DIR="${2:-}"; shift 2 ;;
    --scope) SCOPES+=("${2:-}"); shift 2 ;;
    --goal) GOAL="${2:-}"; shift 2 ;;
    --run-dir) RUN_DIR="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ ${#SCOPES[@]} -eq 0 ]]; then
  echo "At least one --scope is required" >&2
  exit 1
fi

ROOT_DIR="$(cd "${ROOT_DIR}" && pwd)"

if [[ -x "${ROOT_DIR}/mvnw" ]]; then
  MVN_CMD=("${ROOT_DIR}/mvnw")
  MAVEN_EXECUTOR="mvnw"
else
  require_tool "mvn"
  MVN_CMD=("mvn")
  MAVEN_EXECUTOR="mvn"
fi

if [[ -z "${RUN_DIR}" ]]; then
  RUN_DIR="${ROOT_DIR}/docs/java-migration/openrewrite-runs/validation-$(date -u +"%Y%m%dT%H%M%SZ")"
fi

mkdir -p "${RUN_DIR}"

LOG_FILE="${RUN_DIR}/validation.log"
SUMMARY_FILE="${RUN_DIR}/validation-summary.json"
PROJECT_CSV="$(IFS=,; echo "${SCOPES[*]}")"

declare -a CMD=(
  "${MVN_CMD[@]}"
  "-pl" "${PROJECT_CSV}"
  "-am"
  "-DskipTests=true"
  "${GOAL}"
)

printf 'timestamp=%s\n' "$(timestamp_utc)" > "${LOG_FILE}"
printf 'maven_executor=%s\n' "${MAVEN_EXECUTOR}" >> "${LOG_FILE}"
printf 'goal=%s\n' "${GOAL}" >> "${LOG_FILE}"
printf 'scopes=%s\n' "${PROJECT_CSV}" >> "${LOG_FILE}"
printf 'command=' >> "${LOG_FILE}"
printf '%q ' "${CMD[@]}" >> "${LOG_FILE}"
printf '\n' >> "${LOG_FILE}"

set +e
"${CMD[@]}" >> "${LOG_FILE}" 2>&1
EXIT_CODE=$?
set -e

python3 - "${SUMMARY_FILE}" "${GOAL}" "${PROJECT_CSV}" "${EXIT_CODE}" "${LOG_FILE}" "${MAVEN_EXECUTOR}" <<'PY'
import json
import pathlib
import sys

summary_file, goal, scopes, exit_code, log_file, maven_executor = sys.argv[1:]
log_path = pathlib.Path(log_file)
tail = ""
if log_path.exists():
    text = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = "\n".join(text[-40:])

payload = {
    "goal": goal,
    "scopes": [item for item in scopes.split(",") if item],
    "exit_code": int(exit_code),
    "status": "passed" if exit_code == "0" else "failed",
    "maven_executor": maven_executor,
    "log_file": str(log_path),
    "log_tail": tail,
}

pathlib.Path(summary_file).write_text(
    json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
    encoding="utf-8",
)
PY

printf 'Validation summary written to %s\n' "${SUMMARY_FILE}"
exit "${EXIT_CODE}"

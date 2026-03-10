#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run-openrewrite.sh --root PATH --scope PATH [--scope PATH ...]
                     [--recipe NAME ... | --recipe-set jakarta-ee]
                     [--validate-goal GOAL]
                     [--no-validate]
                     [--dry-run]
                     [--run-id ID]

Examples:
  run-openrewrite.sh --root . --scope module-a --recipe org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta
  run-openrewrite.sh --root . --scope module-a --scope module-b --recipe-set jakarta-ee --dry-run
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

timestamp_compact() {
  date -u +"%Y%m%dT%H%M%SZ"
}

ROOT_DIR="."
DRY_RUN="false"
RUN_ID=""
VALIDATE_AFTER_RUN="true"
VALIDATE_GOAL="test-compile"
RECIPE_SET_ID=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRESETS_DIR="${SCRIPT_DIR}/../../references/openrewrite/presets"
declare -a SCOPES=()
declare -a RECIPES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT_DIR="${2:-}"; shift 2 ;;
    --scope) SCOPES+=("${2:-}"); shift 2 ;;
    --recipe) RECIPES+=("${2:-}"); shift 2 ;;
    --recipe-set)
      RECIPE_SET_ID="${2:-}"
      PRESET_RECIPES="$(python3 "${SCRIPT_DIR}/resolve-recipe-set.py" "${PRESETS_DIR}" "${RECIPE_SET_ID}")"
      IFS=',' read -r -a PRESET_RECIPE_ARRAY <<< "${PRESET_RECIPES}"
      RECIPES+=("${PRESET_RECIPE_ARRAY[@]}")
      shift 2
      ;;
    --validate-goal) VALIDATE_GOAL="${2:-}"; shift 2 ;;
    --no-validate) VALIDATE_AFTER_RUN="false"; shift ;;
    --dry-run) DRY_RUN="true"; shift ;;
    --run-id) RUN_ID="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ ${#SCOPES[@]} -eq 0 ]]; then
  echo "At least one --scope is required" >&2
  exit 1
fi

if [[ ${#RECIPES[@]} -eq 0 ]]; then
  echo "At least one --recipe or --recipe-set is required" >&2
  exit 1
fi

require_tool "python3"

ROOT_DIR="$(cd "${ROOT_DIR}" && pwd)"

if [[ -z "${RUN_ID}" ]]; then
  RUN_ID="openrewrite-$(timestamp_compact)"
fi

RUNS_DIR="${ROOT_DIR}/docs/java-migration/openrewrite-runs"
RUN_DIR="${RUNS_DIR}/${RUN_ID}"
LOG_FILE="${RUN_DIR}/command.log"
SUMMARY_FILE="${RUN_DIR}/summary.json"
VALIDATION_SUMMARY_FILE="${RUN_DIR}/validation-summary.json"

mkdir -p "${RUN_DIR}"

if [[ -x "${ROOT_DIR}/mvnw" ]]; then
  MVN_CMD=("${ROOT_DIR}/mvnw")
  MAVEN_EXECUTOR="mvnw"
else
  require_tool "mvn"
  MVN_CMD=("mvn")
  MAVEN_EXECUTOR="mvn"
fi

RECIPE_CSV="$(IFS=,; echo "${RECIPES[*]}")"

declare -a PROJECT_LIST=()
for scope in "${SCOPES[@]}"; do
  PROJECT_LIST+=("${scope}")
done
PROJECT_CSV="$(IFS=,; echo "${PROJECT_LIST[*]}")"

declare -a CMD=(
  "${MVN_CMD[@]}"
  "-Drewrite.activeRecipes=${RECIPE_CSV}"
  "-Drewrite.exportDatatables=true"
  "-Drewrite.failOnDryRunResults=true"
  "-pl" "${PROJECT_CSV}"
  "org.openrewrite.maven:rewrite-maven-plugin:run"
)

if [[ "${DRY_RUN}" == "true" ]]; then
  CMD[-1]="org.openrewrite.maven:rewrite-maven-plugin:dryRun"
fi

printf 'timestamp=%s\n' "$(timestamp_utc)" > "${LOG_FILE}"
printf 'root=%s\n' "${ROOT_DIR}" >> "${LOG_FILE}"
printf 'run_id=%s\n' "${RUN_ID}" >> "${LOG_FILE}"
printf 'scopes=%s\n' "${PROJECT_CSV}" >> "${LOG_FILE}"
printf 'recipes=%s\n' "${RECIPE_CSV}" >> "${LOG_FILE}"
printf 'recipe_set_id=%s\n' "${RECIPE_SET_ID:-none}" >> "${LOG_FILE}"
printf 'dry_run=%s\n' "${DRY_RUN}" >> "${LOG_FILE}"
printf 'validate_after_run=%s\n' "${VALIDATE_AFTER_RUN}" >> "${LOG_FILE}"
printf 'validate_goal=%s\n' "${VALIDATE_GOAL}" >> "${LOG_FILE}"
printf 'maven_executor=%s\n' "${MAVEN_EXECUTOR}" >> "${LOG_FILE}"
printf 'command=' >> "${LOG_FILE}"
printf '%q ' "${CMD[@]}" >> "${LOG_FILE}"
printf '\n' >> "${LOG_FILE}"

set +e
"${CMD[@]}" >> "${LOG_FILE}" 2>&1
EXIT_CODE=$?
set -e

VALIDATION_STATUS="not_run"
VALIDATION_EXIT_CODE=0
if [[ "${DRY_RUN}" != "true" && "${EXIT_CODE}" -eq 0 && "${VALIDATE_AFTER_RUN}" == "true" ]]; then
  declare -a VALIDATION_CMD=(
    bash "${SCRIPT_DIR}/validate-maven-scopes.sh"
    --root "${ROOT_DIR}"
  )
  for scope in "${SCOPES[@]}"; do
    VALIDATION_CMD+=(--scope "${scope}")
  done
  VALIDATION_CMD+=(
    --goal "${VALIDATE_GOAL}"
    --run-dir "${RUN_DIR}"
  )
  set +e
  "${VALIDATION_CMD[@]}" >> "${LOG_FILE}" 2>&1
  VALIDATION_EXIT_CODE=$?
  set -e
  if [[ "${VALIDATION_EXIT_CODE}" -eq 0 ]]; then
    VALIDATION_STATUS="passed"
  else
    VALIDATION_STATUS="failed"
  fi
fi

python3 - "${SUMMARY_FILE}" "${RUN_ID}" "${PROJECT_CSV}" "${RECIPE_CSV}" "${RECIPE_SET_ID:-}" "${DRY_RUN}" "${EXIT_CODE}" "${VALIDATION_STATUS}" "${VALIDATION_EXIT_CODE}" "${VALIDATION_SUMMARY_FILE}" "${LOG_FILE}" "${MAVEN_EXECUTOR}" "${VALIDATE_GOAL}" "${VALIDATE_AFTER_RUN}" <<'PY'
import json
import pathlib
import sys

(
    summary_file,
    run_id,
    scopes,
    recipes,
    recipe_set_id,
    dry_run,
    exit_code,
    validation_status,
    validation_exit_code,
    validation_summary_file,
    log_file,
    maven_executor,
    validate_goal,
    validate_after_run,
) = sys.argv[1:]
log_path = pathlib.Path(log_file)
validation_summary_path = pathlib.Path(validation_summary_file)
tail = ""
if log_path.exists():
    text = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = "\n".join(text[-40:])

exit_code_int = int(exit_code)
validation_exit_code_int = int(validation_exit_code)

if dry_run == "true":
    status = "dry_run_clean" if exit_code_int == 0 else "dry_run_changes_or_failure"
    recommended_next_skill = "java-migration"
elif exit_code_int != 0:
    status = "rewrite_failed"
    recommended_next_skill = "java-migration"
elif validation_status == "failed":
    status = "rewrite_applied_validation_failed"
    recommended_next_skill = "java-migration"
else:
    status = "rewrite_applied_validation_passed"
    recommended_next_skill = "java-migration"

payload = {
    "summary_schema_version": "2.0",
    "run_id": run_id,
    "scopes": [item for item in scopes.split(",") if item],
    "recipes": [item for item in recipes.split(",") if item],
    "recipe_set_id": recipe_set_id or None,
    "dry_run": dry_run == "true",
    "rewrite_exit_code": exit_code_int,
    "validation_status": validation_status,
    "validation_exit_code": validation_exit_code_int,
    "validate_goal": validate_goal,
    "validate_after_run": validate_after_run == "true",
    "status": status,
    "recommended_next_skill": recommended_next_skill,
    "recommended_path": "last-mile" if status.startswith("rewrite_applied_validation") else "openrewrite",
    "log_file": str(log_path),
    "validation_summary_file": str(validation_summary_path) if validation_summary_path.exists() else "",
    "maven_executor": maven_executor,
    "log_tail": tail,
}

pathlib.Path(summary_file).write_text(
    json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
    encoding="utf-8",
)
PY

printf 'OpenRewrite summary written to %s\n' "${SUMMARY_FILE}"
exit "${EXIT_CODE}"

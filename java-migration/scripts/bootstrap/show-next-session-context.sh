#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
STATE_DIR="${ROOT_DIR%/}/docs/java-migration/state"
PROJECT_STATE="${STATE_DIR}/project.state.json"
MILESTONE_STATE="${STATE_DIR}/active-milestone.json"
HANDOFF_FILE="${STATE_DIR}/session-handoff.md"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROUTE_SCRIPT="${SCRIPT_DIR}/../state/resolve-state-route.py"

require_file() {
  local file="$1"
  if [[ ! -f "${file}" ]]; then
    echo "Missing required file: ${file}" >&2
    exit 1
  fi
}

require_file "${PROJECT_STATE}"
require_file "${MILESTONE_STATE}"
require_file "${HANDOFF_FILE}"

echo "Read these files in order:"
echo "- ${PROJECT_STATE}"
echo "- ${MILESTONE_STATE}"
echo "- ${HANDOFF_FILE}"
echo
echo "Current project state:"
python3 - "${PROJECT_STATE}" "${MILESTONE_STATE}" "${ROUTE_SCRIPT}" <<'PY'
import json
import subprocess
import sys

project_path, milestone_path, route_script = sys.argv[1], sys.argv[2], sys.argv[3]

with open(project_path, encoding="utf-8") as fh:
    project = json.load(fh)

with open(milestone_path, encoding="utf-8") as fh:
    milestone = json.load(fh)

route_result = subprocess.run(
    ["python3", route_script, project_path, milestone_path],
    capture_output=True,
    text=True,
    check=False,
)
route = json.loads(route_result.stdout)

print(f"- phase: {project['current_phase']}")
print(f"- operating_mode: {project.get('operating_mode', 'unknown')}")
print(f"- phase_status: {project.get('phase_status', 'unknown')}")
print(f"- next_skill: {project['next_skill']}")
print(f"- expected_skill: {route['expected_skill'] or 'unknown'}")
print(f"- route_status: {route['route_status']}")
print(f"- route_mode: {route['route_mode']}")
print(f"- build_system: {project.get('build_system', 'unknown')}")
print(f"- next_scope_ids: {', '.join(project['next_scope_ids']) or 'none'}")
print(f"- active_milestone: {milestone['milestone_id']}")
print(f"- milestone_status: {milestone['status']}")
print(f"- selected_scope_ids: {', '.join(milestone.get('selected_scope_ids', [])) or 'none'}")
print(f"- milestone_next_scope_ids: {', '.join(milestone.get('next_scope_ids', [])) or 'none'}")
for message in route.get("messages", []):
    print(f"- route_note: {message}")
PY
echo
echo "Then load only the ADRs and scope runs needed for the listed next scopes."

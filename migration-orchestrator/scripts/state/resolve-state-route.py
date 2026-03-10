#!/usr/bin/env python3
import json
import pathlib
import sys


PHASE_TO_SKILL = {
    "bootstrap_governance": "migration-bootstrap",
    "structured_discovery": "migration-discovery",
    "migration_planning": "migration-wave-planner",
    "automated_execution": "migration-openrewrite",
    "last_mile_fixes": "migration-last-mile-fixer",
    "stabilization": "migration-orchestrator",
}

PHASE_TO_MODE = {
    "bootstrap_governance": "bootstrap",
    "structured_discovery": "discover",
    "migration_planning": "plan",
    "automated_execution": "execute",
    "last_mile_fixes": "stabilize",
    "stabilization": "resume",
}

EXCEPTION_SKILLS = {
    "migration-transformer-fallback",
}


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: resolve-state-route.py <project.state.json> <active-milestone.json>",
            file=sys.stderr,
        )
        return 1

    project_state_path = pathlib.Path(sys.argv[1])
    milestone_state_path = pathlib.Path(sys.argv[2])

    for path in (project_state_path, milestone_state_path):
        if not path.exists():
            print(f"Missing required file: {path}", file=sys.stderr)
            return 1

    project_state = load_json(project_state_path)
    milestone_state = load_json(milestone_state_path)

    current_phase = project_state["current_phase"]
    next_skill = project_state["next_skill"]
    expected_skill = PHASE_TO_SKILL.get(current_phase)
    expected_mode = PHASE_TO_MODE.get(current_phase)
    project_next_scope_ids = project_state.get("next_scope_ids", [])
    milestone_next_scope_ids = milestone_state.get("next_scope_ids", [])
    build_system = project_state.get("build_system", "unknown")
    operating_mode = project_state.get("operating_mode", "unknown")
    phase_status = project_state.get("phase_status", "unknown")

    route_mode = "phase_default"
    route_status = "coherent"
    messages = []

    if expected_skill is None:
        route_status = "inconsistent"
        messages.append(f"unknown current_phase={current_phase}")
    elif next_skill == expected_skill:
        messages.append(f"phase {current_phase} routes to {next_skill}")
    elif next_skill in EXCEPTION_SKILLS:
        route_mode = "explicit_exception"
        messages.append(f"phase {current_phase} overridden by exception skill {next_skill}")
    else:
        route_status = "inconsistent"
        messages.append(
            f"phase {current_phase} expects {expected_skill} but state points to {next_skill}"
        )

    if expected_mode and operating_mode not in {expected_mode, "assess", "resume"}:
        route_status = "inconsistent"
        messages.append(
            f"phase {current_phase} expects operating_mode={expected_mode} but state has {operating_mode}"
        )

    if project_next_scope_ids != milestone_next_scope_ids:
        route_status = "inconsistent"
        messages.append("project.next_scope_ids diverges from milestone.next_scope_ids")

    if current_phase == "automated_execution" and build_system != "maven":
        route_status = "inconsistent"
        messages.append(
            f"automated_execution currently supports build_system=maven only, got {build_system}"
        )

    if phase_status == "blocked" and not project_state.get("global_blockers"):
        route_status = "inconsistent"
        messages.append("phase_status=blocked without global_blockers")

    if phase_status == "completed" and next_skill != "migration-orchestrator":
        messages.append(
            "phase marked completed; confirm whether a new milestone should be activated"
        )

    payload = {
        "current_phase": current_phase,
        "next_skill": next_skill,
        "expected_skill": expected_skill,
        "expected_mode": expected_mode,
        "operating_mode": operating_mode,
        "phase_status": phase_status,
        "route_mode": route_mode,
        "route_status": route_status,
        "project_next_scope_ids": project_next_scope_ids,
        "milestone_next_scope_ids": milestone_next_scope_ids,
        "messages": messages,
    }

    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if route_status == "coherent" else 2


if __name__ == "__main__":
    raise SystemExit(main())

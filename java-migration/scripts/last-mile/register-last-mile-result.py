#!/usr/bin/env python3
import argparse
import datetime
import json
import pathlib


def now_utc() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def append_phase_history(project_state: dict, now: str) -> None:
    entry = {
        "phase": project_state["current_phase"],
        "status": project_state["phase_status"],
        "reason": project_state["transition_reason"],
        "changed_at": now,
    }
    history = project_state.setdefault("phase_history", [])
    if not history or history[-1] != entry:
        history.append(entry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Register the outcome of last-mile fixes")
    parser.add_argument("project_state")
    parser.add_argument("milestone_state")
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--status", required=True, choices=("completed", "blocked", "in_progress"))
    parser.add_argument("--validation-status", default="not_run", choices=("not_run", "passed", "failed"))
    parser.add_argument("--validation-summary-file", default="")
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)
    project_state = json.loads(project_state_path.read_text(encoding="utf-8"))
    milestone_state = json.loads(milestone_state_path.read_text(encoding="utf-8"))
    now = now_utc()

    selected_scope_ids = args.scope or milestone_state.get("selected_scope_ids", [])
    milestone_state["selected_scope_ids"] = selected_scope_ids
    milestone_state["next_scope_ids"] = selected_scope_ids
    milestone_state["last_updated"] = now
    project_state["next_scope_ids"] = selected_scope_ids
    project_state["last_updated"] = now

    notes = project_state.get("notes", "")
    line = f"[{now}] last-mile status={args.status} scopes={','.join(selected_scope_ids) or 'none'} validation={args.validation_status}"
    if args.note:
        line = f"{line} note={args.note}"
    project_state["notes"] = f"{notes}\n{line}".strip()

    if args.status == "completed" and args.validation_status == "passed":
        project_state["operating_mode"] = "resume"
        project_state["current_phase"] = "stabilization"
        project_state["phase_status"] = "completed"
        project_state["next_skill"] = "java-migration"
        project_state["transition_reason"] = "Last-mile fixes validated successfully"
        milestone_state["status"] = "completed"
    elif args.status == "blocked" or args.validation_status == "failed":
        project_state["operating_mode"] = "stabilize"
        project_state["current_phase"] = "last_mile_fixes"
        project_state["phase_status"] = "blocked"
        project_state["next_skill"] = "java-migration"
        project_state["transition_reason"] = "Last-mile fixes remain blocked after validation"
        milestone_state["status"] = "blocked"
        blockers = project_state.setdefault("global_blockers", [])
        blocker = {
            "blocker_id": f"last-mile-blocked:{','.join(selected_scope_ids) or 'none'}",
            "severity": "high",
            "summary": "Residual migration breakage remains after manual fixes",
            "next_action": "Inspect failing validation output and continue last-mile work",
        }
        if blocker not in blockers:
            blockers.append(blocker)
    else:
        project_state["operating_mode"] = "stabilize"
        project_state["current_phase"] = "last_mile_fixes"
        project_state["phase_status"] = "in_progress"
        project_state["next_skill"] = "java-migration"
        project_state["transition_reason"] = "Last-mile fixes are still in progress"
        milestone_state["status"] = "in_progress"

    if args.validation_summary_file:
        artifact = args.validation_summary_file
        artifacts = milestone_state.setdefault("artifacts_required", [])
        if artifact not in artifacts:
            artifacts.append(artifact)

    append_phase_history(project_state, now)
    write_json(project_state_path, project_state)
    write_json(milestone_state_path, milestone_state)
    print(project_state["next_skill"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

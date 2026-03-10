#!/usr/bin/env python3
import datetime
import json
import pathlib
import sys


def now_utc() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
    if len(sys.argv) != 5:
        print(
            "Usage: register-openrewrite-result.py <project.state.json> <active-milestone.json> <summary.json> <next-skill>",
            file=sys.stderr,
        )
        return 1

    project_state_path = pathlib.Path(sys.argv[1])
    milestone_state_path = pathlib.Path(sys.argv[2])
    summary_path = pathlib.Path(sys.argv[3])
    next_skill = sys.argv[4]

    for path in (project_state_path, milestone_state_path, summary_path):
        if not path.exists():
            print(f"Missing required file: {path}", file=sys.stderr)
            return 1

    project_state = load_json(project_state_path)
    milestone_state = load_json(milestone_state_path)
    summary = load_json(summary_path)
    now = now_utc()

    notes = project_state.get("notes", "")
    note_line = (
        f"[{now}] openrewrite run_id={summary['run_id']} "
        f"status={summary['status']} scopes={','.join(summary.get('scopes', [])) or 'none'} "
        f"recipes={','.join(summary.get('recipes', [])) or 'none'} "
        f"validation={summary.get('validation_status', 'not_run')}"
    )
    project_state["notes"] = f"{notes}\n{note_line}".strip()

    project_state["next_scope_ids"] = summary.get("scopes", [])
    milestone_state["selected_scope_ids"] = summary.get("scopes", [])
    milestone_state["next_scope_ids"] = summary.get("scopes", [])

    if summary["status"] == "rewrite_applied_validation_passed":
        project_state["operating_mode"] = "stabilize"
        project_state["current_phase"] = "last_mile_fixes"
        project_state["phase_status"] = "in_progress"
        project_state["next_skill"] = next_skill
        project_state["transition_reason"] = "Automation completed cleanly; inspect residual manual follow-up"
        milestone_state["status"] = "in_progress"
    elif summary["status"] == "rewrite_applied_validation_failed":
        project_state["operating_mode"] = "stabilize"
        project_state["current_phase"] = "last_mile_fixes"
        project_state["phase_status"] = "blocked"
        project_state["next_skill"] = next_skill
        project_state["transition_reason"] = "Automation applied but validation failed; residual fixes required"
        blocker = {
            "blocker_id": f"openrewrite-validation-failed:{summary['run_id']}",
            "severity": "high",
            "summary": "OpenRewrite changes compiled into a failing validation state",
            "next_action": "Inspect validation summary and route residual issues to last-mile fixes",
        }
        blockers = project_state.setdefault("global_blockers", [])
        if blocker not in blockers:
            blockers.append(blocker)
        milestone_state["status"] = "blocked"
    elif summary["status"].startswith("dry_run_"):
        project_state["operating_mode"] = "execute"
        project_state["current_phase"] = "automated_execution"
        project_state["phase_status"] = "in_progress"
        project_state["next_skill"] = "migration-openrewrite"
        project_state["transition_reason"] = "Dry run completed; decide whether to apply recipes"
        milestone_state["status"] = "in_progress"
    else:
        project_state["operating_mode"] = "execute"
        project_state["current_phase"] = "automated_execution"
        project_state["phase_status"] = "blocked"
        project_state["next_skill"] = "migration-openrewrite"
        project_state["transition_reason"] = "Automation failed and requires recipe or scope review"
        blocker = {
            "blocker_id": f"openrewrite-failed:{summary['run_id']}",
            "severity": "high",
            "summary": "OpenRewrite execution failed before a stable post-run state",
            "next_action": "Inspect the run log and reduce recipe batch or scope size",
        }
        blockers = project_state.setdefault("global_blockers", [])
        if blocker not in blockers:
            blockers.append(blocker)
        milestone_state["status"] = "blocked"

    project_state["last_updated"] = now
    milestone_state["last_updated"] = now
    append_phase_history(project_state, now)

    write_json(project_state_path, project_state)
    write_json(milestone_state_path, milestone_state)
    print(project_state["next_skill"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

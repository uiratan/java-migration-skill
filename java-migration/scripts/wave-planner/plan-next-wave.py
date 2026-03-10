#!/usr/bin/env python3
import csv
import datetime
import json
import pathlib
import sys


def now_utc() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_summary_state(path: pathlib.Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        key, value = line.split("\t", 1)
        data[key] = value
    return data


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
            "Usage: plan-next-wave.py <project.state.json> <active-milestone.json> <scopes.csv> <runs-dir>",
            file=sys.stderr,
        )
        return 1

    project_state_path = pathlib.Path(sys.argv[1])
    milestone_state_path = pathlib.Path(sys.argv[2])
    scopes_csv_path = pathlib.Path(sys.argv[3])
    runs_dir = pathlib.Path(sys.argv[4])

    project_state = json.loads(project_state_path.read_text(encoding="utf-8"))
    milestone_state = json.loads(milestone_state_path.read_text(encoding="utf-8"))

    ready: list[str] = []
    manual_only: list[str] = []
    blocked: list[str] = []
    deferred: list[str] = []

    with scopes_csv_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            scope_id = row["scope_id"]
            summary = read_summary_state(runs_dir / scope_id / "summary.state")
            if not summary:
                continue
            status = summary.get("STATUS", "pending")
            if status == "blocked":
                blocked.append(scope_id)
                continue
            if status != "completed":
                deferred.append(scope_id)
                continue
            if summary.get("REQUIRES_HUMAN_DECISION") == "true":
                deferred.append(scope_id)
                continue
            eligibility = summary.get("AUTOMATION_ELIGIBILITY", "unknown")
            if eligibility == "openrewrite_ready":
                ready.append(scope_id)
            elif eligibility == "manual_only":
                manual_only.append(scope_id)
            else:
                deferred.append(scope_id)

    next_scope_ids = ready[:3]
    now = now_utc()

    milestone_state["selected_scope_ids"] = next_scope_ids
    milestone_state["next_scope_ids"] = next_scope_ids
    milestone_state["deferred_scope_ids"] = sorted(set(manual_only + deferred))
    milestone_state["blocked_scope_ids"] = blocked
    milestone_state["status"] = "blocked" if blocked and not next_scope_ids else "in_progress"
    milestone_state["last_updated"] = now

    project_state["next_scope_ids"] = next_scope_ids
    project_state["last_updated"] = now

    blockers = project_state.setdefault("global_blockers", [])
    if blocked:
        blocker = {
            "blocker_id": "wave-planning-blocked-scopes",
            "severity": "high",
            "summary": "Some scopes remain blocked and cannot be promoted into an execution wave",
            "next_action": "Inspect blocked discovery runs before execution",
        }
        if blocker not in blockers:
            blockers.append(blocker)

    if next_scope_ids:
        project_state["operating_mode"] = "execute"
        project_state["current_phase"] = "automated_execution"
        project_state["phase_status"] = "in_progress"
        project_state["next_skill"] = "java-migration"
        project_state["transition_reason"] = "Discovery evidence is sufficient to promote the next execution wave"
    elif manual_only:
        project_state["operating_mode"] = "stabilize"
        project_state["current_phase"] = "last_mile_fixes"
        project_state["phase_status"] = "in_progress"
        project_state["next_skill"] = "java-migration"
        project_state["transition_reason"] = "No safe automated wave available; hand-fix work is next"
    else:
        project_state["operating_mode"] = "plan"
        project_state["current_phase"] = "migration_planning"
        project_state["phase_status"] = "blocked" if blocked else "in_progress"
        project_state["next_skill"] = "java-migration"
        project_state["transition_reason"] = "Planning could not promote a safe execution wave yet"

    append_phase_history(project_state, now)

    project_state_path.write_text(json.dumps(project_state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    milestone_state_path.write_text(json.dumps(milestone_state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(",".join(next_scope_ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

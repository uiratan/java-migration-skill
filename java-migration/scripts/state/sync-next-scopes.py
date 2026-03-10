#!/usr/bin/env python3
import csv
import datetime
import json
import pathlib
import sys
from typing import Dict, List


def read_summary_state(path: pathlib.Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path.exists():
        return data

    for line in path.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        key, value = line.split("\t", 1)
        data[key] = value
    return data


def append_phase_history(project_state: dict, now: str, reason: str) -> None:
    entry = {
        "phase": project_state["current_phase"],
        "status": project_state["phase_status"],
        "reason": reason,
        "changed_at": now,
    }
    history = project_state.setdefault("phase_history", [])
    if not history or history[-1] != entry:
        history.append(entry)


def main() -> int:
    if len(sys.argv) != 5:
        print(
            "Usage: sync-next-scopes.py <project.state.json> <active-milestone.json> <scopes.csv> <runs-dir>",
            file=sys.stderr,
        )
        return 1

    project_state_path = pathlib.Path(sys.argv[1])
    milestone_state_path = pathlib.Path(sys.argv[2])
    scopes_csv_path = pathlib.Path(sys.argv[3])
    runs_dir = pathlib.Path(sys.argv[4])

    for path in (project_state_path, milestone_state_path, scopes_csv_path):
        if not path.exists():
            print(f"Missing required file: {path}", file=sys.stderr)
            return 1
    if not runs_dir.exists():
        print(f"Missing required directory: {runs_dir}", file=sys.stderr)
        return 1

    project_state = json.loads(project_state_path.read_text(encoding="utf-8"))
    milestone_state = json.loads(milestone_state_path.read_text(encoding="utf-8"))

    pending: List[str] = []
    completed: List[str] = []
    blocked: List[str] = []

    with scopes_csv_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            scope_id = row["scope_id"]
            state = read_summary_state(runs_dir / scope_id / "summary.state")
            status = state.get("STATUS", row.get("status", "pending"))
            if status == "completed":
                completed.append(scope_id)
            elif status == "blocked":
                blocked.append(scope_id)
            else:
                pending.append(scope_id)

    next_scope_ids = pending[:3]
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    project_state["next_scope_ids"] = next_scope_ids
    project_state["last_updated"] = now
    milestone_state["last_updated"] = now

    if blocked and not pending:
        project_state["phase_status"] = "blocked"
        project_state["transition_reason"] = "All remaining scopes are blocked after discovery sync"
        if not project_state.get("global_blockers"):
            project_state["global_blockers"] = [
                {
                    "blocker_id": "discovery-blocked-scopes",
                    "severity": "high",
                    "summary": "Remaining scopes are blocked and require review before planning",
                    "next_action": "Inspect blocked scope runs and decide whether to defer or unblock",
                }
            ]
        milestone_state["status"] = "blocked"
    else:
        project_state["phase_status"] = "in_progress" if next_scope_ids else "completed"
        milestone_state["status"] = "completed" if not pending and not blocked else "in_progress"

    if project_state["current_phase"] == "bootstrap_governance" and next_scope_ids:
        project_state["operating_mode"] = "discover"
        project_state["current_phase"] = "structured_discovery"
        project_state["next_skill"] = "java-migration"
        project_state["transition_reason"] = "Initial scopes detected and ready for structured discovery"

    milestone_state["selected_scope_ids"] = next_scope_ids
    milestone_state["completed_scope_ids"] = completed
    milestone_state["pending_scope_ids"] = pending
    milestone_state["blocked_scope_ids"] = blocked
    milestone_state["next_scope_ids"] = next_scope_ids

    append_phase_history(project_state, now, project_state["transition_reason"])

    project_state_path.write_text(
        json.dumps(project_state, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    milestone_state_path.write_text(
        json.dumps(milestone_state, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print(",".join(next_scope_ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

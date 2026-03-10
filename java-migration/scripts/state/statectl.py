#!/usr/bin/env python3
import argparse
import csv
import json
import pathlib
import sys

LIB_DIR = pathlib.Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from state_helpers import append_phase_history, load_json, now_utc, read_summary_state, write_json


PHASE_TO_SKILL = {
    "bootstrap_governance": "java-migration",
    "structured_discovery": "java-migration",
    "migration_planning": "java-migration",
    "automated_execution": "java-migration",
    "last_mile_fixes": "java-migration",
    "stabilization": "java-migration",
}

PHASE_TO_MODE = {
    "bootstrap_governance": "bootstrap",
    "structured_discovery": "discover",
    "migration_planning": "plan",
    "automated_execution": "execute",
    "last_mile_fixes": "stabilize",
    "stabilization": "resume",
}

EXCEPTION_SKILLS = set()


def cmd_route(args: argparse.Namespace) -> int:
    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)

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

    if phase_status == "completed" and next_skill != "java-migration":
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


def cmd_sync_next_scopes(args: argparse.Namespace) -> int:
    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)
    scopes_csv_path = pathlib.Path(args.scopes_csv)
    runs_dir = pathlib.Path(args.runs_dir)

    for path in (project_state_path, milestone_state_path, scopes_csv_path):
        if not path.exists():
            print(f"Missing required file: {path}", file=sys.stderr)
            return 1
    if not runs_dir.exists():
        print(f"Missing required directory: {runs_dir}", file=sys.stderr)
        return 1

    project_state = load_json(project_state_path)
    milestone_state = load_json(milestone_state_path)

    pending: list[str] = []
    completed: list[str] = []
    blocked: list[str] = []

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
    now = now_utc()

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

    write_json(project_state_path, project_state)
    write_json(milestone_state_path, milestone_state)

    print(",".join(next_scope_ids))
    return 0


def cmd_plan_wave(args: argparse.Namespace) -> int:
    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)
    scopes_csv_path = pathlib.Path(args.scopes_csv)
    runs_dir = pathlib.Path(args.runs_dir)

    project_state = load_json(project_state_path)
    milestone_state = load_json(milestone_state_path)

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

    write_json(project_state_path, project_state)
    write_json(milestone_state_path, milestone_state)

    print(",".join(next_scope_ids))
    return 0


def cmd_register_openrewrite(args: argparse.Namespace) -> int:
    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)
    summary_path = pathlib.Path(args.summary)

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
        project_state["next_skill"] = "java-migration"
        project_state["transition_reason"] = "Automation completed cleanly; inspect residual manual follow-up"
        milestone_state["status"] = "in_progress"
    elif summary["status"] == "rewrite_applied_validation_failed":
        project_state["operating_mode"] = "stabilize"
        project_state["current_phase"] = "last_mile_fixes"
        project_state["phase_status"] = "blocked"
        project_state["next_skill"] = "java-migration"
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
        project_state["next_skill"] = "java-migration"
        project_state["transition_reason"] = "Dry run completed; decide whether to apply recipes"
        milestone_state["status"] = "in_progress"
    else:
        project_state["operating_mode"] = "execute"
        project_state["current_phase"] = "automated_execution"
        project_state["phase_status"] = "blocked"
        project_state["next_skill"] = "java-migration"
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


def cmd_register_last_mile(args: argparse.Namespace) -> int:
    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)
    project_state = load_json(project_state_path)
    milestone_state = load_json(milestone_state_path)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="State controller for java-migration")
    subparsers = parser.add_subparsers(dest="command", required=True)

    route = subparsers.add_parser("route", help="Validate state routing coherence")
    route.add_argument("project_state")
    route.add_argument("milestone_state")
    route.set_defaults(func=cmd_route)

    sync = subparsers.add_parser("sync-next-scopes", help="Sync next scopes from discovery outputs")
    sync.add_argument("project_state")
    sync.add_argument("milestone_state")
    sync.add_argument("scopes_csv")
    sync.add_argument("runs_dir")
    sync.set_defaults(func=cmd_sync_next_scopes)

    plan = subparsers.add_parser("plan-wave", help="Promote the next execution wave")
    plan.add_argument("project_state")
    plan.add_argument("milestone_state")
    plan.add_argument("scopes_csv")
    plan.add_argument("runs_dir")
    plan.set_defaults(func=cmd_plan_wave)

    reg_or = subparsers.add_parser("register-openrewrite", help="Register an OpenRewrite run result")
    reg_or.add_argument("project_state")
    reg_or.add_argument("milestone_state")
    reg_or.add_argument("summary")
    reg_or.set_defaults(func=cmd_register_openrewrite)

    reg_lm = subparsers.add_parser("register-last-mile", help="Register last-mile status")
    reg_lm.add_argument("project_state")
    reg_lm.add_argument("milestone_state")
    reg_lm.add_argument("--scope", action="append", default=[])
    reg_lm.add_argument("--status", required=True, choices=("completed", "blocked", "in_progress"))
    reg_lm.add_argument("--validation-status", default="not_run", choices=("not_run", "passed", "failed"))
    reg_lm.add_argument("--validation-summary-file", default="")
    reg_lm.add_argument("--note", default="")
    reg_lm.set_defaults(func=cmd_register_last_mile)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

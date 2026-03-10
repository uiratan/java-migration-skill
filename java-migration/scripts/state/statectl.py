#!/usr/bin/env python3
import argparse
import csv
import json
import pathlib
import sys
from functools import lru_cache
from dataclasses import dataclass

LIB_DIR = pathlib.Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from state_helpers import append_phase_history, load_json, now_utc, read_summary_state, write_json


CONTRACTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "references" / "contracts"
STATE_MACHINE_CONTRACT_PATH = CONTRACTS_DIR / "state-machine.json"

EXCEPTION_SKILLS = set()


@dataclass(frozen=True)
class TransitionRule:
    event: str
    from_phases: tuple[str, ...]
    to_phase: str
    operating_mode: str
    phase_status: str
    milestone_type: str | None = None
    clear_exception: bool = False


@lru_cache(maxsize=1)
def load_state_machine_contract() -> dict:
    return load_json(STATE_MACHINE_CONTRACT_PATH)


@lru_cache(maxsize=1)
def get_phase_defaults() -> dict[str, dict]:
    contract = load_state_machine_contract()
    return contract["phase_defaults"]


@lru_cache(maxsize=1)
def get_transitions() -> dict[str, TransitionRule]:
    contract = load_state_machine_contract()
    transitions: dict[str, TransitionRule] = {}
    for event, raw_rule in contract["transitions"].items():
        transitions[event] = TransitionRule(
            event=raw_rule["event"],
            from_phases=tuple(raw_rule["from_phases"]),
            to_phase=raw_rule["to_phase"],
            operating_mode=raw_rule["operating_mode"],
            phase_status=raw_rule["phase_status"],
            milestone_type=raw_rule.get("milestone_type"),
            clear_exception=raw_rule.get("clear_exception", False),
        )
    return transitions


def clear_exception_state(project_state: dict) -> None:
    project_state["exception_state"] = None


def set_exception_state(
    project_state: dict,
    *,
    exception_type: str,
    status: str,
    summary: str,
    entry_criteria: str,
    exit_condition: str,
    artifact_scope_ids: list[str],
) -> None:
    project_state["exception_state"] = {
        "exception_type": exception_type,
        "status": status,
        "summary": summary,
        "entry_criteria": entry_criteria,
        "exit_condition": exit_condition,
        "artifact_scope_ids": artifact_scope_ids,
    }


def apply_transition(
    project_state: dict,
    milestone_state: dict,
    *,
    event: str,
    reason: str,
    now: str,
) -> None:
    transitions = get_transitions()
    if event not in transitions:
        raise ValueError(f"unknown transition event={event}")
    rule = transitions[event]
    current_phase = project_state["current_phase"]
    if current_phase not in rule.from_phases:
        allowed = ", ".join(rule.from_phases)
        raise ValueError(
            f"event {event} is not allowed from current_phase={current_phase}; expected one of: {allowed}"
        )

    project_state["operating_mode"] = rule.operating_mode
    project_state["current_phase"] = rule.to_phase
    project_state["phase_status"] = rule.phase_status
    project_state["next_skill"] = "java-migration"
    project_state["transition_reason"] = reason
    project_state["last_updated"] = now
    milestone_state["last_updated"] = now
    if rule.milestone_type is not None:
        milestone_state["milestone_type"] = rule.milestone_type
    milestone_state["status"] = rule.phase_status
    if rule.clear_exception:
        clear_exception_state(project_state)


def load_state_pair(project_state_path: pathlib.Path, milestone_state_path: pathlib.Path) -> tuple[dict, dict]:
    return load_json(project_state_path), load_json(milestone_state_path)


def persist_state_pair(
    project_state_path: pathlib.Path,
    milestone_state_path: pathlib.Path,
    project_state: dict,
    milestone_state: dict,
    *,
    now: str,
) -> None:
    append_phase_history(project_state, now)
    write_json(project_state_path, project_state)
    write_json(milestone_state_path, milestone_state)


def cmd_route(args: argparse.Namespace) -> int:
    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)

    for path in (project_state_path, milestone_state_path):
        if not path.exists():
            print(f"Missing required file: {path}", file=sys.stderr)
            return 1

    project_state, milestone_state = load_state_pair(project_state_path, milestone_state_path)

    current_phase = project_state["current_phase"]
    next_skill = project_state["next_skill"]
    phase_defaults = get_phase_defaults()
    phase_default = phase_defaults.get(current_phase)
    expected_skill = phase_default["next_skill"] if phase_default else None
    expected_mode = phase_default["operating_mode"] if phase_default else None
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

    if current_phase == "controlled_fallback" and operating_mode not in {"fallback", "resume", "assess"}:
        route_status = "inconsistent"
        messages.append("controlled_fallback phase requires operating_mode=fallback unless resuming")
    if current_phase == "controlled_fallback" and not project_state.get("exception_state"):
        route_status = "inconsistent"
        messages.append("controlled_fallback phase requires exception_state")

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

    if blocked and not pending:
        reason = "All remaining scopes are blocked after discovery sync"
        apply_transition(
            project_state,
            milestone_state,
            event="discovery_sync_blocked",
            reason=reason,
            now=now,
        )
        if not project_state.get("global_blockers"):
            project_state["global_blockers"] = [
                {
                    "blocker_id": "discovery-blocked-scopes",
                    "severity": "high",
                    "summary": "Remaining scopes are blocked and require review before planning",
                    "next_action": "Inspect blocked scope runs and decide whether to defer or unblock",
                }
            ]
    elif next_scope_ids:
        apply_transition(
            project_state,
            milestone_state,
            event="discovery_sync_progress",
            reason="Initial scopes detected and ready for structured discovery",
            now=now,
        )
    else:
        apply_transition(
            project_state,
            milestone_state,
            event="discovery_sync_completed",
            reason="Discovery sync completed with no remaining candidate scopes",
            now=now,
        )

    milestone_state["selected_scope_ids"] = next_scope_ids
    milestone_state["completed_scope_ids"] = completed
    milestone_state["pending_scope_ids"] = pending
    milestone_state["blocked_scope_ids"] = blocked
    milestone_state["next_scope_ids"] = next_scope_ids

    persist_state_pair(project_state_path, milestone_state_path, project_state, milestone_state, now=now)

    print(",".join(next_scope_ids))
    return 0


def cmd_plan_wave(args: argparse.Namespace) -> int:
    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)
    scopes_csv_path = pathlib.Path(args.scopes_csv)
    runs_dir = pathlib.Path(args.runs_dir)

    project_state, milestone_state = load_state_pair(project_state_path, milestone_state_path)

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
    project_state["next_scope_ids"] = next_scope_ids

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
        apply_transition(
            project_state,
            milestone_state,
            event="plan_wave_execution",
            reason="Discovery evidence is sufficient to promote the next execution wave",
            now=now,
        )
    elif manual_only:
        apply_transition(
            project_state,
            milestone_state,
            event="plan_wave_manual",
            reason="No safe automated wave available; hand-fix work is next",
            now=now,
        )
    else:
        apply_transition(
            project_state,
            milestone_state,
            event="plan_wave_blocked" if blocked else "plan_wave_deferred",
            reason="Planning could not promote a safe execution wave yet",
            now=now,
        )

    persist_state_pair(project_state_path, milestone_state_path, project_state, milestone_state, now=now)

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

    project_state, milestone_state = load_state_pair(project_state_path, milestone_state_path)
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
        apply_transition(
            project_state,
            milestone_state,
            event="openrewrite_passed",
            reason="Automation completed cleanly; inspect residual manual follow-up",
            now=now,
        )
    elif summary["status"] == "rewrite_applied_validation_failed":
        apply_transition(
            project_state,
            milestone_state,
            event="openrewrite_validation_failed",
            reason="Automation applied but validation failed; residual fixes required",
            now=now,
        )
        blocker = {
            "blocker_id": f"openrewrite-validation-failed:{summary['run_id']}",
            "severity": "high",
            "summary": "OpenRewrite changes compiled into a failing validation state",
            "next_action": "Inspect validation summary and route residual issues to last-mile fixes",
        }
        blockers = project_state.setdefault("global_blockers", [])
        if blocker not in blockers:
            blockers.append(blocker)
    elif summary["status"].startswith("dry_run_"):
        apply_transition(
            project_state,
            milestone_state,
            event="openrewrite_dry_run",
            reason="Dry run completed; decide whether to apply recipes",
            now=now,
        )
    else:
        apply_transition(
            project_state,
            milestone_state,
            event="openrewrite_fallback",
            reason="Automation failed and requires controlled fallback review",
            now=now,
        )
        blocker = {
            "blocker_id": f"openrewrite-failed:{summary['run_id']}",
            "severity": "high",
            "summary": "OpenRewrite execution failed before a stable post-run state",
            "next_action": "Inspect the run log and route the minimal artifact set through controlled fallback",
        }
        blockers = project_state.setdefault("global_blockers", [])
        if blocker not in blockers:
            blockers.append(blocker)
        set_exception_state(
            project_state,
            exception_type="transformer_exception",
            status="active",
            summary="OpenRewrite execution failed before a stable post-run validation state",
            entry_criteria="Normal automated execution failed for the selected wave",
            exit_condition="Either a smaller safe automation path is found or the minimal manual fallback is completed and verified",
            artifact_scope_ids=summary.get("scopes", []),
        )

    persist_state_pair(project_state_path, milestone_state_path, project_state, milestone_state, now=now)
    print(project_state["next_skill"])
    return 0


def cmd_register_last_mile(args: argparse.Namespace) -> int:
    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)
    project_state, milestone_state = load_state_pair(project_state_path, milestone_state_path)
    now = now_utc()

    selected_scope_ids = args.scope or milestone_state.get("selected_scope_ids", [])
    milestone_state["selected_scope_ids"] = selected_scope_ids
    milestone_state["next_scope_ids"] = selected_scope_ids
    project_state["next_scope_ids"] = selected_scope_ids

    notes = project_state.get("notes", "")
    line = f"[{now}] last-mile status={args.status} scopes={','.join(selected_scope_ids) or 'none'} validation={args.validation_status}"
    if args.note:
        line = f"{line} note={args.note}"
    project_state["notes"] = f"{notes}\n{line}".strip()

    if args.status == "completed" and args.validation_status == "passed":
        apply_transition(
            project_state,
            milestone_state,
            event="last_mile_completed",
            reason="Last-mile fixes validated successfully",
            now=now,
        )
    elif args.status == "blocked" or args.validation_status == "failed":
        apply_transition(
            project_state,
            milestone_state,
            event="last_mile_blocked",
            reason="Last-mile fixes remain blocked after validation",
            now=now,
        )
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
        apply_transition(
            project_state,
            milestone_state,
            event="last_mile_in_progress",
            reason="Last-mile fixes are still in progress",
            now=now,
        )

    if args.validation_summary_file:
        artifact = args.validation_summary_file
        artifacts = milestone_state.setdefault("artifacts_required", [])
        if artifact not in artifacts:
            artifacts.append(artifact)

    persist_state_pair(project_state_path, milestone_state_path, project_state, milestone_state, now=now)
    print(project_state["next_skill"])
    return 0


def cmd_register_fallback(args: argparse.Namespace) -> int:
    project_state_path = pathlib.Path(args.project_state)
    milestone_state_path = pathlib.Path(args.milestone_state)
    project_state, milestone_state = load_state_pair(project_state_path, milestone_state_path)
    now = now_utc()

    selected_scope_ids = args.scope or milestone_state.get("selected_scope_ids", [])
    milestone_state["selected_scope_ids"] = selected_scope_ids
    milestone_state["next_scope_ids"] = selected_scope_ids
    project_state["next_scope_ids"] = selected_scope_ids

    notes = project_state.get("notes", "")
    line = (
        f"[{now}] fallback phase_status={args.phase_status} exception_status={args.exception_status} "
        f"exception_type={args.exception_type} scopes={','.join(selected_scope_ids) or 'none'}"
    )
    if args.note:
        line = f"{line} note={args.note}"
    project_state["notes"] = f"{notes}\n{line}".strip()

    apply_transition(
        project_state,
        milestone_state,
        event=f"fallback_{args.phase_status}",
        reason=args.transition_reason,
        now=now,
    )

    if args.exception_status == "resolved":
        clear_exception_state(project_state)
    else:
        set_exception_state(
            project_state,
            exception_type=args.exception_type,
            status=args.exception_status,
            summary=args.summary,
            entry_criteria=args.entry_criteria,
            exit_condition=args.exit_condition,
            artifact_scope_ids=selected_scope_ids,
        )

    blockers = project_state.setdefault("global_blockers", [])
    blocker = {
        "blocker_id": f"controlled-fallback:{args.exception_type}:{','.join(selected_scope_ids) or 'none'}",
        "severity": "high",
        "summary": args.summary,
        "next_action": args.exit_condition,
    }
    if args.phase_status == "blocked":
        if blocker not in blockers:
            blockers.append(blocker)

    persist_state_pair(project_state_path, milestone_state_path, project_state, milestone_state, now=now)
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

    reg_fb = subparsers.add_parser("register-fallback", help="Register controlled fallback status")
    reg_fb.add_argument("project_state")
    reg_fb.add_argument("milestone_state")
    reg_fb.add_argument("--scope", action="append", default=[])
    reg_fb.add_argument(
        "--phase-status",
        required=True,
        choices=("in_progress", "blocked", "completed"),
    )
    reg_fb.add_argument(
        "--exception-status",
        required=True,
        choices=("active", "mitigated", "resolved"),
    )
    reg_fb.add_argument(
        "--exception-type",
        required=True,
        choices=("transformer_exception", "dependency_blocker", "unsupported_build", "human_decision_required"),
    )
    reg_fb.add_argument("--summary", required=True)
    reg_fb.add_argument("--entry-criteria", required=True)
    reg_fb.add_argument("--exit-condition", required=True)
    reg_fb.add_argument("--transition-reason", required=True)
    reg_fb.add_argument("--note", default="")
    reg_fb.set_defaults(func=cmd_register_fallback)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

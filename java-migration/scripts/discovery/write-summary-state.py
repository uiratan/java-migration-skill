#!/usr/bin/env python3
import argparse
import datetime
import pathlib


def now_utc() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def csvish(values: list[str]) -> str:
    return ",".join([value for value in values if value])


def main() -> int:
    parser = argparse.ArgumentParser(description="Write normalized discovery summary.state")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--scope-type", required=True)
    parser.add_argument("--scope-path", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--build-system", default="unknown")
    parser.add_argument("--risk-level", default="unknown")
    parser.add_argument("--compatibility-status", default="unknown")
    parser.add_argument("--migration-wave-candidate", default="unknown")
    parser.add_argument("--automation-eligibility", default="unknown")
    parser.add_argument("--requires-human-decision", choices=("true", "false"), default="false")
    parser.add_argument("--next-action", required=True)
    parser.add_argument("--validation-status", default="not_run")
    parser.add_argument("--detected-technology", action="append", default=[])
    parser.add_argument("--blocking-dependency", action="append", default=[])
    parser.add_argument("--blocker", action="append", default=[])
    parser.add_argument("--evidence-item", action="append", default=[])
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = pathlib.Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    summary_path = run_dir / "summary.state"

    lines = [
        ("RUN_ID", args.run_id),
        ("SCOPE_ID", args.scope_id),
        ("SCOPE_TYPE", args.scope_type),
        ("SCOPE_PATH", args.scope_path),
        ("STATUS", args.status),
        ("BUILD_SYSTEM", args.build_system),
        ("RISK_LEVEL", args.risk_level),
        ("COMPATIBILITY_STATUS", args.compatibility_status),
        ("MIGRATION_WAVE_CANDIDATE", args.migration_wave_candidate),
        ("AUTOMATION_ELIGIBILITY", args.automation_eligibility),
        ("REQUIRES_HUMAN_DECISION", args.requires_human_decision),
        ("NEXT_ACTION", args.next_action),
        ("DETECTED_TECHNOLOGIES", csvish(args.detected_technology)),
        ("BLOCKING_DEPENDENCIES", csvish(args.blocking_dependency)),
        ("BLOCKERS", " | ".join([item for item in args.blocker if item])),
        ("EVIDENCE_INVENTORY", csvish(args.evidence_item)),
        ("VALIDATION_STATUS", args.validation_status),
        ("NOTES", args.notes),
        ("LAST_UPDATED", now_utc()),
    ]
    summary_path.write_text(
        "".join(f"{key}\t{value}\n" for key, value in lines),
        encoding="utf-8",
    )
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

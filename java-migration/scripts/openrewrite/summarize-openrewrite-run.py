#!/usr/bin/env python3
import json
import pathlib
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: summarize-openrewrite-run.py <summary.json>", file=sys.stderr)
        return 1

    path = pathlib.Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))

    print(f"summary_schema_version={data.get('summary_schema_version', 'unknown')}")
    print(f"run_id={data['run_id']}")
    print(f"status={data['status']}")
    print(f"dry_run={str(data['dry_run']).lower()}")
    print(f"rewrite_exit_code={data['rewrite_exit_code']}")
    print(f"validation_status={data['validation_status']}")
    print(f"recommended_next_skill={data['recommended_next_skill']}")
    print(f"recommended_path={data.get('recommended_path', 'unknown')}")
    print(f"scopes={','.join(data['scopes']) or 'none'}")
    print(f"recipes={','.join(data['recipes']) or 'none'}")
    print(f"log_file={data['log_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

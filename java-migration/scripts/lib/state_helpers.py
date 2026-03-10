#!/usr/bin/env python3
import datetime
import json
import pathlib


def now_utc() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


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


def append_phase_history(project_state: dict, now: str, reason: str | None = None) -> None:
    entry = {
        "phase": project_state["current_phase"],
        "status": project_state["phase_status"],
        "reason": reason if reason is not None else project_state["transition_reason"],
        "changed_at": now,
    }
    history = project_state.setdefault("phase_history", [])
    if not history or history[-1] != entry:
        history.append(entry)

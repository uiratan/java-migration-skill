#!/usr/bin/env python3
import pathlib
import runpy


TARGET = pathlib.Path(__file__).resolve().parent.parent / "migration-orchestrator" / "scripts" / "state" / "resolve-state-route.py"
runpy.run_path(str(TARGET), run_name="__main__")

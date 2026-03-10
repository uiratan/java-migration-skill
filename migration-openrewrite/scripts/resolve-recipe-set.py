#!/usr/bin/env python3
import pathlib
import runpy


TARGET = pathlib.Path(__file__).resolve().parents[2] / "migration-orchestrator" / "scripts" / "openrewrite" / "resolve-recipe-set.py"
runpy.run_path(str(TARGET), run_name="__main__")

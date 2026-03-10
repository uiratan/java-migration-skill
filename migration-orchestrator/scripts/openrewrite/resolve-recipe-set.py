#!/usr/bin/env python3
import json
import pathlib
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: resolve-recipe-set.py <presets-dir> <preset-id>", file=sys.stderr)
        return 1

    presets_dir = pathlib.Path(sys.argv[1])
    preset_id = sys.argv[2]
    preset_path = presets_dir / f"{preset_id}.json"

    if not preset_path.exists():
        print(f"Preset not found: {preset_path}", file=sys.stderr)
        return 1

    payload = json.loads(preset_path.read_text(encoding="utf-8"))
    recipes = payload.get("recipes", [])
    if not recipes:
        print(f"Preset has no recipes: {preset_id}", file=sys.stderr)
        return 1

    print(",".join(recipes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

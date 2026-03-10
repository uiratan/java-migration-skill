#!/usr/bin/env python3
import pathlib
import sys

STATE_DIR = pathlib.Path(__file__).resolve().parent
if str(STATE_DIR) not in sys.path:
    sys.path.insert(0, str(STATE_DIR))

from statectl import main as statectl_main


def main() -> int:
    return statectl_main(["route", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())

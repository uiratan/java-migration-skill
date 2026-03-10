#!/usr/bin/env python3
import csv
import pathlib
import sys


JAVAX_HINTS = (
    "javax.",
    "javax:",
    "javaee-api",
    "jakartaee-api",
)

JAKARTA_HINTS = (
    "jakarta.",
    "jakartaee",
)

KNOWN_TRANSFORMER_CANDIDATES = (
    "javax",
    "javaee-api",
)


def classify(group_id: str, artifact_id: str, version: str) -> str:
    joined = " ".join((group_id, artifact_id, version)).lower()

    if any(token in joined for token in JAKARTA_HINTS):
        return "jakarta_aligned"

    if any(token in joined for token in JAVAX_HINTS):
        return "legacy_javax"

    if any(token in joined for token in KNOWN_TRANSFORMER_CANDIDATES):
        return "transformer_candidate"

    if not version.strip():
        return "managed_or_unknown"

    return "review_required"


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: classify-dependencies.py <dependencies.csv> <output.csv>",
            file=sys.stderr,
        )
        return 1

    input_path = pathlib.Path(sys.argv[1])
    output_path = pathlib.Path(sys.argv[2])

    with input_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "source_pom",
                "entry_type",
                "group_id",
                "artifact_id",
                "version",
                "classification",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.get("source_pom", ""),
                    row.get("entry_type", ""),
                    row.get("group_id", ""),
                    row.get("artifact_id", ""),
                    row.get("version", ""),
                    classify(
                        row.get("group_id", ""),
                        row.get("artifact_id", ""),
                        row.get("version", ""),
                    ),
                ]
            )

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

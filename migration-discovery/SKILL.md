---
name: migration-discovery
description: Run migration discovery with minimal context and artifact-first outputs. Use when generating a central baseline, scanning scopes, updating summary.state, recording evidence, identifying blockers, or ranking scopes for the first migration wave.
---

# Migration Discovery

Use this skill for structured discovery after bootstrap.

This skill must keep its outputs inside the discovery run contract only:
`summary.state` plus `evidence/`.

## Required run contract

Each scope run must live under:

- `docs/java-migration/discovery-protocol/runs/<scope-id>/summary.state`
- `docs/java-migration/discovery-protocol/runs/<scope-id>/evidence/`

`summary.state` is the canonical machine-readable summary for the scope. Write it
through:

- `migration-discovery/scripts/write-summary-state.py`

The minimum fields that must be present in every scope summary are:

- status
- build system
- compatibility status
- automation eligibility
- migration wave candidate
- human decision flag
- next action
- evidence inventory

## Workflow

1. Read the active milestone and ADRs.
2. Read `docs/java-migration/discovery-protocol/manifests/scopes.csv`.
3. Select one scope or a small independent batch of scopes.
4. Generate or refresh evidence for each scope.
5. If `dependencies.csv` exists, classify it with
   `scripts/classify-dependencies.py`.
6. Normalize the scope result with `scripts/write-summary-state.py`.
7. Run `docs/java-agentic-migration-kit/scripts/sync-next-scopes.py` to refresh
   official state after the scope updates.

## Evidence expectations

Discovery should try to surface, when applicable:

- build tool and wrapper presence
- module boundaries
- explicit `javax.*` usage
- explicit `jakarta.*` usage
- app server or runtime coupling
- dependency blockers
- likely automation path:
  `openrewrite_ready`, `manual_only`, or `transformer_exception`

## Rules

- Runs keep only `summary.state` and `evidence/`.
- Do not create per-scope Markdown summaries.
- If judgement is required, record it in `NOTES`.
- Reopen global strategy only on explicit exception triggers.
- If a deterministic post-processing step is repeated, move it to a script.
- Do not mark a scope as `openrewrite_ready` unless the evidence supports it.
- Do not promote a blocked scope by hand; let planning decide from persisted
  evidence.

## Output

- updated scope runs
- updated project state
- updated milestone state

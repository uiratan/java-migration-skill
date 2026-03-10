---
name: migration-wave-planner
description: Plan migration waves and executable slices from the discovery baseline. Use when sequencing scopes, grouping modules by risk and dependency, defining the first migration wave, or converting discovery findings into milestone execution slices.
---

# Migration Wave Planner

Use this skill after the baseline and scope runs are mature enough to support
sequencing.

This skill plans from persisted state; it should not rebuild discovery context
from scratch.

## Required inputs

- `docs/java-migration/state/project.state.json`
- `docs/java-migration/state/active-milestone.json`
- `docs/java-migration/discovery-protocol/manifests/scopes.csv`
- scope run `summary.state` files

## Workflow

1. Read the active milestone and project state.
2. Read only the relevant scope runs and dependency evidence.
3. Identify dependency-first constraints.
4. Group scopes into small executable waves.
5. Mark what can go through `OpenRewrite`, what needs manual work, and what is
   blocked.
6. Persist the resulting wave with
   `migration-wave-planner/scripts/plan-next-wave.py`.

## Wave policy

- prefer waves of up to 3 scopes
- prefer rollback-friendly scope groups
- promote only `openrewrite_ready` scopes into automated execution
- defer `manual_only` scopes instead of forcing them into automation
- preserve blocked scopes explicitly in milestone state

## Rules

- Prefer small waves with clear rollback.
- Do not create oversized execution batches.
- Keep the milestone and project state aligned with the proposed waves.
- Persist wave decisions in official state instead of side documents.
- Do not promote execution when `build_system != maven`.
- If no safe automated wave exists, route to manual stabilization or stay in
  planning with blockers persisted.

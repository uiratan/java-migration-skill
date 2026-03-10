# Discovery Playbook

Use this playbook for structured discovery after bootstrap.

Required run contract:

- `docs/java-migration/discovery-protocol/runs/<scope-id>/summary.state`
- `docs/java-migration/discovery-protocol/runs/<scope-id>/evidence/`

Workflow:

1. Read the active milestone, ADRs, and `scopes.csv`.
2. Select one scope or a small independent batch.
3. Generate evidence for each scope.
4. If `dependencies.csv` exists, classify it with `scripts/discovery/classify-dependencies.py`.
5. Normalize the run with `scripts/discovery/write-summary-state.py`.
6. Refresh official state with `scripts/state/sync-next-scopes.py`.

Rules:

- Keep scope outputs limited to `summary.state` and `evidence/`.
- Do not create per-scope Markdown summaries.
- Record judgment in `NOTES` when needed.
- Independent scopes may be investigated by multiple agents in parallel, but a
  single coordinating agent must normalize outputs and run
  `scripts/state/sync-next-scopes.py`.

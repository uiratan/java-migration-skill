# Discovery Playbook

Compatibility note: discovery guidance now lives primarily in
`java-migration/SKILL.md`.

Use this file only as a short pointer when an older prompt or workflow refers to
"the discovery playbook".

Primary source of truth:

- `java-migration/SKILL.md`

Required discovery run contract:

- `docs/java-migration/discovery-protocol/runs/<scope-id>/summary.state`
- `docs/java-migration/discovery-protocol/runs/<scope-id>/evidence/`

Core scripts:

- `scripts/discovery/classify-dependencies.py`
- `scripts/discovery/write-summary-state.py`
- `scripts/state/sync-next-scopes.py`

Keep repository-specific findings in `docs/java-migration/PLAN.md`, not here.

# Bootstrap Playbook

Compatibility note: bootstrap guidance now lives primarily in
`java-migration/SKILL.md`.

Use this file only as a short pointer when an older prompt or workflow refers to
"the bootstrap playbook".

Primary source of truth:

- `java-migration/SKILL.md`

Bootstrap entrypoint:

- `bash java-migration/scripts/bootstrap/migration-kit.sh start <repo-root>`

Minimum expected outcome:

- `docs/java-migration/PLAN.md`
- `docs/java-migration/state/project.state.json`
- `docs/java-migration/state/active-milestone.json`
- `docs/java-migration/state/session-handoff.md`

Do not duplicate bootstrap rules here. Update `SKILL.md` when the skill-level
workflow changes.

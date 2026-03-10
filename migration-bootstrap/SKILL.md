---
name: migration-bootstrap
description: Bootstrap migration governance in a codebase that has no migration kit yet. Use when entering a new repository that needs migration, seeding ADRs, creating milestone 0, initializing persistent state, detecting build structure, and preparing the scope manifest for later discovery.
---

# Migration Bootstrap

Use this skill when the repository does not yet have a migration operating kit.

This skill is a thin wrapper over
`docs/java-agentic-migration-kit/bootstrap/scripts/migration-kit.sh`.

## Workflow

1. Inspect the repository root, build files, module layout, CI files, and README.
2. Run `docs/java-agentic-migration-kit/bootstrap/scripts/migration-kit.sh start <repo-root>`
   when the migration output is missing.
3. Ensure the first run leaves, at minimum:
   - `docs/java-migration/README.md`
   - `docs/java-migration/adr/adr-001-target-stack.md`
   - `docs/java-migration/adr/adr-002-migration-strategy.md`
   - `docs/java-migration/milestones/milestone-0-discovery.md`
   - `docs/java-migration/state/project.state.json`
   - `docs/java-migration/state/active-milestone.json`
   - `docs/java-migration/state/session-handoff.md`
   - `docs/java-migration/discovery-protocol/manifests/scopes.csv`
   - `docs/java-migration/discovery-protocol/runs/`
   - `docs/java-migration/openrewrite-runs/`
4. Populate `docs/java-migration/state/project.state.json`.
5. Populate `docs/java-migration/state/active-milestone.json`.
6. Create the first `scopes.csv` entries.
7. Hand off to `migration-discovery`.

## Rules

- Do not start bulk migration during bootstrap.
- Focus on governance, inventory boundaries, and resumability.
- Keep the state files current enough for a future session to resume cold.
- Do not recreate the first-run contract manually if the script already owns it.

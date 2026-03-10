---
name: migration-openrewrite
description: Execute recipe-driven migration automation with OpenRewrite. Use when applying repeatable changes to source code, build files, or XML descriptors; preparing automated javax-to-jakarta transformations; or measuring residual work before last-mile manual fixes.
---

# Migration OpenRewrite

Use this skill when the next step is deterministic transformation.

This skill is an orchestration layer over
`migration-openrewrite/scripts/` and `presets/*.json`.

## Workflow

1. Confirm the active milestone and target stack.
2. Read the selected scopes and dependency findings.
3. Choose or prepare the smallest safe recipe set.
4. Run `migration-openrewrite/scripts/run-openrewrite.sh`.
5. Validate the affected scopes after a real run.
6. Register the run with
   `migration-openrewrite/scripts/register-openrewrite-result.py`.
7. Measure the residual breakage.
8. Hand off unresolved issues to `migration-last-mile-fixer`.

## Quick Start

For Maven repositories, use:

```bash
bash docs/java-agentic-migration-kit/migration-openrewrite/scripts/run-openrewrite.sh --root . --scope <module> --recipe-set jakarta-ee --dry-run
```

```bash
bash docs/java-agentic-migration-kit/migration-openrewrite/scripts/run-openrewrite.sh --root . --scope <module> --recipe-set jakarta-ee --validate-goal test-compile
```

Use `references/maven-openrewrite-notes.md` when deciding batch size, dry-run
policy, or how to interpret a failed run.
Use `presets/*.json` as the source of truth for reusable recipe sets.

## Rules

- Prefer small, reviewable recipe batches.
- Do not combine recipe execution with unrelated architectural decisions.
- Record what recipe set ran, on which scopes, and what remains broken.
- Keep `Eclipse Transformer` out of the happy path.
- If a recipe decision can be standardized, move it to `presets/*.json`.

# OpenRewrite Playbook

Use this playbook when the next step is deterministic transformation.

Workflow:

1. Confirm the active milestone and target stack.
2. Read selected scopes and dependency findings.
3. Choose the smallest safe recipe set.
4. Run `scripts/openrewrite/run-openrewrite.sh`.
5. Validate the affected scopes after a real run.
6. Register the result with `scripts/openrewrite/register-openrewrite-result.py`.
7. Hand off unresolved issues to last-mile fixes.

Resources:

- `references/openrewrite/maven-openrewrite-notes.md`
- `references/openrewrite/presets/*.json`

Rules:

- Prefer small, reviewable recipe batches.
- Keep Eclipse Transformer out of the happy path.
- Agents may parallelize pre-run inspection or post-run validation by scope when
  scopes are independent.
- Do not run conflicting automated edits in parallel against the same module or
  the same execution wave state.

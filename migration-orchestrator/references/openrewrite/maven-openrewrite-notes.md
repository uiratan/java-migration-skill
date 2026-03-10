Use small recipe batches and prefer a dry run before applying changes broadly.

Interpretation hints:

- `dry_run_clean` means the plugin completed without surfacing pending rewrite output for the selected scopes.
- `dry_run_changes_or_failure` means the scope or recipe batch still needs review before apply mode.
- `rewrite_applied_validation_failed` should route to residual fixes, not a larger rewrite batch.

Maven-first policy:

- Prefer `mvnw` when available.
- Keep validation goals lightweight, usually `test-compile` or `compile`.
- Reduce scope size before reducing observability.

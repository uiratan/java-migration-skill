---
name: migration-last-mile-fixer
description: Resolve residual migration breakage after automation. Use when OpenRewrite or other automated steps already ran and the repository still has compile errors, API incompatibilities, XML adjustments, test failures, or hand-fixed integration issues that need small, reviewable corrections.
---

# Migration Last-Mile Fixer

Use this skill only after deterministic automation has already been applied.

This skill exists to consume residual work, not to replace missing automation.

## Workflow

1. Read the current phase, selected scopes, and residual blockers.
2. Inspect only the failing modules and files.
3. Fix the smallest coherent set of residual issues.
4. Re-run the relevant validation.
5. Register the result with
   `migration-last-mile-fixer/scripts/register-last-mile-result.py`.

## Required registration data

When this skill finishes a slice, it must persist:

- selected scopes
- last-mile status
- validation status
- optional validation artifact path
- transition reason in official state

## Rules

- Treat this as residual correction, not a substitute for missing automation.
- Prefer small fixes and fast validation loops.
- If the same issue appears broadly, stop and push it back toward automation.
- Update only the affected runs and global state required for the next session.
- Do not mark stabilization as completed without successful validation.

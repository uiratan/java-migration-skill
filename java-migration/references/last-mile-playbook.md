# Last-Mile Playbook

Use this playbook only after deterministic automation has already been applied.

Workflow:

1. Read the current phase, selected scopes, and residual blockers.
2. Inspect only the failing modules and files.
3. Fix the smallest coherent set of residual issues.
4. Re-run the relevant validation.
5. Register the result with `scripts/last-mile/register-last-mile-result.py`.

Rules:

- Treat this as residual correction, not a substitute for missing automation.
- If the same issue appears broadly, stop and push it back toward automation.
- If context budget is running low, stop after the smallest validated fix set,
  register the result, and hand off.

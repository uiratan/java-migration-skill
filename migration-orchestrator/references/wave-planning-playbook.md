# Wave Planning Playbook

Use this playbook after discovery artifacts are mature enough to support sequencing.

Workflow:

1. Read project state, active milestone, `scopes.csv`, and only the relevant scope runs.
2. Identify dependency-first constraints.
3. Group scopes into small executable waves.
4. Promote only `openrewrite_ready` scopes into automated execution.
5. Persist the decision with `scripts/wave-planner/plan-next-wave.py`.

Policy:

- Prefer waves of up to 3 scopes.
- Prefer rollback-friendly groups.
- Preserve blocked scopes explicitly in milestone state.

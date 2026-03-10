---
name: migration-orchestrator
description: Main entry skill for agentic Java migration. Use when asking how to update a codebase, what migration strategy fits the current project, how to migrate a Java EE codebase to Jakarta EE, or when you want the kit to inspect the repository, choose the next migration phase, and drive the workflow through the specialized skills.
---

# Migration Orchestrator

Use this skill as the main entrypoint for the migration kit.

This installable skill is self-contained. Prefer its bundled `scripts/` and
`references/` over sibling folders when packaging outside `docs/`.

This is the skill a human should call first for open-ended requests such as:

- "como atualizar essa codebase?"
- "qual a estrategia de atualizacao desse projeto?"
- "como migrar este projeto para jakarta?"
- "quero atualizar esse projeto javaee para jakartaee"

This skill translates those requests into an explicit operating mode, validates
the official state, and routes the work through the specialized skills.

It owns:

- first contact with the repository;
- operating mode selection;
- phase selection;
- next-skill routing;
- scope selection;
- session handoff;
- state persistence.

It does not perform bulk discovery or bulk rewrites by itself unless the task is
too small to justify delegation.

## Product boundary

This kit is `Maven-first` in `v1`.

Treat the happy path as:

- Java repository
- Maven or Maven Wrapper present
- migration centered on Java EE to Jakarta EE
- execution in small reviewable waves

If the repository is outside this envelope, the orchestrator must diagnose,
persist the constraint, and stop before automated execution.

## Operating modes

Interpret the user request into one of these modes:

- `assess`
  strategy or diagnosis without changing repository code
- `bootstrap`
  initialize the official output contract
- `discover`
  produce baseline and evidence for scopes
- `plan`
  sequence scopes into executable waves
- `execute`
  run deterministic automation
- `stabilize`
  fix residual breakage after automation
- `resume`
  resume from official persisted state

The user request can suggest a mode, but persisted state and preconditions are
authoritative.

## Workflow

1. Run `bash scripts/bootstrap/migration-kit.sh status <repo-root>`.
2. If `docs/java-migration` is missing or only reserved, inspect the repository
   enough to classify build system, module shape, and migration intent.
3. Read `docs/java-migration/state/project.state.json` when it exists.
4. Read `docs/java-migration/state/active-milestone.json` when it exists.
5. Read `docs/java-migration/state/session-handoff.md` when it exists.
6. Validate that `current_phase`, `operating_mode`, `next_skill`, `next_scope_ids`,
   and `build_system` are coherent with
   `scripts/state/resolve-state-route.py`.
7. Read only the ADRs and scope runs needed for the next scopes.
8. Load the phase-specific playbook only when needed:
   - bootstrap: `references/bootstrap-playbook.md`
   - discovery: `references/discovery-playbook.md`
   - wave planning: `references/wave-planning-playbook.md`
   - OpenRewrite: `references/openrewrite-playbook.md`
   - transformer fallback: `references/transformer-fallback-playbook.md`
   - last-mile fixes: `references/last-mile-playbook.md`
9. Decide whether the request is consultative or operational.
10. Route to the next specialized skill only if the phase preconditions hold.
11. Run `scripts/state/sync-next-scopes.py` after discovery updates when scope
    ordering changed.
12. Persist updated state and handoff before ending the session.

## Mandatory preconditions

### Before `migration-bootstrap`

- repository root is known
- output is missing or reserved

### Before `migration-discovery`

- official output exists
- active milestone exists
- build system has been classified
- scopes manifest exists or can be materialized from bootstrap

### Before `migration-wave-planner`

- discovery runs exist for the scopes under discussion
- blockers and dependency-first constraints are visible in persisted artifacts

### Before `migration-openrewrite`

- `build_system == maven`
- selected scopes are explicitly listed in state
- selected scopes are ready for automation
- unresolved blocking decisions do not prohibit execution

### Before `migration-last-mile-fixer`

- deterministic automation has already run
- residual validation failure or residual manual work is persisted

### Before `migration-transformer-fallback`

- normal upgrade path is explicitly ruled out
- the blocking artifact is identified
- the future removal condition is known

## Routing rules

- If `docs/java-migration/` does not exist, use `migration-bootstrap`.
- If `current_phase` is `bootstrap_governance`, route to `migration-bootstrap`.
- If the current phase is `structured_discovery`, use `migration-discovery`.
- If the current phase is `migration_planning`, use `migration-wave-planner`.
- If the current phase is `automated_execution`, use `migration-openrewrite`.
- If the current phase is `last_mile_fixes`, use `migration-last-mile-fixer`.
- If a third-party dependency has no viable Jakarta upgrade path, use
  `migration-transformer-fallback`.
- Do not route to `migration-openrewrite` when `build_system` is not `maven`.

## Decision policy

- Prefer answering in product language first, then describe the routed phase.
- Keep consultative answers in `assess` mode unless the user explicitly asked to
  start or resume the operational flow.
- Never move to a new phase without persisting `transition_reason`.
- Never mark a phase as `blocked` without a persisted blocker.
- Never pick a next skill that contradicts the phase matrix unless it is an
  explicit fallback exception.
- Never create side documents outside `docs/java-migration`.

## Parallelism

Use subagents only when:

- scopes are independent;
- outputs are structured and small;
- no shared architectural decision is pending.

Do not run a team of agents against the same unresolved design question.

## Bundled resources

- `scripts/bootstrap/` contains bootstrap and resume entrypoints.
- `scripts/state/` contains route validation and scope sync helpers.
- `scripts/discovery/` contains deterministic discovery normalizers.
- `scripts/openrewrite/` contains automated rewrite execution helpers.
- `scripts/wave-planner/` contains wave promotion logic.
- `scripts/last-mile/` contains residual-fix registration helpers.
- `references/` contains phase playbooks, contracts, and OpenRewrite presets.

## Required outputs

Before finishing, update:

- `docs/java-migration/state/project.state.json`
- `docs/java-migration/state/active-milestone.json`
- `docs/java-migration/state/session-handoff.md`

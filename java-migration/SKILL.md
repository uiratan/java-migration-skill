---
name: java-migration
description: Self-contained Codex skill for agentic Java migration. Use when assessing or executing a Maven-first Java migration, especially Java EE to Jakarta EE, and when you want one installable skill to bootstrap output, run discovery, plan waves, execute OpenRewrite, handle transformer exceptions, and stabilize the repository from persisted state.
---

# Java Migration

Use this as the single entry skill for the migration kit.

This skill is self-contained in this directory. Prefer its bundled `scripts/`,
`references/`, and contracts. Do not depend on sibling skill trees or
repository-level wrappers.

## Product boundary

This kit is `Maven-first` in `v1`.

Treat the supported path as:

- Java repository
- Maven or Maven Wrapper present
- migration centered on Java EE to Jakarta EE
- execution in small, reviewable waves

If the repository is outside this envelope, diagnose the constraint, persist it
in official state, and stop before automated execution.

## Operating modes

Interpret the request into one of these modes:

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

Persisted state and phase preconditions are authoritative.

## Workflow

1. Run `bash scripts/bootstrap/migration-kit.sh status <repo-root>`.
2. If `docs/java-migration` is missing or only reserved, inspect the repository
   enough to classify build system, module shape, and migration intent.
3. Read `docs/java-migration/state/project.state.json` when it exists.
4. Read `docs/java-migration/state/active-milestone.json` when it exists.
5. Read `docs/java-migration/state/session-handoff.md` when it exists.
6. Validate that `current_phase`, `operating_mode`, `next_skill`,
   `next_scope_ids`, and `build_system` are coherent with
   `scripts/state/resolve-state-route.py`.
7. Read only the ADRs and scope runs needed for the next scopes.
8. Load only the playbook for the active phase:
   - bootstrap: `references/bootstrap-playbook.md`
   - discovery: `references/discovery-playbook.md`
   - planning: `references/wave-planning-playbook.md`
   - execution: `references/openrewrite-playbook.md`
   - transformer exception: `references/transformer-fallback-playbook.md`
   - stabilization: `references/last-mile-playbook.md`
9. Use the phase-specific scripts instead of making ad hoc state mutations.
10. Persist the updated state and handoff before ending the session.

## Phase preconditions

### Before bootstrap

- repository root is known
- output is missing or reserved

### Before discovery

- official output exists
- active milestone exists
- build system has been classified
- scopes manifest exists or can be materialized from bootstrap

### Before planning

- discovery runs exist for the scopes under discussion
- blockers and dependency-first constraints are visible in persisted artifacts

### Before execution

- `build_system == maven`
- selected scopes are explicitly listed in state
- selected scopes are ready for automation
- unresolved blocking decisions do not prohibit execution

### Before stabilization

- deterministic automation has already run
- residual validation failure or manual follow-up is persisted

### Before transformer exception handling

- normal upgrade path is explicitly ruled out
- the blocking artifact is identified
- the future removal condition is known

## Decision policy

- Prefer answering in product language first, then describe the active phase.
- Keep consultative answers in `assess` mode unless the user explicitly asked to
  start or resume the operational flow.
- `next_skill` must remain `java-migration`; phase changes are expressed through
  `current_phase`, `operating_mode`, and `transition_reason`.
- Never move to a new phase without persisting `transition_reason`.
- Never mark a phase as `blocked` without a persisted blocker.
- Never create side documents outside `docs/java-migration`.

## Context budget policy

This skill must operate as if context were a scarce runtime budget.

- Treat `50%` of the model context window as a hard operating ceiling.
- Treat `40%` as the mandatory stop-and-handoff threshold.
- Before crossing the `40%` threshold, stop active investigation or execution,
  persist the latest coherent state, and recommend opening a fresh session.
- Do not continue loading more files, playbooks, or evidence once the skill
  judges that it is near the `40%` threshold.
- The handoff must include the minimum restart context and a ready-to-send
  prompt for the next session.
- If exact runtime telemetry is unavailable, apply this conservatively based on
  observed prompt growth and stop early rather than risk crossing `50%`.

## Multi-agent policy

- This skill may use multiple Codex sub-agents even though it is a single
  installable skill.
- Parallelize only across independent scopes, evidence gathering, or validation
  tasks.
- Keep one coordinating agent responsible for the official state files and final
  handoff.
- Do not let multiple agents edit the same state file or the same unresolved
  design decision in parallel.
- Prefer parallelism in discovery and validation-heavy work.
- Prefer serial execution for bootstrap finalization, wave promotion decisions,
  and any state transition that changes `current_phase`, `phase_status`, or
  `transition_reason`.
- For automated execution waves, parallelize analysis or validation around the
  wave, not conflicting edits inside the same module set.

## Bundled resources

- `scripts/bootstrap/` contains bootstrap and resume entrypoints.
- `scripts/state/` contains route validation and scope sync helpers.
- `scripts/discovery/` contains deterministic discovery normalizers.
- `scripts/openrewrite/` contains automated rewrite execution helpers.
- `scripts/wave-planner/` contains wave promotion logic.
- `scripts/last-mile/` contains residual-fix registration helpers.
- `references/` contains phase playbooks, contracts, notes, and OpenRewrite
  presets under `references/openrewrite/presets/`.

## Required outputs

Before finishing, update:

- `docs/java-migration/state/project.state.json`
- `docs/java-migration/state/active-milestone.json`
- `docs/java-migration/state/session-handoff.md`

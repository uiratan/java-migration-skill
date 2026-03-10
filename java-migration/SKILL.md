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

## Planning model

This skill uses two planning layers:

1. skill-level operating contract
   This `SKILL.md`. It defines the reusable operating model of the installed
   skill.
2. repository-level migration plan
   `docs/java-migration/PLAN.md` in the target repository. It records the live
   plan, progress, decisions, risks, and next actions for that repository.

If the human-readable plan and machine-readable state disagree, update both
before continuing. Scripts remain authoritative for deterministic transitions.

## Workflow

1. Run `bash scripts/bootstrap/migration-kit.sh status <repo-root>`.
2. If `docs/java-migration` is missing or only reserved, inspect the repository
   enough to classify build system, module shape, and migration intent.
3. Read `docs/java-migration/PLAN.md` when it exists.
4. Read `docs/java-migration/state/project.state.json` when it exists.
5. Read `docs/java-migration/state/active-milestone.json` when it exists.
6. Read `docs/java-migration/state/session-handoff.md` when it exists.
7. Validate that `current_phase`, `operating_mode`, `next_skill`,
   `next_scope_ids`, and `build_system` are coherent with
   `scripts/state/resolve-state-route.py`.
8. Read only the ADRs and scope runs needed for the next scopes.
9. Use this `SKILL.md` as the canonical phase guidance for the installed skill.
10. Use the phase-specific scripts instead of making ad hoc state mutations.
11. Persist the updated repository `PLAN.md`, state, and handoff before ending
    the session.

## Standard workflow

### 1. Assess

Use when the user wants strategy, feasibility, diagnosis, or simplification
without starting repository changes.

Deliverables:

- recommendation grounded in the current repository
- explicit statement of whether the repository fits the supported envelope
- no mutation unless the user asks to start or resume the operational flow

### 2. Bootstrap

Use when `docs/java-migration/` is missing or only partially initialized.

Required actions:

- inspect repository root just enough to classify build system and module shape
- run `bash java-migration/scripts/bootstrap/migration-kit.sh start <repo-root>`
- confirm the output contract was created
- seed `docs/java-migration/PLAN.md` and state files

Exit criteria:

- repository-level `PLAN.md` exists
- state files exist
- initial ADRs and discovery manifest exist

### 3. Discover

Use when baseline evidence is missing or incomplete.

Required actions:

- read only the active state, target `PLAN.md`, and relevant manifests
- gather evidence for one scope or a small independent batch
- normalize discovery output with bundled scripts
- refresh next-scope state
- record discoveries and decisions in the target `PLAN.md`

Exit criteria:

- prioritized scopes are visible
- blockers and dependency-first constraints are explicit
- candidate scopes can be promoted into waves

### 4. Plan waves

Use when discovery is mature enough to promote executable work.

Required actions:

- group scopes into small rollback-friendly waves
- promote only `openrewrite_ready` scopes into deterministic automation
- persist the promoted wave through the planner script
- update the target `PLAN.md` with rationale, risks, and success criteria

Exit criteria:

- a concrete next wave is selected
- selected scopes are visible in machine-readable state
- validation expectations are explicit

### 5. Execute deterministic automation

Use for OpenRewrite-centered transformations.

Required actions:

- confirm the selected scopes and target stack
- choose the smallest safe recipe set
- run bundled automation helpers
- validate the affected scopes
- register results in state
- summarize outcomes and residual issues in the target `PLAN.md`

Exit criteria:

- the wave result is persisted
- the next action is either another automation wave or stabilization

### 6. Stabilize

Use only after deterministic automation has run.

Required actions:

- inspect only the failing modules and residual issues
- make the smallest coherent fix set
- rerun the relevant validation
- register the result in state
- capture remaining risks or blockers in the target `PLAN.md`

Exit criteria:

- the residual issue is resolved and verified
- or the blocker is explicitly recorded with a next action

### 7. Controlled fallback

Use only when the normal upgrade path is explicitly blocked.

Required actions:

- record why the normal path is not viable
- apply the fallback only to the minimal necessary artifact set
- persist an exit condition
- reflect the exception in the target `PLAN.md` and machine-readable state

Fallbacks are exceptions, not a parallel happy path.

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
- Keep repository-specific progress in `docs/java-migration/PLAN.md`, not in
  the installed skill directory.

## Target repository PLAN.md contract

Each target repository must keep `docs/java-migration/PLAN.md` current.

It should stay compact and operational. The recommended structure is:

1. Objective
   Repository-specific migration goal and supported target stack.
2. Current status
   Current phase, operating mode, active milestone, active wave, and summary.
3. Decisions
   High-signal decisions and tradeoffs, with dates.
4. Scope and waves
   Planned waves, selected scopes, blocked scopes, and why.
5. Validation
   Required checks, latest results, and known failures.
6. Risks and blockers
   Active blockers, fallback conditions, and removal criteria.
7. Next actions
   Exact next steps for the next session or agent.
8. Session resume
   The minimal read order and commands needed to continue safely.

Do not turn the repository plan into a long narrative. It must stay easy to
resume from and cheap to maintain.

## Resume rules

When resuming work in a target repository:

1. Run `bash java-migration/scripts/bootstrap/migration-kit.sh resume <repo-root>`.
2. Read these files in order:
   - `docs/java-migration/PLAN.md`
   - `docs/java-migration/state/project.state.json`
   - `docs/java-migration/state/active-milestone.json`
   - `docs/java-migration/state/session-handoff.md`
3. Load only the ADRs, manifests, and scope runs needed for the listed scopes.
4. Continue from the persisted `operating_mode`, `current_phase`, and
   `next_scope_ids`.

## Context budget policy

This skill must operate as if context were a scarce runtime budget.

- Treat `50%` of the model context window as a hard operating ceiling.
- Treat `40%` as the mandatory stop-and-handoff threshold.
- Before crossing the `40%` threshold, stop active investigation or execution,
  persist the latest coherent state, and recommend opening a fresh session.
- Do not continue loading more files, compatibility notes, or evidence once the skill
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

## Simplification boundary

The skill should stay simple in one specific way:

- keep operational guidance centralized in this `SKILL.md`
- keep deterministic behavior in scripts and schemas
- keep repository-specific progress in the target `PLAN.md`

The skill should not simplify by:

- moving script logic back into prose
- scattering phase rules across many top-level documents
- relying on previous conversation context

## Bundled resources

- `scripts/bootstrap/` contains bootstrap and resume entrypoints.
- `scripts/state/` contains route validation and scope sync helpers.
- `scripts/discovery/` contains deterministic discovery normalizers.
- `scripts/openrewrite/` contains automated rewrite execution helpers.
- `scripts/wave-planner/` contains wave promotion logic.
- `scripts/last-mile/` contains residual-fix registration helpers.
- `references/` contains contracts, notes, the target plan template, and
  OpenRewrite presets under `references/openrewrite/presets/`.

## Required outputs

Before finishing, update:

- `docs/java-migration/PLAN.md`
- `docs/java-migration/state/project.state.json`
- `docs/java-migration/state/active-milestone.json`
- `docs/java-migration/state/session-handoff.md`

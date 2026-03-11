---
name: java-migration
description: Self-contained Agentic skill for Java migration. Use when assessing or executing a Maven-first Java migration, especially Java EE to Jakarta EE, and when you want one installable skill to bootstrap output, run discovery, plan waves, execute OpenRewrite, handle transformer exceptions, and stabilize the repository from persisted state.
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
Prefer fixing the smallest conflicting fields instead of rewriting whole
documents.

## Workflow

Follow progressive disclosure. Load the smallest amount of context that can
safely determine the next action, then expand only when the current phase or
mode requires it.

1. Run `bash java-migration/scripts/bootstrap/migration-kit.sh status <repo-root>`.
2. If `docs/java-migration` is missing or only reserved, inspect the repository
   root just enough to classify build system, module shape, and migration
   intent.
3. Read `docs/java-migration/state/project.state.json` first when it exists.
4. Read `docs/java-migration/state/active-milestone.json` only when milestone
   fields affect the next action.
5. Validate that `current_phase`, `operating_mode`, `next_skill`,
   `next_scope_ids`, and `build_system` are coherent with
   `scripts/state/statectl.py route` or the compatibility wrapper
   `scripts/state/resolve-state-route.py`.
6. Read `docs/java-migration/state/session-handoff.md` only when resuming or
   when blockers / pending decisions suggest unresolved session context.
7. Read `docs/java-migration/PLAN.md` only when state + handoff are
   insufficient to choose the next safe step.
8. Read only the ADRs, manifests, and scope runs needed for the active phase
   and the next selected scopes.
9. Use this `SKILL.md` as the canonical phase guidance for the installed skill.
10. Use the phase-specific scripts instead of making ad hoc state mutations.
11. Persist the updated repository `PLAN.md`, state, and handoff before ending
    the session, but keep each artifact as delta-only as possible.

## Artifact budget

Treat repository artifacts as operational indexes, not narratives.

- `project.state.json` is the primary machine-readable source of truth.
- `active-milestone.json` carries only milestone-local scope selection and
  completion state.
- `session-handoff.md` must be a minimal restart note, not a recap.
- `PLAN.md` must stay compact and readable in one screen when possible.
- `summary.state` files must stay factual and short.
- Do not duplicate the same explanation across all artifacts.
- When only one field changes, update only that field or the smallest relevant
  paragraph.
- Prefer terse factual bullets over chronological storytelling.

## Operational Guardrails

To ensure safety and functional integrity, the agent MUST adhere to these invariants:

### Business Logic Invariant
The agent MUST NOT modify, "simplify", or "refactor" any business logic, algorithms, or domain-specific calculations. Changes are STRICTLY limited to structural migration (namespaces, dependency versions, XML schemas). If a business logic change seems "necessary", it must be escalated to the user as a BLOCKER.

### API Adaptation Policy (Rule of Evidence)
Changes to method signatures or parameter types are permitted ONLY when:
1. **Required by the target library** (e.g., Hibernate 6 Query API or Jakarta Persistence 3.0 changes).
2. **Triggered by empirical evidence**: A specific compilation error (e.g., "incompatible types") must be captured before the fix.
3. **Minimality**: Apply the "Smallest Coherent Fix". Use casts or type conversions at the call site rather than rewriting surrounding logic.

### Documentation Preservation
The agent MUST preserve and update Javadoc when modifying method signatures. If a parameter type changes, the corresponding `@param` tag must be updated to reflect the new type or description. Javadoc MUST NOT be removed to simplify the migration.

### Test Integrity Policy
Tests MUST NOT be deleted. If a test fails after a structural migration:
1. **Fix**: If the failure is due to a simple API change (e.g., a mock returning the wrong type or a change in package name), fix the test code to match the new API. **The fix MUST NOT change the intended logic, assertions, expected values, or the scenarios being tested.** It should only adapt the test setup/harness to the new types and signatures.
2. **Disable (Last Resort)**: If the fix is complex or requires business logic decisions (such as changing the expected outcome to make the test pass), the agent MUST NOT modify the test logic or delete the test. It should instead:
    - Annotate with `@Disabled` (JUnit 5) or `@Ignore` (JUnit 4).
    - Add a mandatory comment: `// TODO: [REVISAR APÓS MIGRAÇÃO] Motivo: [DESCREVER_O_PROBLEMA]`.
    - Link to a BLOCKER in the `PLAN.md`.
3. **Evidence**: All test failures must be recorded in the state before any action is taken.
4. **Test Logic Invariant**: The agent is PROHIBITED from modifying assertions or test scenarios to "force" a test to pass. Any such attempt is a violation of the migration contract.

### XML Schema Consistency Guardrail
When updating namespaces in XML files (`web.xml`, `persistence.xml`, `beans.xml`, `ejb-jar.xml`), the agent MUST also update the `version` attribute and the `xsi:schemaLocation` URL to the matching Jakarta EE version (e.g., Servlet 4.0/5.0/6.0, Persistence 3.0/3.1). A namespace update without a matching schema version update is an incomplete migration and MUST be avoided.

### Dependency Clean-room Policy
The agent MUST ensure the `pom.xml` is free of residual `javax.*` dependencies that conflict with the new `jakarta.*` stack.
1. **Removal**: Explicitly remove legacy artifacts that are no longer needed or have been superseded.
2. **Exclusion**: If a transitive dependency pulls in legacy `javax` classes, use `<exclusions>` to prevent classpath pollution.
3. **Verification**: After automation, perform a visual scan of the dependency tree to ensure a clean Jakarta-only baseline.

### Decision Logging (Audit Trail)
Any non-trivial change (e.g., API adaptation, dependency removal, disabling a test, or an architectural tradeoff) MUST be recorded in the `Decisions` section of the repository `PLAN.md`.
- Format: `[DATE] [MODULE] Decision: [X] Rationale: [Y]`.
- This ensures a clear audit trail and explains the "why" behind the agent's actions for human reviewers.

### Java Version Alignment Guardrail
The agent MUST verify the project's Java version against the target Jakarta EE version using the `java-migration/references/java/jakarta-compatibility-matrix.md`.
1. **Verification**: Check Maven's `<maven.compiler.source>`, `<maven.compiler.target>`, and `<maven.compiler.release>` properties.
2. **Action**: If a version mismatch is detected (e.g., Jakarta EE 10 on Java 8), the agent SHOULD propose an upgrade to the required Java version in the `PLAN.md` before finalizing the migration.

### Literal String Deep Scan (JNDI/Reflection/Properties)
Namespace replacement often misses strings in JNDI lookups, reflection calls, or property keys.
1. **Scope**: Scan for literal strings containing `javax.servlet`, `javax.persistence`, `javax.ejb`, `javax.inject`, `javax.enterprise`, `javax.resource`, `javax.mail`, `javax.jms`, `javax.xml.ws`, `javax.xml.bind`.
2. **Context**: Check `InitialContext.lookup()`, `Class.forName()`, `ClassLoader.loadClass()`, and `.properties` files.
3. **Action**: Replace legacy namespaces in strings ONLY if they are intended to refer to Jakarta EE components. Record these changes in the decision log.

### Multi-module Dependency Strategy (Bottom-Up)
In multi-module Maven projects, the order of migration is critical to avoid cyclic compilation errors.
1. **Rule**: The agent MUST migrate modules from the bottom of the dependency graph upwards.
2. **Mapping**: Before planning waves, the agent SHOULD run `mvn dependency:tree` or inspect `pom.xml` files to identify leaf modules (those with no internal project dependencies).
3. **Sequence**: Migrate leaf modules first, followed by modules that depend on them.

### Atomic Rollback Protocol
To maintain repository integrity, every execution wave must be treated as an atomic operation.
1. **Pre-condition**: Ensure a clean `git status` before starting a wave.
2. **Failure Handling**: If a wave results in unresolved compilation errors or validation failures even after stabilization attempts, the agent MUST:
   - Perform a `git reset --hard` to return the repository to the pre-wave state.
   - Record the specific failure and root cause in the `PLAN.md`.
   - Mark the wave/scope as `blocked` in the state files.
3. **Goal**: Never leave the repository in a broken state between sessions.

### Incompatible Libraries Guardrail
During discovery, the agent MUST screen dependencies against `java-migration/references/compatibility/known-incompatible-libraries.md`.
1. **Detection**: Identify artifacts known to have hardcoded `javax` logic that cannot be fixed by bytecode transformation.
2. **Escalation**: Flag these as **Structural Blockers** in the `PLAN.md` and propose version upgrades as the primary solution.

### Public API & Binary Compatibility Check
The migration MUST NOT accidentally break the project's public contract with external clients.
1. **Rule**: Changes to public/protected method signatures or class hierarchies are only allowed for Jakarta EE compliance (refer to *API Adaptation Policy*).
2. **Verification**: After stabilization, the agent SHOULD perform a manual check of the public API surface. If a breaking change is detected that is not required by Jakarta, it must be reverted or justified in the decision log.

## Migration Tooling Orchestration

To achieve a professional-grade migration, the agent MUST follow this specific hierarchy during the **Execute** phase:

- **Step 1: Foundation (Eclipse Transformer CLI)**
  - **Role**: Authoritative baseline for total namespace replacement (javax -> jakarta) across all file types (Java, XML, Properties, SPI).
  - **Implementation**: Refer to `java-migration/references/transformer/cli-usage.md`.
  - **Output**: A project-wide Jakarta namespace baseline.

- **Step 2: API Refinement (OpenRewrite)**
  - **Role**: Specialist for complex library-specific transformations (e.g., Hibernate 6, Spring 6).
  - **Dynamic Discovery**: Use `mvn rewrite:discover` to find the most up-to-date recipes for the project's stack.
  - **Output**: Human-readable source code adapted to modern Jakarta breaking changes.

- **Step 3: Binary Safety (Eclipse Transformer Maven Plugin)**
  - **Role**: Final guard for third-party binary dependencies and final artifact compatibility.
  - **Implementation**: Refer to `java-migration/references/maven/eclipse-transformer.xml`.
  - **Output**: A 100% Jakarta-compatible deployment artifact.

## Standard workflow

### 1. Assess
Use for strategy and feasibility without code changes. Diagnose if the repo fits the `Maven-first` envelope.

### 2. Bootstrap
Initialize `docs/java-migration/` and official state files. Create the initial `PLAN.md`.

### 3. Discover
Gather baseline evidence. 
- **Incompatible Library Screening**: Screen dependencies against the `known-incompatible-libraries.md` reference.
- **Progressive Disclosure Rule**: Load ONLY the manifests and XML descriptors for the specific module/scope under analysis. Do not load the entire repository's discovery evidence at once.

### 4. Plan waves
Sequence scopes into small, reviewable waves.
- **Dependency Mapping**: Map the project's dependency graph to ensure a **Bottom-Up** sequence.
- **Wave Promotion**: Group leaf modules first. Promote `openrewrite_ready` scopes to execution.

### 5. Execute (Orchestrated Automation)
Apply the **Migration Tooling Orchestration** (Transformer -> OpenRewrite -> Plugin).
- **Atomicity**: Ensure a clean git state before execution. If the wave fails, apply the **Atomic Rollback Protocol**.
- **Validation**: Verify each step before moving to the next.
- **State**: Register outcomes in `active-milestone.json` and `project.state.json`.

### 6. Last-mile stabilization
Resolve residual issues after automation.
- **Evidence-first**: Run `mvn compile` and capture errors.
- **Literal String Verification**: Perform a targeted scan for `javax.*` leakage in JNDI lookups, Reflection calls, and properties files (refer to *Literal String Deep Scan*).
- **API Adaptation**: Fix signature mismatches triggered by evidence, following the *API Adaptation Policy*.
- **Audit**: Review and attempt to re-enable `@Disabled` tests with `// TODO: [REVISAR APÓS MIGRAÇÃO]`.

### 7. Controlled fallback
Handle explicit blockers where the normal path fails. Record the exception state and future removal conditions.
- persist the fallback through the state controller with explicit exception state
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

### Before last-mile stabilization

- deterministic automation has already run
- residual validation failure or manual follow-up is persisted

### Before controlled fallback

- normal upgrade path is explicitly ruled out
- the blocking artifact is identified
- the future removal condition is known

## Decision policy

- Prefer answering in product language first, then describe the active phase.
- Keep consultative answers in `assess` mode unless the user explicitly asked to
  start or resume the operational flow.
- `operating_mode` expresses the session intent; `current_phase` expresses the
  persisted workflow position.
- `resume` is an operating mode only. It must never be used as a phase.
- `next_skill` must remain `java-migration`; phase changes are expressed through
  `current_phase`, `operating_mode`, and `transition_reason`.
- Never move to a new phase without persisting `transition_reason`.
- Never mark a phase as `blocked` without a persisted blocker.
- Never create side documents outside `docs/java-migration`.
- Keep repository-specific progress in `docs/java-migration/PLAN.md`, not in
  the installed skill directory.

## Target repository PLAN.md contract

Each target repository must keep `docs/java-migration/PLAN.md` current.

It should stay compact and operational. **Markdown Guardrail: Every item MUST be a separate bullet point starting with `- ` or `1. ` and followed by a newline. DO NOT concatenate multiple items into a single paragraph.**

The recommended structure is:

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

Do not turn the repository plan into a long narrative. Avoid historical
play-by-play unless the current session still depends on it. It must stay easy
to resume from and cheap to maintain.

## Resume rules

When resuming work in a target repository:

1. Run `bash java-migration/scripts/bootstrap/migration-kit.sh resume <repo-root>`.
2. Read these files in order:
   - `docs/java-migration/state/project.state.json`
   - `docs/java-migration/state/active-milestone.json`
   - `docs/java-migration/state/session-handoff.md`
   - `docs/java-migration/PLAN.md` only if state + handoff do not already
     determine the next safe action
3. Load only the ADRs, manifests, and scope runs needed for the listed scopes.
4. Continue from the persisted `operating_mode`, `current_phase`, and
   `next_scope_ids`.

## Context budget policy

This skill must operate as if context were a scarce runtime budget.

- Treat the point at which `50%` of the model context window has been consumed
  as a hard operating ceiling.
- Treat the point at which `40%` of the model context window has been consumed
  as the mandatory stop-and-handoff threshold.
- Before crossing the `40% consumed` threshold, stop active investigation or
  execution, persist the latest coherent state, and recommend opening a fresh
  session.
- Do not continue loading more files, compatibility notes, or evidence once the skill
  judges that it is near `40% consumed` of the context window.
- The handoff must include the minimum restart context and a ready-to-send
  prompt for the next session.
- If exact runtime telemetry is unavailable, apply this conservatively based on
  observed prompt growth and stop early rather than risk crossing the `50%
  consumed` ceiling.

## Multi-agent policy

- This skill may use multiple AI sub-agents even though it is a single
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
- `scripts/state/` contains `statectl.py`, the centralized state transition and
  validation entrypoint, plus compatibility wrappers.
- `scripts/discovery/` contains deterministic discovery normalizers.
- `scripts/openrewrite/` contains automated rewrite execution helpers.
- `scripts/fallback/` contains controlled fallback registration helpers.
- `scripts/wave-planner/` and `scripts/last-mile/` keep compatibility entrypoints
  that delegate into `scripts/state/statectl.py`.
- `references/` contains contracts, notes, the target plan template, and
  OpenRewrite presets under `references/openrewrite/presets/`.

## Required outputs

Before finishing, update:

- `docs/java-migration/PLAN.md`
- `docs/java-migration/state/project.state.json`
- `docs/java-migration/state/active-milestone.json`
- `docs/java-migration/state/session-handoff.md`

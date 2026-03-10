#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
MIGRATION_DIR="${ROOT_DIR%/}/docs/java-migration"
STATE_DIR="${MIGRATION_DIR}/state"
ADR_DIR="${MIGRATION_DIR}/adr"
MILESTONES_DIR="${MIGRATION_DIR}/milestones"
DISCOVERY_DIR="${MIGRATION_DIR}/discovery-protocol"

timestamp_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

detect_build_system() {
  if [[ -f "${ROOT_DIR%/}/pom.xml" || -x "${ROOT_DIR%/}/mvnw" ]]; then
    echo "maven"
  elif [[ -f "${ROOT_DIR%/}/build.gradle" || -f "${ROOT_DIR%/}/build.gradle.kts" || -x "${ROOT_DIR%/}/gradlew" ]]; then
    echo "gradle"
  else
    echo "unknown"
  fi
}

detect_build_files_json() {
  local -a files=()
  for file in pom.xml mvnw .mvn/wrapper/maven-wrapper.properties build.gradle build.gradle.kts gradlew settings.gradle settings.gradle.kts; do
    if [[ -e "${ROOT_DIR%/}/${file}" ]]; then
      files+=("\"${file}\"")
    fi
  done

  if [[ ${#files[@]} -eq 0 ]]; then
    printf '[]'
  else
    local joined
    joined="$(IFS=,; echo "${files[*]}")"
    printf '[%s]' "${joined}"
  fi
}

mkdir -p "${MIGRATION_DIR}"

if [[ ! -f "${MIGRATION_DIR}/README.md" ]]; then
  cat > "${MIGRATION_DIR}/README.md" <<'EOF'
# Java Migration Output

Output materializado pelo kit de migracao orientado a IA para o projeto atual.

- este repositorio contem a ferramenta reutilizavel.
- `docs/java-migration` contem apenas o estado, os artefatos e os runs deste projeto.
EOF
fi

if [[ ! -f "${MIGRATION_DIR}/PLAN.md" ]]; then
  cat > "${MIGRATION_DIR}/PLAN.md" <<'EOF'
# Java Migration Plan

## Objective

- Repository:
- Migration goal:
- Current stack:
- Target stack:

## Current Status

- Date:
- Operating mode: bootstrap
- Current phase: bootstrap_governance
- Active milestone: milestone-0-discovery
- Active wave: wave-0
- Summary: Bootstrap initialized and waiting for repository inspection.

## Decisions

- YYYY-MM-DD: confirm target runtime, framework, and namespace strategy.

## Scope And Waves

- Current wave: wave-0
- Selected scopes: none
- Blocked scopes: none
- Deferred scopes: none

## Validation

- Required checks: confirm build system, module layout, and initial migration envelope.
- Latest results: pending.
- Known failing modules: unknown.

## Risks And Blockers

- Active blockers: none.
- Fallbacks in use: none.
- Removal conditions: n/a.

## Next Actions

- Next step: inspect repository root and confirm supported migration envelope.
- Then: create ADR seed and initial scopes for discovery.

## Session Resume

1. Run `bash java-migration/scripts/bootstrap/migration-kit.sh resume .`
2. Read `docs/java-migration/state/project.state.json`
3. Read `docs/java-migration/state/active-milestone.json`
4. Read `docs/java-migration/state/session-handoff.md`
5. Read `docs/java-migration/PLAN.md` only if state + handoff do not settle the next action
6. Load only the ADRs and scope runs needed for the listed next scopes
EOF
fi

mkdir -p "${STATE_DIR}" "${ADR_DIR}" "${MILESTONES_DIR}" "${DISCOVERY_DIR}/manifests" "${DISCOVERY_DIR}/runs" "${MIGRATION_DIR}/openrewrite-runs"

if [[ ! -f "${STATE_DIR}/project.state.json" ]]; then
  cat > "${STATE_DIR}/project.state.json" <<EOF
{
  "state_schema_version": "2.2",
  "project_id": "$(basename "$(cd "${ROOT_DIR}" && pwd)")",
  "repository_id": "$(basename "$(cd "${ROOT_DIR}" && pwd)")",
  "repository_root": "$(cd "${ROOT_DIR}" && pwd)",
  "build_system": "$(detect_build_system)",
  "build_files": $(detect_build_files_json),
  "current_stack": {
    "java_version": "unknown",
    "namespace": "unknown",
    "platform": "unknown",
    "framework": "",
    "runtime": "unknown"
  },
  "target_stack": {
    "java_version": "17",
    "namespace": "jakarta",
    "platform": "jakarta-ee",
    "framework": "",
    "runtime": "target-to-confirm"
  },
  "operating_mode": "bootstrap",
  "current_phase": "bootstrap_governance",
  "phase_status": "pending",
  "transition_reason": "Bootstrap initialized and waiting for repository inspection",
  "active_adr_ids": [
    "adr-001-target-stack",
    "adr-002-migration-strategy"
  ],
  "active_milestone_id": "milestone-0-discovery",
  "next_skill": "java-migration",
  "context_budget": {
    "warning_threshold_percent": 30,
    "handoff_threshold_percent": 40,
    "hard_ceiling_percent": 50,
    "fallback_strategy": "persist_state_and_open_new_session"
  },
  "next_scope_ids": [],
  "global_blockers": [],
  "pending_decisions": [],
  "exception_state": null,
  "capabilities": {
    "bootstrap_supported": true,
    "discovery_supported": true,
    "wave_planning_supported": true,
    "openrewrite_supported": $(if [[ "$(detect_build_system)" == "maven" ]]; then echo "true"; else echo "false"; fi),
    "transformer_supported": true,
    "manual_fixes_supported": true
  },
  "phase_history": [
    {
      "phase": "bootstrap_governance",
      "status": "pending",
      "reason": "Bootstrap initialized",
      "changed_at": "$(timestamp_utc)"
    }
  ],
  "last_updated": "$(timestamp_utc)",
  "notes": "Bootstrap initialized"
}
EOF
fi

if [[ ! -f "${STATE_DIR}/active-milestone.json" ]]; then
  cat > "${STATE_DIR}/active-milestone.json" <<EOF
{
  "state_schema_version": "2.0",
  "milestone_id": "milestone-0-discovery",
  "milestone_type": "discovery",
  "goal": "Create the initial migration baseline, define scopes, and identify blockers",
  "status": "pending",
  "wave_id": "wave-0",
  "entry_criteria": [
    "Repository root inspected",
    "Build system identified"
  ],
  "exit_criteria": [
    "ADR seed created",
    "Scope manifest created",
    "Baseline discovery completed"
  ],
  "selected_scope_ids": [],
  "completed_scope_ids": [],
  "stabilized_scope_ids": [],
  "pending_scope_ids": [],
  "blocked_scope_ids": [],
  "deferred_scope_ids": [],
  "next_scope_ids": [],
  "blocking_decision_ids": [],
  "success_metrics": [
    "Build system classified",
    "Initial scopes persisted",
    "Priority blockers surfaced"
  ],
  "artifacts_required": [
    "docs/java-migration/adr/adr-001-target-stack.md",
    "docs/java-migration/adr/adr-002-migration-strategy.md",
    "docs/java-migration/discovery-protocol/manifests/scopes.csv"
  ],
  "last_updated": "$(timestamp_utc)"
}
EOF
fi

if [[ ! -f "${STATE_DIR}/session-handoff.md" ]]; then
  cat > "${STATE_DIR}/session-handoff.md" <<'EOF'
# Session Handoff

- operating_mode: bootstrap
- phase: bootstrap_governance
- phase_status: pending
- active_milestone: milestone-0-discovery
- next_skill: java-migration
- context_warning_threshold_percent: 30
- context_handoff_threshold_percent: 40
- context_hard_ceiling_percent: 50
- next_action: inspect the repository, create ADR seed, and define initial scopes
- if_near_context_limit: stop, persist official state, and continue in a new session
- global_blockers: none

## Next Session Prompt

Use $java-migration for this repository. Start by running `bash java-migration/scripts/bootstrap/migration-kit.sh resume .`, then read `docs/java-migration/state/project.state.json`, `docs/java-migration/state/active-milestone.json`, and `docs/java-migration/state/session-handoff.md` in that order. Read `docs/java-migration/PLAN.md` only if those files do not already determine the next safe action. Respect the persisted context budget policy: warn near 30%, stop and hand off at 40%, and never continue past 50% of the context window. Load only the ADRs and scope runs required for the listed next scopes, then continue from the persisted `operating_mode`, `current_phase`, and `next_scope_ids`.
EOF
fi

if [[ ! -f "${ADR_DIR}/adr-001-target-stack.md" ]]; then
  cat > "${ADR_DIR}/adr-001-target-stack.md" <<'EOF'
# ADR-001: target stack

Status: proposed

## Context

Fill after repository bootstrap.

## Decision

Define target runtime, language level, framework level, and build constraints.

## Consequences

List benefits, costs, and review triggers.
EOF
fi

if [[ ! -f "${ADR_DIR}/adr-002-migration-strategy.md" ]]; then
  cat > "${ADR_DIR}/adr-002-migration-strategy.md" <<'EOF'
# ADR-002: migration strategy

Status: proposed

## Context

Fill after repository bootstrap.

## Decision

Define the official migration strategy, sequencing, and fallback rules.

## Consequences

List the expected operational impact and exception triggers.
EOF
fi

if [[ ! -f "${MILESTONES_DIR}/milestone-0-discovery.md" ]]; then
  cat > "${MILESTONES_DIR}/milestone-0-discovery.md" <<'EOF'
# Milestone 0: discovery

## Goal

Establish the migration baseline, discover scopes, and surface blockers.

## In scope

- build inventory
- dependency inventory
- scope inventory
- compatibility hotspots

## Out of scope

- full execution plan
- large-scale code changes
- bulk automated rewrites
EOF
fi

if [[ ! -f "${DISCOVERY_DIR}/manifests/scopes.csv" ]]; then
  printf 'scope_id,scope_type,scope_path,scope_name,inventory_mode,status,notes\n' > "${DISCOVERY_DIR}/manifests/scopes.csv"
fi

printf 'Migration kit initialized at %s\n' "${MIGRATION_DIR}"

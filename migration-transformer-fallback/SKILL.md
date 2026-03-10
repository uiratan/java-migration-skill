---
name: migration-transformer-fallback
description: Handle exception cases that require Eclipse Transformer or compatibility-based fallback. Use when a third-party artifact has no viable Jakarta-ready version, when source-level rewrite is impossible, or when a controlled temporary compatibility bridge must be documented.
---

# Migration Transformer Fallback

Use this skill only for controlled exceptions.

This skill must stay exceptional and must not become a generic compatibility
path.

## Workflow

1. Confirm that normal upgrade or source rewrite is not viable.
2. Record the blocking artifact and why it blocks the target stack.
3. Apply `Eclipse Transformer` only to the minimal necessary artifact set.
4. Register the fallback in project state, milestone state, and the relevant
   scope run notes.
5. Define the future removal condition.

## Rules

- This is not a default path.
- Every use must be traceable.
- Every use must include an exit condition.
- Every use must update only the official state and run artifacts.

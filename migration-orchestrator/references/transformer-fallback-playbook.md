# Transformer Fallback Playbook

Use this playbook only for controlled exceptions.

Workflow:

1. Confirm that normal upgrade or source rewrite is not viable.
2. Record the blocking artifact and why it blocks the target stack.
3. Apply Eclipse Transformer only to the minimal necessary artifact set.
4. Register the fallback in project state, milestone state, and the relevant scope run notes.
5. Define the future removal condition.

Rules:

- This is not a default path.
- Every use must be traceable.
- Every use must include an exit condition.

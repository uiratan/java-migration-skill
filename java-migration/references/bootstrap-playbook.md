# Bootstrap Playbook

Use this playbook when `docs/java-migration` is missing or only reserved.

Workflow:

1. Inspect the repository root, build files, module layout, CI files, and
   README.
2. Run `scripts/bootstrap/migration-kit.sh start <repo-root>` when the official
   migration output is missing.
3. Ensure the first run leaves the expected output contract in `docs/java-migration`.
4. Populate the official state and initial scope manifest.
5. Hand off to structured discovery.

Rules:

- Do not start bulk migration during bootstrap.
- Prefer the bundled bootstrap scripts over recreating files by hand.
- Leave the persisted state resumable without prior chat context.
- Seed the official context budget policy in persisted state and handoff output.

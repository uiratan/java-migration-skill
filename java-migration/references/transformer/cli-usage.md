# Eclipse Transformer CLI Reference

Use this reference during **Phase 1: Foundation** to perform a project-wide namespace replacement.

## Core Command Pattern

The primary usage is via the Java JAR. The agent MUST identify the CLI JAR version in the environment or download the latest one if missing.

```bash
java -jar org.eclipse.transformer.cli-0.5.0.jar \
     <source-directory> \
     <target-directory> \
     -o \
     -t jakarta-defaults.properties
```

## Key Flags

- `<source-directory>`: The path to the project root or module being migrated.
- `<target-directory>`: The destination path (can be the same as source for in-place transformation if using `-o`).
- `-o`: Overwrite the source files (use this when working within a git repository after a clean commit).
- `-t <rules>`: The transformation rules to apply. Use `jakarta-defaults.properties` for the standard `javax` to `jakarta` migration.

## Execution Guardrails

1. **Clean Workspace**: Ensure `git status` is clean before running the Transformer.
2. **Selective Transformation**: Focus on `src/main/java`, `src/main/resources`, and `src/test/java`.
3. **Artifact Skipping**: The agent MUST NOT run the Transformer on the `target/` directory or `.git/` folder.
4. **Validation**: After transformation, verify that file encodings (UTF-8) are preserved and that the total file count remains consistent.

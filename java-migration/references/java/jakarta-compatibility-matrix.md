# Jakarta EE & Java Compatibility Matrix

Use this matrix to verify if the project's Java version is compatible with the target Jakarta EE version.

| Jakarta EE Version | Minimum Java Version | Recommended Java Version | Notes |
| :--- | :--- | :--- | :--- |
| **8** | 8 | 8 | Still uses `javax.*` namespace. |
| **9 / 9.1** | 8 (9) / 11 (9.1) | 11 | First versions using `jakarta.*` namespace. |
| **10** | 11 | 17 | Current industry standard for modern apps. |
| **11** | 21 | 21 | Future-proofing with latest LTS. |

## Verification Checkpoints

1. **Maven Compiler Plugin**: Check `<source>` and `<target>` (or `<release>`) in `pom.xml`.
2. **Maven Enforcer Plugin**: If present, verify `<requireJavaVersion>` rule.
3. **Environment**: Verify if the CI/CD pipeline and runtime server match these requirements.

## Guardrail: Java Version Alignment
The agent MUST NOT complete a migration to Jakarta EE 9+ while the project is still targeting Java 8, as it will likely lead to runtime ClassCastExceptions or NoClassDefFoundErrors due to bytecode version mismatches.

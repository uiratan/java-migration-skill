# Known Incompatible Libraries (Jakarta EE Migration)

Use this reference during **Phase 3: Discover** to identify libraries that are difficult or impossible to migrate without deep architectural changes.

| Library | Known Issues | Suggested Alternative |
| :--- | :--- | :--- |
| **JBPM 3 (jbpm-jpdl / jbpm-identity)** | Heavily tied to Hibernate 3/4 and legacy JTA. No Jakarta path exists. | Migrate to JBPM 7+ or Camunda (Architectural change). |
| **Keycloak Adapters** | Deprecated. `keycloak-spring-boot-starter` does not support Jakarta EE 9+. | Use native **Spring Security OIDC** or Quarkus OIDC. |
| **JSF / Mojarra 2.x (`com.sun.faces`)** | Hardcoded to `javax.faces`. Massive breaking changes in Faces 4.0. | Upgrade to `org.glassfish:jakarta.faces`. |
| **JavaMail (`com.sun.mail`)** | Implementation tied to `javax.mail`. | Upgrade to **Eclipse Angus** (`org.eclipse.angus:jakarta.mail`). |
| **RESTEasy (< 6.x)** | Older versions are bound to `javax.ws.rs`. | Upgrade to **RESTEasy 6.x**. |
| **Jackrabbit 2.x (jackrabbit-core)** | Legacy JCR implementation with deep `javax.jcr` ties. | Upgrade to Jackrabbit Oak or isolate. |
| **Old Apache CXF (< 3.5)** | Heavy internal dependencies on `javax.xml.ws` and `javax.xml.bind`. | Upgrade to CXF 4.0+. |
| **Spring Framework 5.x** | Does not support Jakarta EE 9+ natively (hardcoded `javax.*`). | Upgrade to Spring 6.x / Boot 3.x. |
| **Hibernate 5.x** | Requires specific transformer configurations and has limited Jakarta support. | Upgrade to Hibernate 6.x. |
| **Jersey 2.x** | Hardcoded to `javax.ws.rs`. Transformation is unstable. | Upgrade to Jersey 3.x. |
| **Arquillian Persistence (< 2.0)** | Internal use of `javax.transaction` for test state management. | Upgrade to Jakarta-compatible Arquillian adapters. |
| **Bouncy Castle Mail (bcmail-*)** | Often depends on `javax.mail` for S/MIME operations. | Use `jakarta.mail` compatible Bouncy Castle versions. |
| **Old Quartz Scheduler** | Uses `javax.transaction` and `javax.mail` internally. | Upgrade to Quartz 2.4+. |
| **Apache Shiro (< 2.0)** | Direct dependency on `javax.servlet`. | Upgrade to Shiro 2.0+. |
| **Mirror / Reflection Libs** | Risk of hardcoded class name lookups (e.g., `Class.forName("javax...")`). | Manual audit of reflection calls required. |

## Strategy for Incompatible Libraries

1. **Detection**: If these libraries are found in `pom.xml` during discovery, flag them as **BLOQUEIOS ESTRUTURAIS**.
2. **Action**: Propose a major version upgrade (refer to the alternative above).
3. **Escalation**: If no alternative is available, mark the scope as `controlled_fallback_required` and document the risk in `PLAN.md`.

## Guardrail: Reflection & String Literals
Libraries like **Mirror**, **Reflections**, or custom **Class.forName** calls MUST be audited. Even if the bytecode is transformed, a string `"javax.servlet.http.HttpServlet"` inside a reflection call will NOT be changed by most tools and will cause a `ClassNotFoundException` at runtime.

## Guardrail: Binary Transformation Limit
Eclipse Transformer CANNOT fix libraries that use heavy reflection on internal `javax` classes at runtime. If a library is on this list, a binary transformation alone is likely to fail.

---
id: F47-advanced-rbac
type: report
summary: "Implemented Role-Based Access Control (Admin, Operator, Viewer)"
status: completed
validations:
  - unit_tests: "tests/unit/test_auth.py: 100% pass"
  - integration_tests: "tests/integration/test_cli_auth_rbac_admin.py: 100% pass"
  - lint: "ruff check passed"
  - typecheck: "mypy passed"
security_review:
  verdict: approved
  risks:
    - risk: "Privilege escalation via token issue"
      mitigation: "Only 'auth:manage' permission (admin) can issue tokens."
    - risk: "Role confusion"
      mitigation: "Explicit Role enum and strict Pydantic validation."
    - risk: "Inconsistent enforcement"
      mitigation: "Centralized _resolve_principal_id check in CLI entry points."
  notes: "The implementation relies on the filesystem for persistence (auth-registry.json). File permissions (0600) are enforced by AuthRegistryStore."
---

# Feature Report: F47 - Advanced RBAC

## Contexto

The AIgnt OS CLI previously operated with a flat authorization model (all valid tokens had full access). As the system scales to support different user personas (viewers vs operators vs admins), a more granular permission system was required.

## Mudanças Realizadas

1.  **Auth Model**: Introduced `AuthRole` (admin, operator, viewer) and `Permission` sets.
2.  **Registry**: Updated `AuthRegistryStore` to persist roles alongside principal IDs.
3.  **CLI Enforcement**: Added `_resolve_principal_id(permission=...)` checks to all sensitive commands.
    - `runs submit`, `runs stop` -> `run:write`
    - `runs list`, `runs show`, `runs watch`, `runs follow` -> `run:read`
    - `runtime *` -> `runtime:manage`
    - `auth issue`, `auth disable` -> `auth:manage`
4.  **CLI UX**: Added `--role` flag to `auth issue` and `auth init` to create principals with specific roles.

## Validação

- **Unit Tests**: Verified `is_authorized` logic and `AuthRegistryStore` persistence.
- **Integration Tests**: Verified CLI behavior for different roles (viewer cannot submit run, operator cannot issue tokens).
- **Regression**: Verified existing auth flows remain functional (backward compatibility for tokens without explicit role in old registries, though new registry structure enforces it).

## Próximos Passos

- Consider moving to a database-backed auth store for higher concurrency/security in future.
- Add "service account" concept if non-human actors need specific subsets of permissions beyond standard roles.

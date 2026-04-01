---
id: F67-workspace-management-v2
type: feature
summary: Workspace Management v2 with per-run workspace isolation, lifecycle hooks, and workspace pool for reuse.
inputs:
    - Existing WorkspaceProvider protocol
    - Run lifecycle events
outputs:
    - WorkspaceState enum and TrackedWorkspace model
    - WorkspacePool with acquire/release/discard
    - WorkspaceManager integrating providers and pool
acceptance_criteria:
    - WorkspaceProvider creates isolated per-run workspace directories
    - WorkspaceProvider tracks workspace lifecycle states
    - Workspace cleanup hook is called when run completes
    - Workspace pool holds up to N reusable idle workspaces
    - Reuse of pooled workspace resets its contents
    - All unit tests pass
non_goals:
    - Cross-session workspace persistence
    - Workspace templates
    - Multi-tenant isolation
---

# Contexto

O sistema atual de workspace em `runtime_contracts.py` (`WorkspaceProvider`, `LocalWorkspaceProvider`, `RunScopedWorkspaceProvider`) não suporta pool de workspaces para reuse, lifecycle hooks de cleanup, tracking de estado ou reset de workspace antes de reuse.

# Objetivo

Introduzir WorkspaceState enum, TrackedWorkspace, WorkspacePool com acquire/release/reset, Lifecycle hooks de cleanup, e WorkspaceManager que integra providers + pool.

## 1. Decision

Introduzir:

1. **WorkspaceState enum** — `CREATING`, `READY`, `BUSY`, `CLEANUP`, `DESTROYED`
2. **TrackedWorkspace** — workspace com state tracking e metadata
3. **WorkspacePool** — pool fixo de workspaces idle que podem ser reutilizados
4. **Lifecycle hooks** — `on_workspace_cleanup(path)` callback

## 2. Scope

### In Scope

- `WorkspaceState` enum
- `TrackedWorkspace` model
- `WorkspacePool` class com acquire/release/reset
- `WorkspaceManager` que integra providers + pool
- Unit tests

### Out of Scope

- Persistência de workspace entre sessões
- Workspace templates
- Multi-tenant workspace isolation

## 3. Files

- `src/synapse_os/workspace.py` (novo)
- `tests/unit/test_workspace_v2.py` (novo)

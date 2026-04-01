---
id: F67-workspace-management-v2
type: feature
summary: Workspace Management v2 with per-run workspace isolation, workspace lifecycle hooks, and workspace pool for reuse.
status: ready
created: 2026-03-31
owner: agent
inputs: []
outputs: []
acceptance_criteria:
    - WorkspaceProvider creates isolated per-run workspace directories
    - WorkspaceProvider tracks workspace lifecycle (creating/ready/cleanup)
    - Workspace cleanup hook is called when run completes
    - Workspace pool holds up to N reusable idle workspaces
    - Reuse of pooled workspace resets its contents
    - All new unit tests pass; existing workspace tests continue to pass
non_goals: []
---

# Contexto

O sistema atual de workspace em `runtime_contracts.py` (`WorkspaceProvider`, `LocalWorkspaceProvider`, `RunScopedWorkspaceProvider`) não suporta:

- Pool de workspaces para reuse
- Lifecycle hooks de cleanup
- Tracking de estado de workspace (creating/ready/cleanup)
- Reset de workspace antes de reuse

# Decisão

Introduzir:

1. **WorkspaceState enum** — `CREATING`, `READY`, `BUSY`, `CLEANUP`, `DESTROYED`
2. **TrackedWorkspace** — workspace com state tracking e metadata
3. **WorkspacePool** — pool fixo de workspaces idle que podem ser reutilizados
4. **Lifecycle hooks** — `on_workspace_cleanup(path)` callback

# Escopo

## Dentro do Escopo

- `WorkspaceState` enum
- `TrackedWorkspace` model
- `WorkspacePool` class com acquire/release/reset
- `WorkspaceManager` que integra providers + pool
- Unit tests

## Fora do Escopo

- Persistência de workspace entre sessões
- Workspace templates
- Multi-tenant workspace isolation

# Arquivos

- `src/synapse_os/workspace.py` (novo)
- `tests/unit/test_workspace_v2.py` (novo)

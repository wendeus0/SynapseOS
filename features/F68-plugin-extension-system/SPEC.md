---
id: F68-plugin-extension-system
type: feature
summary: Plugin/Extension system with hook-based registration, entry point discovery, and lifecycle management.
inputs:
    - Existing hooks.py hook system
    - Python entry point mechanism
outputs:
    - PluginManifest dataclass with name, version, hooks
    - PluginRegistry singleton with discovery and lifecycle
    - load_plugins() via entry point discovery
acceptance_criteria:
    - Plugins are discovered via entry point group synapse_os.plugins
    - Plugin manifest declared via hook_manifest function
    - PluginRegistry tracks loaded plugins and hook handlers
    - load_plugins() discovers and loads all installed plugins
    - unload_plugin() removes plugin and its handlers
    - Plugin can declare pre_step, post_step, on_run_start, on_run_end hooks
    - All unit tests pass
non_goals:
    - Plugin sandboxing/security
    - Plugin packaging/distribution
    - Plugin config API
    - Hot reload
---

# Contexto

O sistema atual de hooks em `hooks.py` suporta apenas hooks internos registrados manualmente. Não existe mecanismo para extensões externas descobrirem e registrarem hooks no Synapse-Flow.

# Objetivo

Introduzir PluginManifest, PluginRegistry singleton com discovery e lifecycle, entry point group `synapse_os.plugins` para descoberta automática, load_plugins() e unload_plugin().

## 1. Decision

Introduzir:

1. **PluginManifest** — dataclass com name, version, hooks, enabled
2. **PluginRegistry** — singleton que gerencia plugins descobertos e carregados
3. **entry point group** `synapse_os.plugins` para descoberta automática
4. **load_plugins()** — descobre e registra todos os plugins via entry points
5. **unload_plugin(name)** — remove plugin do registry

## 2. Scope

### In Scope

- PluginManifest dataclass
- PluginRegistry com discovery e lifecycle
- Entry point based plugin discovery
- Unit tests

### Out of Scope

- Plugin sandboxing/security
- Plugin packaging/distribution
- Plugin config API
- Hot reload

## 3. Files

- `src/synapse_os/plugins.py` (novo)
- `tests/unit/test_plugins.py` (novo)

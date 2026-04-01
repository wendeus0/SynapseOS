---
id: F68-plugin-extension-system
type: feature
summary: Plugin/Extension system with hook-based registration, discovery, and lifecycle management.
status: ready
created: 2026-03-31
owner: agent
inputs: []
outputs: []
acceptance_criteria:
    - Plugins are discovered via entry point group synapse_os.plugins
    - Plugin manifest (name, version, hooks) is declared via hook_manifest function
    - PluginRegistry tracks loaded plugins and their hook handlers
    - load_plugins() discovers and loads all installed plugins
    - unload_plugin() removes plugin and its handlers from registry
    - Plugin can declare pre_step, post_step, on_run_start, on_run_end hooks
    - All new unit tests pass
non_goals: []
---

# Contexto

O sistema atual de hooks em `hooks.py` suporta apenas hooks internos registrados manualmente. Não existe mecanismo para extensões externas descobrirem e registrarem hooks no Synapse-Flow.

# Decisão

Introduzir:

1. **PluginManifest** — dataclass com name, version, hooks, enabled
2. **PluginRegistry** — singleton que gerencia plugins descobertos e carregados
3. **entry point group** `synapse_os.plugins` para descoberta automática
4. **load_plugins()** — descobre e registra todos os plugins via entry points
5. **unload_plugin(name)** — remove plugin do registry

# Escopo

## Dentro do Escopo

- PluginManifest dataclass
- PluginRegistry com discovery e lifecycle
- Entry point based plugin discovery
- Unit tests

## Fora do Escopo

- Plugin sandboxing/security
- Plugin packaging/distribution
- Plugin config API
- Hot reload

# Arquivos

- `src/synapse_os/plugins.py` (novo)
- `tests/unit/test_plugins.py` (novo)

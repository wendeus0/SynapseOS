---
id: F63-memory-engine-enhancement
type: feature
summary: Artifact metadata, indexed artifact store, and namespace-scoped memory store for run context persistence.
inputs:
    - Existing artifact store and report generator
    - Run context and feature metadata
outputs:
    - ArtifactMetadata Pydantic model
    - IndexedArtifactStore with find_by_tag and find_by_type
    - MemoryStore with JSON-file backing and namespace isolation
acceptance_criteria:
    - ArtifactMetadata has type, tags, source_step, created_at fields
    - IndexedArtifactStore.find_by_tag returns tagged artifacts
    - MemoryStore.get/set/delete works with namespace isolation
    - feature_memory returns namespaced view
    - All unit tests pass
non_goals:
    - Vector/semantic search
    - Cross-process memory sharing
---

# Contexto

The current `RunReportGenerator` produces basic markdown reports with limited metadata. The `artifact_store` is a simple file-based store with no indexing or search. Memory for feature state is entirely external with no integration into the runtime's artifact model.

# Objetivo

Introduce `ArtifactMetadata`, `IndexedArtifactStore`, and `MemoryStore` to support richer structured metadata, fast artifact lookup, and a clean interface for persisting run context and feature decisions.

## 1. Decision

We introduce three complementary components:

1. **`ArtifactMetadata`** — a Pydantic model attached to each artifact, containing type, tags, source_step, and created_at. Artifacts without metadata get a default entry.

2. **`IndexedArtifactStore`** — wraps the existing artifact store with an in-memory index mapping `run_id → artifact_name → ArtifactMetadata`. Supports `find_by_tag`, `find_by_type`, and `list_for_run`.

3. **`MemoryStore`** — a minimal key-value store backed by JSON files in the runtime state directory. Keys are namespaced (`memory:<namespace>:<key>`). Supports `get`, `set`, `delete`, and `list_namespaces`. Provides `feature_memory()` to scope operations to the current feature.

These components are purely additive — no existing behavior changes.

## 2. Scope

### In Scope

- `ArtifactMetadata` Pydantic model (type, tags, source_step, created_at)
- `IndexedArtifactStore` class with in-memory index and lookup methods
- `MemoryStore` class with JSON-file backing and namespace isolation
- `feature_memory()` helper on `MemoryStore` returning a namespaced view
- Unit tests for all three components
- `ArtifactMetadata` attached to `StepExecutionResult` artifacts field (optional key)

### Out of Scope

- Vector/semantic search
- Cross-process memory sharing
- Automatic memory population from runs
- Integration with opencode memory blocks

## 3. Files

- `src/synapse_os/memory.py` — all new memory/artifact index classes
- `tests/unit/test_memory.py` — unit tests

## 4. Acceptance Criteria

| #   | Criterion                                                                                             |
| --- | ----------------------------------------------------------------------------------------------------- |
| 1   | `ArtifactMetadata` has fields: type (str), tags (list[str]), source_step (str), created_at (datetime) |
| 2   | `IndexedArtifactStore.find_by_tag("error")` returns artifacts tagged "error"                          |
| 3   | `IndexedArtifactStore.find_by_type("test_report")` returns artifacts of that type                     |
| 4   | `MemoryStore.set("ns", "key", "value")` persists and `get("ns", "key")` retrieves it                  |
| 5   | `MemoryStore.list_namespaces()` returns all namespaces                                                |
| 6   | `feature_memory("F63")` returns a namespaced view that only touches F63 keys                          |
| 7   | All unit tests pass; existing tests continue to pass                                                  |
| 8   | `ArtifactMetadata` is added to `StepExecutionResult` artifacts field (optional key)                   |

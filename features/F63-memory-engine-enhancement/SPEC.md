---
feature_id: F63
title: Memory Engine Enhancement
status: draft
created: 2026-03-31
owner: agent
tags: [memory, reporting, artifacts, observability]
---

# F63 — Memory Engine Enhancement

## 1. Context

The current `RunReportGenerator` produces basic markdown reports with limited metadata. The `artifact_store` is a simple file-based store with no indexing or search. Memory for feature state is entirely external (opencode memory blocks) with no integration into the runtime's artifact model.

The system needs to support richer structured metadata for artifacts, a simple in-memory artifact index for fast lookup, and a `MemoryStore` abstraction that provides a clean interface for persisting run context, feature decisions, and cross-run memory — all while keeping the implementation minimal.

## 2. Decision

We introduce three complementary components:

1. **`ArtifactMetadata`** — a Pydantic model attached to each artifact, containing type, tags, source_step, and created_at. Artifacts without metadata get a default entry.

2. **`IndexedArtifactStore`** — wraps the existing artifact store with an in-memory index mapping `run_id → artifact_name → ArtifactMetadata`. Supports `find_by_tag`, `find_by_type`, and `list_for_run`.

3. **`MemoryStore`** — a minimal key-value store backed by JSON files in the runtime state directory. Keys are namespaced (`memory:<namespace>:<key>`). Supports `get`, `set`, `delete`, and `list_namespaces`. Provides `feature_memory()` to scope operations to the current feature.

These components are purely additive — no existing behavior changes.

## 3. Scope

### In Scope

- `ArtifactMetadata` Pydantic model (type, tags, source_step, created_at)
- `IndexedArtifactStore` class with in-memory index and lookup methods
- `MemoryStore` class with JSON-file backing and namespace isolation
- `feature_memory()` helper on `MemoryStore` returning a namespaced view
- Unit tests for all three components
- `ArtifactMetadata` attached to `StepExecutionResult`

### Out of Scope

- Vector/semantic search
- Cross-process memory sharing
- Automatic memory population from runs
- Integration with opencode memory blocks

## 4. Files

- `src/synapse_os/memory.py` — all new memory/artifact index classes
- `tests/unit/test_memory.py` — unit tests

## 5. Acceptance Criteria

| #   | Criterion                                                                                             |
| --- | ----------------------------------------------------------------------------------------------------- |
| 1   | `ArtifactMetadata` has fields: type (str), tags (list[str]), source_step (str), created_at (datetime) |
| 2   | `IndexedArtifactStore.find_by_tag("error")` returns artifacts tagged "error"                          |
| 3   | `IndexedArtifactStore.find_by_type("test_report")` returns artifacts of that type                     |
| 4   | `MemoryStore.set("ns", "key", "value")` persists and `get("ns", "key")` retrieves it                  |
| 5   | `MemoryStore.list_namespaces()` returns all namespaces                                                |
| 6   | `feature_memory("F59")` returns a namespaced view that only touches F59 keys                          |
| 7   | All unit tests pass; existing tests continue to pass                                                  |
| 8   | `ArtifactMetadata` is added to `StepExecutionResult` artifacts field (optional key)                   |

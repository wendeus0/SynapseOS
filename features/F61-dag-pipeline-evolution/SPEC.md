---
id: F61-dag-pipeline-evolution
type: feature
summary: DAG-aware pipeline executor with parallel step execution, fan-out/fan-in, cycle detection, and linear fallback.
inputs:
    - SPEC.md with dag metadata
    - PipelineEngine
outputs:
    - DAGExecutor with ThreadPoolExecutor parallel dispatch
    - DAGValidator with Kahn cycle detection
    - LinearPipelineAdapter for backward compatibility
acceptance_criteria:
    - DAG mode executes independent steps in parallel
    - Cycle detection raises DAGSpecificationError
    - Fan-in steps wait for all dependencies
    - Linear fallback works when mode is linear
    - All unit tests pass
non_goals:
    - Dynamic DAG construction at runtime
    - Distributed execution
---

# Contexto

The current `SynapseStateMachine` enforces a strictly linear state flow. Every pipeline step executes sequentially. This becomes a bottleneck when multiple independent steps could run in parallel, when fan-out/fan-in patterns are needed, or when conditional routing is required. Synapse-Flow, as the proprietary pipeline engine of SynapseOS, needs to evolve from a linear executor to a DAG-aware executor while maintaining backward compatibility.

# Objetivo

Introduce a DAG mode that coexists with the existing linear mode. When a SPEC contains DAG metadata, the `PipelineEngine` switches to a `DAGExecutor` that resolves step dependencies and schedules work in parallel. When no DAG metadata is present, the system behaves exactly as before.

## 1. Problem Statement

The linear pipeline model limits throughput on multi-core hosts and cannot express conditional or data-flow-driven execution graphs. The system needs to support:

1. **Parallel execution** of independent steps.
2. **Fan-out** — one step triggers multiple downstream steps.
3. **Fan-in** — a step waits for multiple upstream steps before executing.
4. **Conditional routing** — step execution depends on runtime state or output.
5. **No cycles** — DAG must be acyclic (validated at startup).

All while keeping the existing linear pipeline as the default mode for simple features.

## 2. Decision

We introduce a **DAG mode** that coexists with the existing linear mode. When a SPEC contains DAG metadata, the `PipelineEngine` switches to a `DAGExecutor` that resolves step dependencies and schedules work accordingly. When no DAG metadata is present, the system behaves exactly as before (linear, sequential).

The DAG metadata lives in the SPEC front matter under a `dag` key:

```yaml
---
dag:
    mode: dag # "linear" (default) or "dag"
    steps:
        - id: build_core
          executor: codex
          depends_on: []
        - id: build_tests
          executor: codex
          depends_on: [build_core]
        - id: build_integration
          executor: codex
          depends_on: [build_core]
        - id: verify
          executor: codex
          depends_on: [build_tests, build_integration]
    conditionals:
        - id: check_api
          step: validate_api
          if: runtime.api_present == true
---
# Normal SPEC body follows...
```

The `DAGExecutor`:

1. Builds an adjacency list from `depends_on` declarations.
2. Validates the graph has no cycles (Kahn's algorithm or DFS).
3. Computes ready set (steps with all dependencies satisfied).
4. Schedules ready steps (parallel execution within thread-pool limit).
5. Marks completed steps, refreshes ready set, repeats until all done or one fails.
6. Supports fan-in synchronization (wait for all dependencies before next step starts).
7. Falls back to linear order when `mode: linear` or no `dag` key present.

## 3. Scope

### 3.1 In Scope

- `DAGValidator`: validates DAG structure (no cycles, referenced steps exist, no orphan steps).
- `DAGExecutor`: adjacency-list graph, Kahn topological sort, thread-pool-based parallel dispatch.
- `DAGContext`: tracks step state (PENDING / RUNNING / DONE / FAILED) per step ID.
- Fan-out: one step can appear in `depends_on` of multiple downstream steps.
- Fan-in: a step with multiple `depends_on` entries waits for all of them.
- Backward compatibility: `mode: linear` or absent `dag` key → existing linear behavior.
- `DAGSpecificationError` — raised on invalid DAG metadata.
- Unit tests covering: cycle detection, topological sort, fan-out, fan-in, linear fallback.
- `LinearPipelineAdapter` — wraps existing linear flow so the same `PipelineEngine` can call either mode.

### 3.2 Out of Scope

- Dynamic DAG construction at runtime (steps added based on output of prior steps) — this is a future Phase 3 item.
- Distributed DAG execution across machines.
- DAG visualization or rendering.
- Persistence of DAG intermediate state — linear pipeline persistence model is reused.
- Automatic DAG generation from SPEC content.

## 4. Architecture

```
PipelineEngine
  ├── LinearPipelineAdapter  (mode: linear or no dag key)
  │   └── executes LINEAR_STATE_FLOW sequentially
  └── DAGExecutor            (mode: dag)
        ├── DAGValidator     (cycle check, orphan check, dependency check)
        ├── DAGContext       (step state tracker)
        └── ThreadPoolExecutor (concurrent step dispatch)
```

### Key Classes

| Class                   | Responsibility                                                                   |
| ----------------------- | -------------------------------------------------------------------------------- |
| `DAGSpec`               | Pydantic model for `dag` section in SPEC front matter                            |
| `DAGStep`               | Pydantic model for individual DAG step (id, executor, depends_on, if)            |
| `DAGConditional`        | Pydantic model for conditional step routing                                      |
| `DAGValidator`          | Validates DAG (cycle via Kahn, orphan steps, missing deps)                       |
| `DAGContext`            | Tracks per-step state: PENDING/RUNNING/DONE/FAILED                               |
| `DAGExecutor`           | Builds adjacency list, computes in-degree, dispatches ready steps to thread pool |
| `LinearPipelineAdapter` | Wraps existing linear flow as a drop-in executor interface                       |

### Files to Create

- `src/synapse_os/pipeline_dag.py` — all DAG classes and executor
- `tests/unit/test_pipeline_dag.py` — unit tests

### Files to Modify

- `src/synapse_os/pipeline.py` — detect DAG mode, route to DAGExecutor, add `dag` field to `PipelineContext`
- `src/synapse_os/specs/validator.py` — accept and parse `dag` key in SPEC front matter
- `tests/unit/test_pipeline.py` — add DAG mode integration tests (can be minimal)

## 5. Acceptance Criteria

| #   | Criterion                                                                                                                                             |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | A SPEC with `dag: mode: linear` or no `dag` key executes exactly as before (linear, sequential)                                                       |
| 2   | A SPEC with `dag: mode: dag` and valid `depends_on` graph executes with fan-out parallelism                                                           |
| 3   | A step with multiple `depends_on` entries starts only after all dependencies are DONE                                                                 |
| 4   | `DAGValidator` raises `DAGSpecificationError` on cycle detection                                                                                      |
| 5   | `DAGValidator` raises `DAGSpecificationError` when a `depends_on` references a non-existent step ID                                                   |
| 6   | `DAGValidator` raises `DAGSpecificationError` when a step has no `depends_on` but is referenced by no other step (orphan), unless it is the root step |
| 7   | ThreadPoolExecutor dispatches up to N steps concurrently (N = `settings.max_workers`, default 4)                                                      |
| 8   | When any step fails, the DAGExecutor records FAILED state and stops scheduling new steps                                                              |
| 9   | Fan-in synchronization: a step waits for all its `depends_on` to complete, not just one                                                               |
| 10  | All new unit tests pass; existing linear pipeline tests continue to pass                                                                              |

## 6. Dependencies

No new runtime dependencies. ThreadPoolExecutor is stdlib.

## 7. Configuration

`AppSettings` gains one new field:

```python
max_workers: int = Field(default=4, description="Max concurrent DAG step executions")
```

## 8. Edge Cases

| Case                                                             | Expected Behavior                                                               |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Empty `depends_on: []` list                                      | Step is a root; eligible for first batch of execution                           |
| Single-step DAG                                                  | Behaves like linear (no parallelism gain)                                       |
| DAG with 10 root steps and max_workers=4                         | Executes 4 in first batch, then remaining 6 (or fewer, depending on completion) |
| Step depends on another step in the same `depends_on` list twice | Ignored (deduplicated)                                                          |
| `dag` key present but `steps` list is empty                      | Raises `DAGSpecificationError`                                                  |

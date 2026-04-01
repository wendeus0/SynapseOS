---
id: F62-copilot-adapter
type: feature
summary: GitHub Copilot CLI adapter following BaseCLIAdapter pattern with circuit breaker and error classification.
inputs:
    - BaseCLIAdapter interface
    - gh CLI available on PATH
outputs:
    - CopilotCLIAdapter class
    - classify_copilot_execution function
    - Unit tests
acceptance_criteria:
    - CopilotCLIAdapter inherits from BaseCLIAdapter
    - adapter.capabilities includes code_generation
    - classify_copilot_execution returns correct categories
    - Circuit breaker integration works
    - All unit tests pass
non_goals:
    - Interactive shell mode
    - Bash completion
---

# Contexto

The SynapseOS adapter system (`BaseCLIAdapter` in `adapters.py`) currently supports two CLI-based AI runtimes: `CodexCLIAdapter` and `GeminiCLIAdapter`. The architecture supports arbitrary adapters via `BaseCLIAdapter`. GitHub Copilot CLI (`gh copilot`) is a widely-used AI coding assistant that complements Codex and Gemini.

# Objetivo

Create a `CopilotCLIAdapter` following the existing adapter pattern, expanding the routing options available to the `CapabilityRouter`.

## 1. Decision

Create a `CopilotCLIAdapter` following the existing adapter pattern. The adapter:

1. Calls `gh copilot ai` as the primary command
2. Returns a `CLIExecutionResult` with appropriate `success` flag
3. Classifies execution outcomes using `classify_copilot_execution`
4. Inherits circuit breaker and semaphore guard behavior
5. Has `capabilities = ("cli_execution", "code_generation")` matching Codex

### Authentication

Não há env var dedicada do SynapseOS para o adapter. A autenticação depende do estado já configurado no `gh` CLI.

## 2. Scope

### In Scope

- `CopilotCLIAdapter` class following `BaseCLIAdapter` pattern
- `classify_copilot_execution()` function (mirrors `classify_codex_execution`)
- Error classification: timeout, non-zero exit, authentication failure, unavailable
- Integration with `AdapterCircuitBreakerStore`
- Unit tests in `tests/unit/test_copilot_adapter.py`

### Out of Scope

- Changing the `gh copilot` binary location (uses `gh` from PATH)
- Supporting interactive `gh copilot` shell mode
- Bash completion or streaming output

## 3. Files

- `src/synapse_os/adapters.py` — add `CopilotCLIAdapter` and `classify_copilot_execution`
- `tests/unit/test_copilot_adapter.py` — unit tests (mock `gh copilot`)

## 4. Acceptance Criteria

| #   | Criterion                                                                                                |
| --- | -------------------------------------------------------------------------------------------------------- |
| 1   | `CopilotCLIAdapter` inherits from `BaseCLIAdapter`                                                       |
| 2   | `adapter.capabilities == ("cli_execution", "code_generation")`                                           |
| 3   | `classify_copilot_execution` returns correct category for: success, timeout, non-zero exit, auth failure |
| 4   | Adapter uses circuit breaker (same as `CodexCLIAdapter`)                                                 |
| 5   | All unit tests pass; existing adapter tests continue to pass                                             |
| 6   | `gh copilot` invoked with `--color never` to suppress ANSI                                               |

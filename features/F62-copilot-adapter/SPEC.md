---
feature_id: F62
title: Additional CLI Adapter — Copilot
status: draft
created: 2026-03-31
owner: agent
tags: [adapter, cli, copilot, github]
---

# F62 — Additional CLI Adapter: Copilot

## 1. Context

The SynapseOS adapter system (`BaseCLIAdapter` in `adapters.py`) currently supports two CLI-based AI runtimes: `CodexCLIAdapter` (Anthropic Claude Code via Docker) and `GeminiCLIAdapter` (Google Gemini). The architecture supports arbitrary adapters via `BaseCLIAdapter`.

GitHub Copilot CLI (`gh copilot`) is a widely-used AI coding assistant that complements Codex and Gemini with unique strengths. Adding a `CopilotCLIAdapter` expands the routing options available to the `CapabilityRouter`.

## 2. Decision

Create a `CopilotCLIAdapter` following the existing adapter pattern. The adapter:

1. Calls `gh copilot ai` (or `gh copilot`) as the primary command
2. Returns a `CLIExecutionResult` with appropriate `success` flag
3. Classifies execution outcomes using `classify_copilot_execution`
4. Inherits circuit breaker and semaphore guard behavior from `CodexCLIAdapter`
5. Has `capabilities = ("cli_execution", "code_generation")` matching Codex

### Environment Variable

`SYNAPSE_OS_GH_TOKEN` — GitHub CLI token. Required for authentication. If absent, adapter returns `authentication_unavailable`.

## 3. Scope

### In Scope

- `CopilotCLIAdapter` class following `BaseCLIAdapter` pattern
- `classify_copilot_execution()` function (mirrors `classify_codex_execution`)
- Error classification: timeout, non-zero exit, authentication failure, unavailable
- Integration with `AdapterCircuitBreakerStore`
- Unit tests in `tests/unit/test_copilot_adapter.py`
- Adapter registered in `multi_agent.py` `AdapterRegistry` (via existing pattern)

### Out of Scope

- Changing the `gh copilot` binary location (uses `gh` from PATH)
- Supporting interactive `gh copilot` shell mode
- Bash completion or streaming output

## 4. Files

- `src/synapse_os/adapters.py` — add `CopilotCLIAdapter` and `classify_copilot_execution`
- `tests/unit/test_copilot_adapter.py` — unit tests (mock `gh copilot`)

## 5. Acceptance Criteria

| #   | Criterion                                                                                                |
| --- | -------------------------------------------------------------------------------------------------------- |
| 1   | `CopilotCLIAdapter` inherits from `BaseCLIAdapter`                                                       |
| 2   | `adapter.capabilities == ("cli_execution", "code_generation")`                                           |
| 3   | `classify_copilot_execution` returns correct category for: success, timeout, non-zero exit, auth failure |
| 4   | Adapter uses circuit breaker (same as `CodexCLIAdapter`)                                                 |
| 5   | All unit tests pass; existing adapter tests continue to pass                                             |
| 6   | `gh copilot` invoked with `--color never` to suppress ANSI                                               |

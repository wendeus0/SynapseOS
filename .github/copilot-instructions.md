# Copilot Instructions for `aignt-os`

## Read first

Before making non-trivial changes, read these in order:

1. `CONTEXT.md`
2. `docs/architecture/SDD.md`
3. `docs/architecture/TDD.md`
4. `docs/architecture/SPEC_FORMAT.md`
5. `features/<current-feature>/SPEC.md` if the task is feature-specific

If they conflict, treat the feature `SPEC.md` as the source of truth for that feature, then `SDD.md` for architecture, `TDD.md` for implementation/testing strategy, and `SPEC_FORMAT.md` for SPEC structure.

## Idioma das respostas

O idioma padrão e obrigatório das respostas ao utilizador neste repositório é português.

Responda sempre em português em toda interação com o utilizador.

Só responda em outro idioma se o utilizador pedir isso de forma explícita.

## Build, test, lint, and validation commands

Prefer the repo scripts over ad hoc commands.

### Preferred full local validation flow

Use this as the standard local entrypoint when you need the repository checks:

```bash
./scripts/commit-check.sh --sync-dev
```

This bootstraps the dev environment with `uv sync --locked --extra dev` and then runs:

```bash
uv run ruff format --check .
uv run ruff check .
uv run python -m mypy
uv run python -m pytest
```

For a fast rerun after the environment is already synced:

```bash
./scripts/commit-check.sh --no-sync
```

### Individual checks

After bootstrap, use the same `uv`-based execution style the repo scripts use:

```bash
uv run --no-sync ruff format --check .
uv run --no-sync ruff check .
uv run --no-sync python -m mypy
uv run --no-sync python -m pytest
```

Use `python -m pytest` and `python -m mypy`, not bare `pytest`/`mypy`, because the repo explicitly hardened around broken virtualenv wrapper issues.

### Running a single test

Run one file:

```bash
uv run --no-sync python -m pytest tests/unit/test_state_machine.py
```

Run one test:

```bash
uv run --no-sync python -m pytest tests/unit/test_state_machine.py::test_state_machine_follows_minimal_happy_path_to_complete
```

### Docker and runtime validation

The repo distinguishes lightweight repository checks from operational Docker preflight:

```bash
./scripts/docker-preflight.sh
./scripts/docker-preflight.sh --full-runtime
```

- Default `docker-preflight` is intentionally light: `docker compose config` plus build, without bringing the full runtime up.
- Use `--full-runtime` only for changes that affect boot, lifecycle, persistence, integration, or container runtime behavior.

### Git hook behavior

The local pre-commit hook runs:

```bash
./scripts/commit-check.sh --hook-mode
```

That is only a lightweight repo check. It does **not** replace the operational `DOCKER_PREFLIGHT`.

## High-level architecture

AIgnt OS is a CLI-first meta-orchestrator for external AI tools. The intended system is centered on **AIgnt-Synapse-Flow**, the repository's own pipeline engine, which is state-driven and spec-first.

There are two related flows to keep straight:

1. The **official feature workflow** used by humans/agents working in the repo:

```text
DOCKER_PREFLIGHT → SPEC → TEST_RED → CODE_GREEN → REFACTOR → SECURITY_REVIEW → REPORT → COMMIT
```

2. The **internal runtime state flow** described in the architecture docs and partially implemented in code:

```text
REQUEST → SPEC_DISCOVERY → SPEC_NORMALIZATION → SPEC_VALIDATION → PLAN → TEST_RED → CODE_GREEN → REVIEW → SECURITY → DOCUMENT → COMPLETE
```

### What is implemented today

The docs describe a larger target system, but the current codebase is still in foundational MVP slices. The implemented modules are concentrated in:

- `src/aignt_os/cli/app.py` for the Typer CLI
- `src/aignt_os/runtime/` for the minimal persistent runtime lifecycle and runtime state file handling
- `src/aignt_os/specs/validator.py` for SPEC validation
- `src/aignt_os/state_machine.py` for the linear state machine
- `src/aignt_os/contracts.py` and `src/aignt_os/config.py` for base contracts and settings

Directories such as `adapters/`, `orchestrator/`, `pipeline/`, `memory/`, `db/`, `observability/`, and `supervisor/` reflect the planned architecture, but future sessions should verify concrete implementation before assuming those subsystems exist.

### Current runtime slice

The current runtime is a minimal dual-mode foundation:

- The CLI exposes `aignt version` and `aignt runtime {start,status,run,ready,stop}`.
- `RuntimeService` manages a resident process and persists runtime state to a JSON file.
- `RuntimeStateStore` treats missing state as `stopped` and corrupted or mismatched persisted state as `inconsistent`.
- Integration tests around `runtime` and unit tests around runtime state/security are the main executable proof of current runtime behavior.

### SPEC and contracts

The repo is explicitly spec-first:

- SPECs are Markdown documents with required YAML front matter.
- The validator requires at least the metadata fields `id`, `type`, `summary`, `inputs`, `outputs`, `acceptance_criteria`, and `non_goals`.
- The body must contain the sections `Contexto` and `Objetivo`.
- The state machine blocks moving past `SPEC_VALIDATION` until the flow stays in order.

### Testing layout

Current test coverage is organized as:

- `tests/unit/` for config, contracts, SPEC validation, runtime state/security, state machine, and repo automation scripts
- `tests/integration/` for CLI bootstrap and runtime CLI behavior
- `tests/fixtures/specs/` for SPEC fixtures

`tests/pipeline/` exists as part of the intended architecture, but current coverage is mostly unit and integration tests.

## Key repo-specific conventions

### Work feature-by-feature

This repo is organized around one feature at a time. Do not mix scopes across multiple features or worktrees in one change. If a task is feature-specific, inspect `features/<feature>/SPEC.md` first and keep the change inside that feature's intended scope.

### Treat docs as architecture, but code as the implementation truth

The architecture docs are important and should guide naming and design, but the repository currently implements only part of that target system. Always verify whether a module is real code or just a placeholder directory before wiring against it.

### Use the official terminology

When referring to the internal runtime flow, use **AIgnt-Synapse-Flow** and make clear at least once that it is the repository's own pipeline engine.

Keep these terms stable:

- `SPEC` = the formal feature specification
- `run` = one pipeline execution
- `worker` or runtime = the resident long-lived mode of the dual runtime

### Respect the repo's validation flow

The repo expects this order:

1. `DOCKER_PREFLIGHT`
2. SPEC work
3. failing tests (`TEST_RED`)
4. minimal implementation (`CODE_GREEN`)
5. refactor
6. security gate
7. report/commit

Do not treat a green local hook as equivalent to the operational preflight.

### Follow the repo's Python execution style

Use `uv`-managed commands and prefer the repository scripts. When running tools directly, follow the same pattern as `commit-check.sh`:

- `uv run --no-sync python -m pytest`
- `uv run --no-sync python -m mypy`

That convention exists because wrapper binaries in `.venv` have been unreliable in this repo.

### Keep SPEC handling strict

Do not invent looser SPEC formats. The validator is intentionally strict:

- YAML front matter is mandatory
- `acceptance_criteria` must be non-empty
- `non_goals` must exist
- `Contexto` and `Objetivo` sections are required

If a change affects SPEC handling, update tests and validator behavior together.

### Preserve explicit contracts

Current contracts are intentionally small and strict. For example, `CLIExecutionResult` keeps `stdout_raw` and `stdout_clean` separate. Preserve that distinction rather than collapsing raw and sanitized output into one field.

### Respect branch sync checks

On non-`main` branches, the repo expects drift checks against `origin/main` before substantial work and before commit/PR steps. Use:

```bash
./scripts/branch-sync-check.sh
```

Use `./scripts/branch-sync-update.sh` only as the conservative helper described in `AGENTS.md`, not as an automatic fix for every branch state.

### Treat runtime consistency checks as part of behavior, not just plumbing

The runtime layer explicitly distinguishes `running`, `stopped`, and `inconsistent` states, and validates persisted process identity against `/proc`. Changes to runtime behavior should preserve those safety checks and keep the CLI/runtime tests aligned.

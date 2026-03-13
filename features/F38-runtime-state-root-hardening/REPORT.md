# F38 Report

## Resumo executivo

- A `F38-runtime-state-root-hardening` endurece o diretório de estado compartilhado de runtime, auth registry e circuit breaker contra escapes do `workspace_root`.
- O boundary passa a ser aplicado em `AppSettings`, preservando o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS sem abrir nova superficie publica.
- O recorte permaneceu não conflitante com a frente da TUI: sem tocar dashboard, watch mode, socket, IPC ou transporte remoto.

## Escopo alterado

- `AppSettings` passa a resolver `runtime_state_dir` por canonicalizacao dentro de `workspace_root`
- `runtime_state_file`, `auth_registry_file` e `adapter_circuit_breaker_state_file` passam a herdar o mesmo boundary confiável
- `runtime`, `auth` e fluxos que dependem desses arquivos agora retornam erro de ambiente previsivel quando o state-dir configurado escapa da raiz confiável
- fixtures e integrações que usam `tmp_path` passam a declarar `AIGNT_OS_WORKSPACE_ROOT` explicitamente quando necessário
- `tests/integration/test_runs_submit_cli.py` foi alinhado para usar o mesmo `runtime_state_dir` do ambiente sob teste
- `SPEC.md`, `NOTES.md`, `CHECKLIST.md` e este `REPORT.md` adicionados para a `F38`

## Validacoes executadas

- `validate_spec_file(Path("features/F38-runtime-state-root-hardening/SPEC.md"))`
- `env PYTHONPATH=/tmp/aignt-os-worktrees/F38-runtime-state-root-hardening/src /tmp/aignt-os-worktrees/F38-runtime-state-root-hardening/.venv/bin/python -m pytest tests/unit/test_config.py tests/integration/test_runtime_cli.py tests/integration/test_cli_auth_registry.py tests/unit/test_cli_adapter.py tests/integration/test_doctor_cli.py tests/integration/test_cli_error_model.py tests/integration/test_worker_runtime_flow.py tests/integration/test_codex_adapter_operational.py -q`
- `env PYTHONPATH=/tmp/aignt-os-worktrees/F38-runtime-state-root-hardening/src /tmp/aignt-os-worktrees/F38-runtime-state-root-hardening/.venv/bin/python -m pytest tests/integration/test_runs_submit_cli.py -q`
- `env PYTHONPATH=/tmp/aignt-os-worktrees/F38-runtime-state-root-hardening/src /tmp/aignt-os-worktrees/F38-runtime-state-root-hardening/.venv/bin/python -m ruff check src/aignt_os/config.py src/aignt_os/cli/app.py tests/unit/test_config.py tests/unit/test_cli_adapter.py tests/integration/conftest.py tests/integration/test_runtime_cli.py tests/integration/test_cli_auth_registry.py tests/integration/test_cli_error_model.py tests/integration/test_doctor_cli.py tests/integration/test_worker_runtime_flow.py tests/integration/test_codex_adapter_operational.py tests/integration/test_runs_submit_cli.py`
- `env PYTHONPATH=/tmp/aignt-os-worktrees/F38-runtime-state-root-hardening/src /tmp/aignt-os-worktrees/F38-runtime-state-root-hardening/.venv/bin/python -m mypy src/aignt_os/config.py src/aignt_os/cli/app.py`
- `env UV_CACHE_DIR=/tmp/aignt-os-worktrees/F38-runtime-state-root-hardening/.cache/uv ./scripts/commit-check.sh --no-sync --skip-branch-validation --skip-docker --skip-security`
- `./scripts/security-gate.sh`

## Review de seguranca

- Parecer final: aprovado.
- Riscos revisados:
  - `runtime_state_dir` absoluto ou symlinkado escapar do `workspace_root` e contaminar o estado compartilhado
  - `auth init` e `runtime start` vazarem traceback em vez de erro configuracional previsivel
  - regressao incidental em integrações que dependem de `tmp_path` como raiz confiável
- Mitigacoes aplicadas:
  - a canonicalizacao de `runtime_state_dir` reutiliza `resolve_path_within_root`, bloqueando escapes absolutos e por symlink
  - a CLI converte `ValueError` de configuração em `environment_error(...)` nos pontos que acessam runtime state e auth registry
  - a suite de integração foi ajustada para declarar `AIGNT_OS_WORKSPACE_ROOT` de forma explícita onde o root confiável diverge do cwd do teste

## Riscos residuais

- `runs_db_path` e `artifacts_dir` permanecem fora do escopo desta frente e continuam com seus contratos atuais.
- A proteção depende de `workspace_root` coerente no ambiente; configurações inconsistentes agora falham cedo, mas a escolha desse root continua responsabilidade operacional do chamador.

## Proximos passos

- Se houver novo hardening não conflitante com a TUI, o próximo slice natural é revisar se `runs_db_path` merece boundary equivalente ou se isso deve continuar fora do MVP.
- Fora disso, a fila imediata pode sair de auth/runtime local e migrar para outro bucket isolado sem reabrir `G-11`.

## Status final da frente

- `READY_FOR_COMMIT`

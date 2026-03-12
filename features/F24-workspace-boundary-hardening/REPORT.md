# F24 Report

## Resumo executivo

- A F24 foi implementada como o endurecimento de boundary de workspace e artifacts publicos da IDEA-001.
- O recorte ficou fechado em `G-05 + G-10` sem ampliar para migration, auth, Docker ou AST scanning.
- A superficie publica da CLI foi preservada: `runs submit` e `runs show` mantiveram os mesmos comandos, mas agora rejeitam paths fora das roots confiaveis com boundary previsivel de `Not found`.

## Escopo entregue

- `AppSettings.workspace_root` com default em `Path.cwd()` e override por ambiente.
- Helper compartilhado em `src/aignt_os/security.py` para canonicalizar paths dentro de uma root confiavel.
- `RunDispatchService` endurecido para aceitar SPEC apenas dentro de `workspace_root` e persistir `spec_path` canonicalizado.
- `ArtifactStore.list_artifact_paths()` filtrando artifacts/symlinks cujo destino resolvido escape `artifacts_dir`.
- Preview publico endurecido para bloquear `clean_output_path` e report paths fora de `artifacts_dir`, inclusive quando vierem do banco.
- Cobertura unitaria e de integracao para submit valido, SPEC fora da root, symlink de escape, preview bloqueado e listagem filtrada.

## Validacoes executadas

- Leitura e alinhamento com `CONTEXT.md`, `docs/architecture/SDD.md`, `docs/architecture/TDD.md` e `docs/architecture/SPEC_FORMAT.md`.
- Validacao da SPEC com `validate_spec_file(Path('features/F24-workspace-boundary-hardening/SPEC.md'))`.
- `uv run --no-sync python -m pytest tests/unit/test_security.py tests/unit/test_config.py tests/unit/test_runtime_dispatch.py tests/integration/test_runs_submit_cli.py tests/integration/test_public_onboarding_flow.py tests/integration/test_worker_runtime_flow.py tests/integration/test_cli_error_model.py tests/integration/test_runs_cli.py -q`
- `uv run --no-sync ruff check src/aignt_os/security.py src/aignt_os/config.py src/aignt_os/runtime/dispatch.py src/aignt_os/persistence.py src/aignt_os/cli/app.py tests/unit/test_security.py tests/unit/test_config.py tests/unit/test_runtime_dispatch.py tests/integration/test_runs_submit_cli.py tests/integration/test_public_onboarding_flow.py tests/integration/test_worker_runtime_flow.py tests/integration/test_cli_error_model.py tests/integration/test_runs_cli.py`
- `uv run --no-sync mypy src/aignt_os/security.py src/aignt_os/config.py src/aignt_os/runtime/dispatch.py src/aignt_os/persistence.py src/aignt_os/cli/app.py`
- `./scripts/security-gate.sh`

## Security review

- O boundary de seguranca foi mantido sem disclosure de host: SPEC fora da root confiavel e artifacts fora de `artifacts_dir` sao tratados como indisponiveis.
- O review local de correcao/seguranca nao deixou findings bloqueantes abertos apos o hardening do dispatch e do default dinamico de `workspace_root`.
- O contrato de F23 permanece intacto: `raw.txt` segue privado e fora do preview publico.

## Riscos residuais

- A F24 nao retroage runs antigas ja persistidas; ela endurece a leitura/listagem publica no estado atual da CLI.
- O root confiavel do workspace no MVP depende de configuracao correta de `AIGNT_OS_WORKSPACE_ROOT` quando o operador quiser trabalhar fora de `Path.cwd()`.
- Integridade por hash da SPEC, audit trail e autenticacao continuam em features posteriores da IDEA-001.

## Proximos passos

- Executar o fluxo Git da F24 ate PR aberta com pedido de aprovacao para merge.

## Status final da frente

- `READY_FOR_REVIEW`

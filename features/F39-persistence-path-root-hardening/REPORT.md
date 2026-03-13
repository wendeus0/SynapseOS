# F39 Report

## Resumo executivo

- A `F39-persistence-path-root-hardening` endurece `runs_db_path` e `artifacts_dir` contra escapes do `workspace_root`.
- O boundary passa a ser aplicado em `AppSettings` e consumido pelos entrypoints de CLI, worker e dashboard, preservando o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS.
- O recorte permaneceu pequeno e independente da frente visual: sem alterar watch mode como produto, sem migracao de schema e sem tocar auth remota.

## Escopo alterado

- `AppSettings` passa a expor `runs_db_path_resolved` e `artifacts_dir_resolved`
- `cli/app.py`, `runtime/worker.py` e `cli/dashboard.py` passam a consumir apenas os paths resolvidos
- `doctor` passa a reprovar explicitamente configuracao de persistencia fora do `workspace_root`
- fixtures de integracao de runs foram alinhadas para usar persistencia dentro do root confiavel
- `SPEC.md`, `NOTES.md`, `CHECKLIST.md` e este `REPORT.md` foram adicionados para a `F39`

## Validacoes executadas

- `validate_spec_file(Path("features/F39-persistence-path-root-hardening/SPEC.md"))`
- `pytest tests/unit/test_config.py tests/integration/test_runs_submit_cli.py tests/integration/test_runs_cli.py tests/integration/test_doctor_cli.py -q`
- `ruff check src/aignt_os/config.py src/aignt_os/cli/app.py src/aignt_os/runtime/worker.py src/aignt_os/cli/dashboard.py tests/unit/test_config.py tests/integration/test_runs_submit_cli.py tests/integration/test_runs_cli.py tests/integration/test_doctor_cli.py`
- `mypy src/aignt_os/config.py src/aignt_os/cli/app.py src/aignt_os/runtime/worker.py src/aignt_os/cli/dashboard.py`
- `./scripts/commit-check.sh --no-sync --skip-branch-validation --skip-docker --skip-security`
- `./scripts/security-gate.sh`

## Review de seguranca

- Parecer final: aprovado.
- Riscos revisados:
  - banco SQLite configurado fora do `workspace_root`
  - diretório de artifacts escapando por path absoluto ou por symlink
  - CLIs de runs e doctor emitindo traceback cru para erro configuracional
- Mitigacoes aplicadas:
  - canonicalizacao de `runs_db_path` e `artifacts_dir` com `resolve_path_within_root`
  - tradução consistente de `ValueError` em `Environment error:` nos entrypoints de CLI
  - integração ajustada para declarar `AIGNT_OS_WORKSPACE_ROOT` coerente com os paths persistidos

## Riscos residuais

- O boundary depende de `workspace_root` coerente no ambiente; configuracoes divergentes agora falham cedo, mas a escolha do root continua responsabilidade operacional do chamador.
- O diretório de artifacts ainda pode conter arquivos problemáticos ja persistidos anteriormente; esta frente endurece a configuracao de entrada, nao saneia retroativamente dados legados.

## Proximos passos

- Se houver novo hardening pequeno fora da TUI, o proximo slice natural e revisar outros boundaries configuraveis ainda brutos.
- Fora isso, a fila independente pode voltar para backlog funcional apos absorver esta protecao de persistencia.

## Status final da frente

- `READY_FOR_COMMIT`

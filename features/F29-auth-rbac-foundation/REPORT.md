# F29 Report

## Resumo executivo

- A F29 introduziu uma fundacao local e opt-in de autenticacao com RBAC para a CLI do AIgnt OS.
- O recorte ficou deliberadamente limitado ao baseline atual: `runs submit` e `runtime start|run|stop` agora podem exigir token, enquanto a leitura local continua aberta.
- O AIgnt-Synapse-Flow permanece a engine propria de pipeline do AIgnt OS; a frente reaproveitou `initiated_by` e o contrato publico de erro da CLI sem abrir socket, auth remota ou gerenciamento completo de credenciais.

## Escopo entregue

- Novo modulo `src/aignt_os/auth.py` com:
  - registry privado em JSON com escrita atomica
  - principals e tokens por hash SHA-256
  - verificacao de permissao por papel (`viewer`, `operator`)
- `AppSettings` estendido com `auth_enabled` e `auth_registry_file`.
- `src/aignt_os/cli/errors.py` ampliado com exit codes `7` e `8` para authn/authz.
- `src/aignt_os/cli/app.py` endurecido para:
  - exigir token apenas em comandos mutaveis quando auth estiver habilitada
  - aceitar `--auth-token` com fallback em `AIGNT_OS_AUTH_TOKEN`
  - persistir `principal_id` autenticado em `initiated_by` no submit bem-sucedido
- Cobertura unitaria e de integracao para registry, baseline sem auth, falha de autenticacao, falha de autorizacao, fail-closed por registry ausente e provenance autenticada.

## Validacoes executadas

- Validacao da SPEC com `validate_spec_file(Path('features/F29-auth-rbac-foundation/SPEC.md'))`.
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync python -m pytest tests/unit/test_config.py tests/unit/test_auth.py tests/integration/test_cli_auth_rbac.py tests/integration/test_runs_submit_cli.py tests/integration/test_runtime_cli.py tests/integration/test_cli_error_model.py -q`
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync ruff check src/aignt_os/auth.py src/aignt_os/config.py src/aignt_os/cli/errors.py src/aignt_os/cli/app.py tests/unit/test_config.py tests/unit/test_auth.py tests/integration/test_cli_auth_rbac.py`
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync python -m mypy src/aignt_os/auth.py src/aignt_os/config.py src/aignt_os/cli/errors.py src/aignt_os/cli/app.py`

## Security review

- Parecer final: aprovado.
- Riscos revisados:
  - persistencia de token em claro
  - permissao fraca em arquivo de credenciais
  - bypass de auth em `runtime run`
  - vazamento de detalhes sensiveis em mensagens de erro
- Mitigacoes aplicadas:
  - registry persiste apenas `token_sha256`
  - escrita atomica e permissoes privadas (`0600` arquivo / `0700` diretorio)
  - `runtime run` revalida auth e propaga token para o reexec por ambiente
  - mensagens diferenciam authn/authz sem imprimir token ou hash

## Riscos residuais

- O registry continua local ao workspace/host atual; nao ha revogacao dinamica nem coordenacao entre processos/hosts.
- A role `viewer` ainda nao governa um conjunto amplo de politicas porque a frente protege apenas comandos mutaveis do baseline.
- A configuracao do registry continua manual; ergonomia de provisionamento e rotacao ficam para frente futura propria.

## Proximos passos

- Rodar `branch-sync-guard` antes do commit/push final da branch.
- Fechar o fluxo Git da F29.
- Triar a proxima frente apos merge sem reabrir socket ou auth distribuida por inercia.

## Status final da frente

- `READY_FOR_COMMIT`

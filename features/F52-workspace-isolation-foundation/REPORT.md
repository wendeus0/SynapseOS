# F52 Report

## Resumo executivo

- A `F52-workspace-isolation-foundation` introduz a fundação de isolamento operacional de workspace por run sobre os contratos abertos na `F51`.
- O recorte ficou restrito a `workspace_path` auditável e a um provider `run-scoped`, sem abrir `git worktree` obrigatório nem alterar a CLI pública.
- A feature preserva o modo legado de workspace único quando o isolamento adicional não é solicitado.

## Escopo alterado

- [runtime_contracts.py](/home/g0dsssp33d/work/projects/SynapseOS/src/synapse_os/runtime_contracts.py) ganha `RunScopedWorkspaceProvider`
- [persistence.py](/home/g0dsssp33d/work/projects/SynapseOS/src/synapse_os/persistence.py) passa a persistir `workspace_path` na tabela `runs`
- `RunRepository` passa a aceitar `workspace_path` explícito e a atualizar schema legado com coluna nova
- `PersistedPipelineRunner` passa a resolver workspace por `run_id` quando `run_workspace_root` é fornecido
- o evento `run_started` passa a carregar `workspace` no texto para melhorar rastreabilidade local

## Validacoes executadas

- `validate_spec_file(Path("features/F52-workspace-isolation-foundation/SPEC.md"))`
- `env PYTHONPATH=src ./.venv-codex-runtime/bin/python -m pytest tests/unit/test_persistence.py tests/integration/test_pipeline_persistence.py tests/unit/test_runtime_dispatch.py -q`
- `env PYTHONPATH=src ./.venv-codex-runtime/bin/python -m ruff check src/synapse_os/runtime_contracts.py src/synapse_os/persistence.py tests/unit/test_persistence.py tests/integration/test_pipeline_persistence.py tests/unit/test_runtime_dispatch.py`
- `env PYTHONPATH=src ./.venv-codex-runtime/bin/python -m ruff format --check src/synapse_os/runtime_contracts.py src/synapse_os/persistence.py tests/unit/test_persistence.py tests/integration/test_pipeline_persistence.py tests/unit/test_runtime_dispatch.py`
- `env PYTHONPATH=src ./.venv-codex-runtime/bin/python -m mypy src/synapse_os/runtime_contracts.py src/synapse_os/persistence.py`

## Review de seguranca

- Parecer final: aprovado.
- Riscos revisados:
  - materializar diretórios fora da raiz confiável
  - quebrar compatibilidade de runs existentes por mudança de schema
  - introduzir isolamento mais ambicioso do que o MVP comporta
- Mitigações aplicadas:
  - o provider novo só cria diretórios previsíveis sob `run_workspace_root / <run_id>`
  - a coluna `workspace_path` entra com upgrade compatível para schema legado
  - o modo atual continua funcionando com fallback seguro para o diretório da SPEC

## Riscos residuais

- O isolamento entregue ainda não cria `git worktree`, cópia de árvore nem múltiplos workspaces por run.
- A materialização do workspace é operacional e auditável, mas ainda não altera a política de artifacts ou diff por run.

## Proximos passos

- Reaproveitar `workspace_path` e `RunContext` para enriquecer a timeline de eventos e o diagnóstico da run.
- Decidir depois, em frente própria, se `git worktree` realmente compensa como próximo grau de isolamento.

## Status final da frente

- `READY_FOR_COMMIT`

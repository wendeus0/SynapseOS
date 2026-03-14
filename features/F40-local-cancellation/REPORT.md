# F40 Report

## Resumo executivo

- A `F40-local-cancellation` adicionou cancelamento local de runs via CLI e dashboard TUI.
- A feature preservou o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS e nao abriu fila remota, scheduler nem cancelamento distribuido.

## Escopo alterado

- superficie publica com `aignt runs cancel <run_id>`
- atalho `k` no dashboard TUI para a run atualmente observada
- persistencia de sinalizacao de cancelamento para `pending` e `running`

## Validacoes executadas

- cobertura existente em `tests/integration/test_cli_cancellation.py`
- cobertura existente em `tests/unit/test_persistence_cancellation.py`

## Riscos residuais

- o recorte atual continua local e gracioso; nao ha interrupcao forcada nem coordenacao entre hosts
- cancelamento distribuido continua fora de escopo e exigiria SPEC propria

## Status final da frente

- `READY_FOR_COMMIT`

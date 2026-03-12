---
id: F15-public-run-submission
type: feature
summary: Expor submissao publica de runs pela CLI a partir de uma SPEC validada, reutilizando o dispatch e o runtime dual ja existentes.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - memory.md
  - PENDING_LOG.md
  - src/aignt_os/cli/app.py
  - src/aignt_os/runtime/dispatch.py
  - src/aignt_os/persistence.py
outputs:
  - runs_submit_cli_command
  - dispatch_validation_guardrails
  - runs_submit_tests
constraints:
  - manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS
  - manter a entrada publica restrita a um caminho de SPEC explicitamente informado
  - reutilizar `RunDispatchService`, `PersistedPipelineRunner`, `RunRepository` e `RuntimeService` ja existentes
  - nao introduzir nova service layer, nova fila ou mudanca em schema SQLite
  - nao exigir TUI, watch mode, preview de artifacts ou novo modelo global de erros fora do minimo desta frente
acceptance_criteria:
  - "`aignt runs submit <spec_path>` submete uma SPEC valida pela CLI publica e sempre retorna pelo menos `run_id`, `status` e `mode`."
  - "Quando `--mode sync` for usado, a run e concluida inline e o resultado reporta `status=completed` e `mode=sync`."
  - "Quando `--mode async` for usado, a run e enfileirada como pendente e o resultado reporta `status=queued` e `mode=async`."
  - "Quando `--mode auto` for usado, a CLI resolve para `async` se o runtime estiver pronto e para `sync` caso contrario."
  - "Existe pelo menos um teste de integracao cobrindo `runs submit` em modo `sync` e pelo menos um em `auto` ou `async`, contra persistencia real."
  - "SPEC ausente ou SPEC invalida falham de forma previsivel, sem traceback cru e sem persistir run invalida."
non_goals:
  - enriquecer `runs show`
  - definir o modelo global de exit codes da CLI
  - adicionar TUI, watch mode ou streaming
  - permitir submit a partir de prompt cru
security_notes:
  - validar o path e a SPEC antes de acionar o dispatch
  - nao introduzir subprocesso ou shell novo fora do contrato ja existente
  - manter mensagens operacionais sem vazar traceback cru
dependencies:
  - F08-worker-runtime-dual
  - F14-runs-observability-cli
---

# Contexto

O projeto ja possui runtime dual, persistencia de runs e um `RunDispatchService` interno capaz de resolver dispatch `sync` ou `async`, mantendo o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS. Porem, essa capacidade ainda nao esta exposta na CLI publica: hoje a superficie publica permite inspecionar runs, mas nao criar uma nova run a partir de uma SPEC.

A etapa 2 foi priorizada exatamente para fechar essa lacuna. A F15 deve abrir o caminho publico minimo de execucao sem criar nova engine ou novo modelo operacional.

# Objetivo

Entregar um comando publico `aignt runs submit <spec_path>` que valide a SPEC informada, resolva o modo de dispatch (`sync`, `async` ou `auto`) e retorne um contrato textual minimo, util para humanos e para captura em testes.

# Escopo

## Incluido

- comando publico `aignt runs submit <spec_path>`
- flags `--mode auto|sync|async` e `--stop-at <state>` com defaults operacionais seguros
- validacao previa de existencia e formato minimo da SPEC
- reutilizacao do `RunDispatchService` interno
- saida textual minima com `run_id`, `status` e `mode`
- testes unitarios do dispatch e testes de integracao do comando

## Fora de escopo

- submit por prompt cru
- preview de artifacts ou expansao de `runs show`
- modelo global de erros e exit codes alem do necessario para esta frente
- mudancas no schema de persistencia

# Requisitos funcionais

1. O comando `aignt runs submit <spec_path>` deve aceitar um path de SPEC e rejeitar caminhos ausentes.
2. Antes de despachar a run, a SPEC deve passar por validacao minima de formato.
3. O comando deve aceitar `--mode auto|sync|async`.
4. O comando deve aceitar `--stop-at <state>` para limitar a execucao ao estado suportado informado.
5. O default de `--mode` deve ser `auto`.
6. O default de `--stop-at` deve ser `SPEC_VALIDATION`, preservando um caminho publico funcional sem depender de executors ainda nao expostos.
7. O resultado deve sempre informar:
   - `run_id`
   - `status`
   - `mode`
8. Em `sync`, a run deve ser executada inline no mesmo processo.
9. Em `async`, a run deve ser persistida como pendente para consumo posterior pelo worker.
10. Em `auto`, a decisao deve usar a disponibilidade atual do runtime.

# Requisitos nao funcionais

- A saida precisa continuar legivel sem TTY e em captura de testes.
- A implementacao deve ficar concentrada na CLI e no dispatch ja existente.
- O contrato da F15 nao deve antecipar o modelo global da F21.

# Casos de erro

- path de SPEC ausente
- SPEC invalida
- `mode` invalido
- `stop_at` invalido
- falha interna de dispatch sem `run_id`

# Cenarios verificaveis

## Cenario 1: submit sincrono

- Dado uma SPEC valida
- Quando `aignt runs submit <spec_path> --mode sync --stop-at SPEC_VALIDATION` for executado
- Entao a CLI retorna `run_id`, `status=completed` e `mode=sync`
- E a run fica persistida com estado final coerente

## Cenario 2: submit assincrono

- Dado uma SPEC valida
- Quando `aignt runs submit <spec_path> --mode async --stop-at SPEC_VALIDATION` for executado
- Entao a CLI retorna `run_id`, `status=queued` e `mode=async`
- E a run fica persistida como pendente

## Cenario 3: modo auto

- Dado uma SPEC valida
- Quando `aignt runs submit <spec_path> --mode auto` for executado com runtime pronto
- Entao a CLI resolve o dispatch para `async`

- E quando o runtime nao estiver pronto
- Entao a CLI resolve o dispatch para `sync`

## Cenario 4: erro de input

- Dado um path inexistente ou uma SPEC invalida
- Quando `aignt runs submit <spec_path>` for executado
- Entao a CLI falha sem traceback cru
- E nenhuma run invalida e persistida

# Observacoes

Esta frente existe para expor a capacidade publica minima de submit antes de aprofundar detalhamento de runs, error model e onboarding. A definicao de exit codes estaveis e classificacao ampla de falhas fica para a `F21-cli-error-model-and-exit-codes`.

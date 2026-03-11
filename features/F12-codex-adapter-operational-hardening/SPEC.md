---
id: F12-codex-adapter-operational-hardening
type: feature
summary: Endurecer a validacao operacional do CodexCLIAdapter com smoke real container-first e tratamento previsivel de bloqueios operacionais.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - features/F10-run-report-one-real-adapter/SPEC.md
  - scripts/dev-codex.sh
outputs:
  - codex_adapter_smoke_path
  - codex_operational_validation
  - codex_hardening_tests
constraints:
  - manter o AIgnt-Synapse-Flow como engine propria de pipeline do AIgnt OS
  - manter o fluxo container-first via ./scripts/dev-codex.sh
  - nao adicionar nova CLI publica nem segundo adapter real
  - nao reabrir escopo de runtime distribuido, DAG ou multiplos workers
  - exigir DOCKER_PREFLIGHT antes da validacao pratica dependente de container
acceptance_criteria:
  - Existe um caminho de smoke operacional explicito para o `CodexCLIAdapter` usando `./scripts/dev-codex.sh -- exec`.
  - Existe pelo menos um teste de integracao cobrindo o caminho real do adapter com subprocesso e contrato de `CLIExecutionResult`.
  - Falhas previsiveis do caminho real do Codex sao classificadas de forma clara, incluindo timeout, return code nao zero e indisponibilidade operacional do launcher/container.
  - O recorte define quando `DOCKER_PREFLIGHT` e obrigatorio para a validacao pratica do adapter real.
  - O hardening nao adiciona nova CLI publica nem altera o fluxo oficial de feature.
non_goals:
  - adicionar segundo adapter real
  - redesenhar o `PipelineEngine`
  - introduzir roteamento automatico, DAG ou worker distribuido
  - transformar autenticacao do Codex em subsistema proprio
security_notes:
  - preservar execucao sem shell no adapter
  - tratar falhas de autenticacao, permissao e runtime como bloqueios operacionais explicitos
  - nao ampliar mounts ou privilegios do ambiente `codex-dev`
dependencies:
  - F10-run-report-one-real-adapter
  - F11-repo-automation
---

# Contexto

Com a F10 mergeada, o AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS, ja fecha o MVP com `DOCUMENT`, `RUN_REPORT.md` e o primeiro adapter real (`CodexCLIAdapter`). O gap remanescente nao esta mais no contrato do adapter nem na persistencia do relatorio, e sim na validacao operacional do caminho real do Codex via launcher container-first.

Hoje o repositório cobre a montagem do comando e o contrato do adapter majoritariamente com mocks e smoke parcial de launcher. Ainda falta um recorte pequeno e explícito que diga qual e o smoke real minimo do `CodexCLIAdapter`, como falhas operacionais devem aparecer e quando esse caminho precisa passar por `DOCKER_PREFLIGHT`.

# Objetivo

Entregar um hardening operacional pequeno e fechado para o primeiro adapter real:

- validar o caminho real do `CodexCLIAdapter` via `./scripts/dev-codex.sh -- exec`;
- tornar previsiveis os cenarios de timeout, erro de retorno e bloqueio operacional;
- registrar o gate minimo de validacao pratica desse adapter sem ampliar a arquitetura.

# Escopo

## Incluido

- smoke operacional minimo do `CodexCLIAdapter`
- teste(s) de integracao para o caminho real do adapter
- classificacao previsivel de falhas operacionais do launcher/container
- definicao explicita do ponto em que `DOCKER_PREFLIGHT` passa a ser obrigatorio

## Fora de escopo

- novos adapters reais
- mudancas na CLI publica
- redesign do runtime dual ou do supervisor
- suite ampla de end-to-end com multiplas ferramentas externas

# Requisitos funcionais

1. O sistema deve possuir um caminho explicito de validacao pratica para o `CodexCLIAdapter`.
2. O smoke real deve usar o launcher container-first `./scripts/dev-codex.sh -- exec`.
3. O sistema deve diferenciar falha operacional do launcher/container de falha funcional do adapter.
4. O sistema deve tratar timeout do Codex como falha previsivel e observavel.
5. O sistema deve tratar return code nao zero do Codex como falha previsivel e observavel.
6. O sistema nao deve introduzir shell nem montagem dinamica insegura de comando.

# Requisitos nao funcionais

- O recorte deve caber como follow-up pequeno da F10.
- A validacao pratica deve reaproveitar a infraestrutura operacional ja existente no repositório.
- O fluxo deve continuar coerente com o gate `DOCKER_PREFLIGHT`.
- O comportamento deve ser testavel sem exigir expansao de arquitetura.

# Casos de erro

- `codex-dev` indisponivel ou launcher falhando antes da execucao do adapter
- timeout do subprocesso real do Codex
- `return_code` nao zero no comando do Codex
- autenticacao ausente ou invalida para executar o Codex no ambiente real

# Cenarios verificaveis

## Cenario 1: smoke real do adapter funciona

- Dado um ambiente operacional valido
- Quando o `CodexCLIAdapter` for validado pelo caminho real
- Entao o launcher container-first e usado
- E o contrato de resultado do adapter permanece coerente

## Cenario 2: timeout e reportado de forma previsivel

- Dado que o subprocesso do Codex excede o tempo limite
- Quando o smoke operacional for executado
- Entao a falha e classificada explicitamente como timeout

## Cenario 3: bloqueio operacional e separado de falha funcional

- Dado que o launcher, o container ou a autenticacao impedem a execucao
- Quando a validacao pratica do adapter rodar
- Entao o resultado deixa claro que houve bloqueio operacional
- E nao uma falha silenciosa do contrato do adapter

# Observacoes

Esta frente existe para fechar a ultima lacuna operacional do primeiro adapter real, nao para expandir o produto alem do MVP. Se a validacao real exigir ajuste de ambiente em vez de ajuste de codigo, o encaminhamento correto e `debug-failure` ou `repo-automation`, sem ampliar o escopo funcional da feature.

---
id: F27-adapter-concurrency-guard
type: feature
summary: Limitar concorrencia de execucao no adapter layer com `asyncio.Semaphore`, cobrindo G-07 sem abrir circuit breaker persistido nem ampliar a arquitetura do runtime.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - src/aignt_os/adapters.py
  - src/aignt_os/config.py
outputs:
  - adapter_concurrency_guard
  - adapter_config_contract
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "trabalhar apenas o recorte de G-07"
  - "nao implementar circuit breaker persistido, estado entre runs ou G-09 nesta frente"
  - "nao alterar o contrato publico da CLI nem exigir novo subcomando"
  - "preservar timeout, sanitizacao e classificacao operacional ja existentes no adapter layer"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente nao depende de boot, ciclo de vida em container ou integracao real"
acceptance_criteria:
  - "Existe `AppSettings.max_concurrent_adapters: int = 4` com override por ambiente."
  - "A execucao de adapters passa por um guard compartilhado por processo baseado em `asyncio.Semaphore`, impedindo abrir mais subprocessos simultaneos que o limite configurado."
  - "O limite se aplica entre instancias do mesmo adapter layer no mesmo processo, sem depender de runtime distribuido ou coordenacao externa."
  - "Quando uma execucao entra no slot do semaphore, o contrato atual de timeout, sanitizacao e classificacao operacional continua inalterado."
  - "Existe cobertura unitaria e de integracao para limite respeitado, espera por slot e nao-regressao do contrato atual do adapter."
non_goals:
  - "implementar circuit breaker, cooldown ou estado persistido entre runs"
  - "criar coordenacao distribuida, fila externa ou rate limiting cross-process"
  - "mudar a CLI publica, o runtime worker ou o fluxo de pipeline fora do adapter layer"
  - "revisitar auth, provenance, preview de artifacts ou outros guardrails fora de G-07"
security_notes:
  - "o objetivo e reduzir explosao de subprocessos simultaneos no adapter layer sem reabrir a arquitetura do runtime"
  - "o guard deve ser compartilhado no processo atual e explicitamente configuravel"
  - "circuit breaker persistido fica fora desta SPEC e deve virar follow-up proprio"
dependencies:
  - F12-codex-adapter-operational-hardening
  - F23-security-sanitization-foundation
  - F24-workspace-boundary-hardening
  - F25-generated-artifact-ast-guard
  - F26-run-provenance-integrity
---

# Contexto

Depois da F26, o proximo gap logico da IDEA-001 ainda aberto no runtime atual fica na protecao contra excesso de subprocessos no adapter layer. Hoje `BaseCLIAdapter.execute()` abre o subprocesso diretamente e nao existe nenhum guard compartilhado por processo para limitar quantas chamadas de adapters podem entrar ao mesmo tempo.

No shape atual do repositório, ainda nao existe uma camada de coordenacao robusta o bastante para justificar circuit breaker persistido entre runs. O menor recorte util e coerente com o MVP e adicionar apenas o limite de concorrencia local no processo, preservando o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS e sem reabrir o runtime dual.

# Objetivo

Adicionar um guard de concorrencia no adapter layer usando `asyncio.Semaphore`, com configuracao minima em `AppSettings`, sem introduzir persistencia de estado, cooldown ou coordenacao cross-process.

# Escopo

## Incluido

- `AppSettings.max_concurrent_adapters`
- guard compartilhado por processo no adapter layer
- aplicacao do limite dentro de `BaseCLIAdapter.execute()`
- cobertura unitaria e de integracao para concorrencia limitada e nao-regressao
- `NOTES.md` da feature para registrar o boundary com G-09

## Fora de escopo

- circuit breaker persistido entre runs
- estado de health por adapter
- rate limiting distribuido ou cross-process
- alteracoes no runtime worker, banco SQLite ou CLI publica

# Requisitos funcionais

1. O projeto deve expor `max_concurrent_adapters` na configuracao com default `4`.
2. Toda execucao do adapter layer deve adquirir um slot antes de abrir o subprocesso.
3. O limite deve ser compartilhado entre instancias de adapters dentro do mesmo processo.
4. O comportamento de timeout, sanitizacao e classificacao operacional nao deve mudar quando a execucao efetivamente acontecer.
5. O guard nao deve exigir scheduler externo, locks distribuidos ou arquivo de estado.

# Requisitos nao funcionais

- o recorte deve caber em 1 a 3 dias
- a implementacao deve permanecer local ao processo atual
- a mudanca deve ser reversivel e pequena
- a feature nao deve exigir ADR nova

# Casos de erro

- configuracao invalida de `max_concurrent_adapters` com valor menor ou igual a zero
- concorrencia acima do limite configurado
- timeout ou falha operacional do adapter enquanto aguardava ou executava sob o guard

# Cenarios verificaveis

## Cenario 1: segunda execucao espera slot

- Dado `max_concurrent_adapters=1`
- Quando duas execucoes do adapter forem disparadas no mesmo processo
- Entao a segunda so abre o subprocesso depois de a primeira liberar o slot

## Cenario 2: contrato do adapter permanece intacto

- Dado uma execucao que entra no slot do semaphore
- Quando o subprocesso concluir com sucesso, timeout ou erro operacional
- Entao `CLIExecutionResult` e sua classificacao continuam com o mesmo contrato da baseline

## Cenario 3: configuracao invalida e rejeitada

- Dado `max_concurrent_adapters` menor ou igual a zero
- Quando a configuracao for carregada
- Entao a validacao falha antes de o guard ser usado

# Observacoes

Esta frente abre apenas o guard de concorrencia local (`G-07`). O circuit breaker persistido (`G-09`) permanece explicitamente fora porque exigiria contrato proprio de estado, cooldown e recuperacao entre runs, o que ampliaria demais esta SPEC.

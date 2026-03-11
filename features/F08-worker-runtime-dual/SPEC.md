---
id: F08-worker-runtime-dual
type: feature
summary: Adicionar worker leve para consumir runs pendentes e uma camada interna de dispatch sync/async sobre a persistencia operacional e o runtime dual do AIgnt OS.
inputs:
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/architecture/IMPLEMENTATION_STACK.md
  - docs/adr/009-runtime-dual-cli-worker.md
  - features/F07-persistence-artifacts/SPEC.md
  - features/f11-runtime-persistente-minimo/SPEC.md
outputs:
  - runtime_worker
  - run_dispatch_service
  - worker_runtime_tests
constraints:
  - manter o recorte backend-only sem adicionar nova CLI publica de runs
  - reutilizar o runtime dual e a persistencia operacional ja existentes
  - manter um unico worker por workspace no MVP
  - nao introduzir retry, reroute, scheduler complexo ou RUN_REPORT nesta feature
  - manter o AIgnt-Synapse-Flow como engine propria de pipeline do AIgnt OS
acceptance_criteria:
  - Existe uma camada interna de dispatch com modos `sync`, `async` e `auto`.
  - O modo `auto` executa inline quando o runtime nao esta pronto e enfileira a run quando o runtime esta pronto.
  - Existe uma forma de criar run pendente sem executa-la imediatamente.
  - Existe um worker leve capaz de selecionar a proxima run `pending` desbloqueada, adquirir lock e executa-la pela pipeline persistida.
  - O worker ignora runs ja bloqueadas, concluidas ou falhadas.
  - O loop foreground do runtime pode hospedar o worker sem alterar a CLI publica existente.
  - Existe pelo menos um teste de integracao cobrindo o worker consumindo uma run pendente em ambiente real de filesystem/SQLite.
  - Existe pelo menos um teste de integracao cobrindo o dispatch `auto` resolvendo para `async` quando o runtime esta pronto.
non_goals:
  - nova CLI publica para enfileirar ou inspecionar runs
  - multiplos workers concorrentes
  - lease distribuido ou retomada de run interrompida no meio do step
  - retry, reroute ou supervisor
  - geracao de RUN_REPORT.md
dependencies:
  - F07-persistence-artifacts
  - f11-runtime-persistente-minimo
---

# Contexto

A F07 ja persistiu runs, steps, eventos e artefatos do AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS, mas deixou explicitamente fora do escopo o worker, o polling e a retomada basica. Em paralelo, a feature de runtime persistente minimo ja entregou o lifecycle do processo residente com `start`, `status`, `run`, `ready` e `stop`, incluindo hardening local do arquivo de estado.

O gap atual do MVP nao esta em mais uma superficie publica de CLI. O gap esta em conectar essas duas bases: criar runs pendentes de forma controlada, decidir entre execucao inline ou assincrona e permitir que o processo foreground do runtime drene a fila simples de runs pendentes.

# Objetivo

Entregar o primeiro worker leve do MVP e a camada interna de dispatch do runtime dual:

- dispatch interno com modos `sync`, `async` e `auto`;
- criacao de runs pendentes sem execucao imediata;
- consumo de runs pendentes pelo processo foreground do runtime;
- lock local simples por run usando o repositorio existente;
- testes unitarios e de integracao para o caminho feliz e os bloqueios basicos.

# Escopo

## Incluido

- servico interno para despachar uma run como execucao inline ou enfileirada
- regra `auto` baseada no estado de prontidao do runtime
- selecao da proxima run `pending` e `unlocked`
- execucao de run existente pelo `run_id` persistido
- polling simples no processo foreground do runtime
- configuracao de intervalo de polling do worker
- testes unitarios e de integracao do recorte

## Fora de escopo

- comandos CLI publicos para criar ou listar runs
- worker distribuido, lease, heartbeat ou scheduler
- retomada de run parcialmente executada
- retries, reroute ou decisao do supervisor
- integracao com adapters reais ou passos alem do que a pipeline atual suporta

# Requisitos funcionais

1. O sistema deve permitir criar uma run persistida em estado `pending` sem executa-la imediatamente.
2. O sistema deve permitir executar uma run persistida existente a partir do `run_id`.
3. O dispatch interno deve aceitar os modos `sync`, `async` e `auto`.
4. O dispatch em modo `sync` deve executar a run imediatamente usando a pipeline persistida.
5. O dispatch em modo `async` deve criar a run em `pending` e retornar sem executar a pipeline.
6. O dispatch em modo `auto` deve resolver para `sync` quando o runtime nao estiver pronto.
7. O dispatch em modo `auto` deve resolver para `async` quando o runtime estiver pronto.
8. O worker deve processar no maximo uma run por polling.
9. O worker deve ignorar runs que nao estejam `pending` ou que ja estejam com lock ativo.
10. O worker deve adquirir lock antes de executar a run escolhida.
11. O loop foreground do runtime deve continuar saudavel quando nao houver runs pendentes.
12. O loop foreground do runtime deve conseguir consumir runs pendentes quando um worker estiver configurado.

# Requisitos nao funcionais

- A implementacao deve continuar pequena e local ao MVP.
- O worker deve permanecer single-process e single-workspace.
- O polling padrao deve ser simples, com intervalo fixo configuravel.
- A integracao nao deve alterar os comandos publicos existentes do runtime.
- A pipeline deve continuar reutilizando SQLite e filesystem da F07 sem nova infraestrutura.

# Casos de erro

- tentativa de executar run inexistente
- tentativa de processar run ja bloqueada
- runtime sem pronto para caminho `auto` assincrono
- falha de pipeline em uma run enfileirada
- reprocessamento acidental de run ja concluida

# Cenarios verificaveis

## Cenario 1: dispatch auto cai para sync

- Dado um runtime nao pronto
- Quando uma run e despachada com modo `auto`
- Entao o modo resolvido e `sync`
- E a run e concluida inline

## Cenario 2: dispatch auto enfileira com runtime pronto

- Dado um runtime pronto
- Quando uma run e despachada com modo `auto`
- Entao o modo resolvido e `async`
- E a run fica persistida como `pending`

## Cenario 3: worker consome uma run pendente

- Dado uma run `pending` e sem lock
- Quando o worker executa um polling
- Entao a run e processada pela pipeline persistida
- E a run termina `completed` ou `failed` de forma auditavel

## Cenario 4: worker ignora run indisponivel

- Dado uma run ja bloqueada ou ja finalizada
- Quando o worker executa um polling
- Entao nenhuma nova execucao dessa run acontece

# Observacoes

Esta feature fecha apenas o degrau minimo entre a persistencia operacional e o runtime dual. Retomada de runs interrompidas no meio, retries, reroute e superficie publica de fila ficam deliberadamente para frentes posteriores.

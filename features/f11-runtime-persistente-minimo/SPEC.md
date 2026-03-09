---
id: f11-runtime-persistente-minimo
type: feature
summary: Runtime persistente minimo com um unico processo residente real da aplicacao, comandos CLI de lifecycle, base legitima para compose e healthcheck, validacao de identidade do processo e persistencia local endurecida do estado.
status: draft
owner: wendeus0
priority: p0
estimated_size: S
related_docs:
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/architecture/IMPLEMENTATION_STACK.md
related_adrs:
  - docs/adr/002-python-orchestrator.md
  - docs/adr/003-state-machine-pipeline-engine.md
  - docs/adr/009-runtime-dual-cli-worker.md
  - docs/adr/010-adopt-aignt-synapse-flow-name.md
  - docs/adr/011-lightweight-docker-preflight-default.md
inputs:
  - CLI atual do projeto
  - decisao arquitetural de runtime dual simples
  - filesystem local para persistencia minima
outputs:
  - comando CLI para iniciar o runtime residente
  - comando CLI para consultar status do runtime
  - comando CLI para parar o runtime
  - modo de execucao persistente real da aplicacao utilizavel como processo principal do container
  - base verificavel para readiness/healthcheck do runtime
  - persistencia local endurecida do estado do runtime
  - testes automatizados da feature
acceptance_criteria:
  - Existe exatamente um processo residente local do AIgnt OS por workspace durante o MVP desta feature.
  - A CLI expõe comandos mínimos de lifecycle para start, status e stop do runtime persistente.
  - Existe um modo legitimo de execucao persistente do runtime do AIgnt OS que pode ser usado pelo `compose` como processo principal do container sem recorrer a keepalive artificial.
  - O comando start cria o processo residente e persiste estado local suficiente para identificar pid, status e metadados mínimos que permitam validar a identidade do processo antes do stop.
  - O comando status informa de forma verificável se o runtime está ativo, parado ou inconsistente.
  - O modo persistente do runtime permanece em execucao ate receber sinal de encerramento ou erro real do processo.
  - O comando stop só envia sinal quando a identidade do processo persistido for validada adicionalmente além do PID.
  - Se houver mismatch entre o estado persistido e a identidade observada do processo, o estado deve ser tratado como `inconsistent` e nenhum sinal deve ser enviado.
  - O estado persistido é gravado com permissões restritas e escrita atômica.
  - O sistema valida ou restringe o diretório configurável do estado para reduzir risco de adulteração local no escopo do MVP.
  - Existe ao menos uma verificacao local e automatizavel de prontidao baseada no proprio runtime da aplicacao, adequada para uso posterior em healthcheck/readiness.
  - O `compose` pode apontar para o runtime persistente real da aplicacao sem depender de `sleep infinity`, `tail -f /dev/null` ou artificios equivalentes.
  - O sistema trata de forma previsível os casos de runtime já ativo, runtime inexistente, pid inexistente, mismatch de identidade do processo e arquivo de estado corrompido.
  - A feature integra o lifecycle à CLI existente sem introduzir API de rede pública nem coordenação distribuída.
  - Existem testes cobrindo start, status, stop, modo persistente foreground para container, readiness minima, escrita atômica/permissões restritas e os casos mínimos de estado inconsistente.
non_goals:
  - multiplos workers ou mais de um processo residente por workspace
  - distribuicao entre nos ou coordenacao remota
  - scheduler, fila complexa ou gerenciamento avancado de jobs
  - memoria semantica ativa ou decisao automatica baseada em memoria
  - API HTTP, socket publico ou qualquer interface de rede exposta
  - recuperacao completa de jobs longos apos reinicio
dependencies:
  - f01-bootstrap-contracts
---

# Contexto

O AIgnt OS ja adota um runtime dual no nivel arquitetural, mas ainda precisa do primeiro incremento pratico desse modelo. Esta feature cria apenas o degrau minimo para que a CLI consiga iniciar, inspecionar e parar um processo residente unico, preservando o foco do MVP e sem expandir o escopo para distribuicao, scheduler ou rede.

O runtime interno continua sendo coordenado pelo AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS, mas esta feature nao implementa a pipeline completa do worker. Ela apenas estabelece o lifecycle minimo do processo residente.

Como o runtime opera por processo residente local, o hardening minimo do controle por PID e do arquivo de estado faz parte do proprio contrato da feature. O objetivo nao e adicionar um subsistema completo de seguranca, mas evitar que `stop` confie apenas em PID persistido ou em estado facilmente adulteravel.

O `DOCKER_PREFLIGHT` real em host ja validou `compose config` e `build`, mas evidenciou que o container atual apenas executa `aignt --help`, sai com codigo `0` e nao permanece vivo. Portanto, o bloqueio de `CONTAINER_UP/HEALTHY` nao e de Docker nem do host: ele decorre da ausencia de um runtime persistente legitimo da aplicacao para ser usado como processo principal do container.

# Objetivo

Entregar um runtime persistente minimo com um unico processo residente local, comandos `start`, `status` e `stop`, um modo de execucao persistente legitimo para o container da aplicacao, base real para readiness/healthcheck e persistencia local endurecida de estado, exigindo validacao adicional da identidade do processo antes de qualquer sinal de parada.

# Escopo

## Incluido

- um processo residente unico no contexto do workspace atual
- comandos CLI minimos de lifecycle: `start`, `status` e `stop`
- um modo de execucao persistente real da aplicacao para uso como processo principal do container
- uma verificacao minima de prontidao baseada no proprio runtime para suportar healthcheck/readiness
- persistencia local endurecida do estado do runtime em disco
- checagem basica de consistencia entre estado persistido e processo real
- validacao adicional da identidade do processo antes do `stop`
- escrita atomica e permissoes restritas para o arquivo de estado
- validacao ou restricao do diretorio configuravel do estado no escopo do MVP
- integracao direta com a CLI atual do projeto
- testes automatizados focados no lifecycle minimo

## Fora de escopo

- multiplos workers
- execucao distribuida
- scheduler
- fila de jobs complexa
- keepalive artificial de container via `sleep`, `tail -f` ou equivalente
- memoria semantica ativa
- API de rede publica
- orquestracao completa de runs longas
- protocolo de healthcheck remoto complexo ou observabilidade distribuida

# Requisitos funcionais

1. O usuario deve conseguir iniciar o runtime persistente por um comando CLI explicito.
2. O sistema deve impedir a criacao de um segundo processo residente quando um runtime valido ja estiver ativo.
3. O usuario deve conseguir consultar o estado atual do runtime por um comando CLI explicito.
4. O usuario deve conseguir parar o runtime por um comando CLI explicito.
5. O sistema deve expor ao menos um modo de execucao persistente real da aplicacao que possa ser usado pelo `compose` como processo principal do container.
6. O sistema deve fornecer uma forma automatizavel de verificar se o runtime persistente esta pronto ou nao, sem depender apenas de o processo existir.
7. O sistema deve persistir em disco o estado minimo necessario para suportar os comandos de lifecycle.
8. O sistema nao deve depender de keepalive artificial de container para manter o processo principal em execucao.
9. O sistema deve detectar ao menos os estados `running`, `stopped` e `inconsistent`.
10. O sistema deve tratar arquivo de estado corrompido sem travar a CLI.
11. O sistema deve validar a identidade do processo do runtime com pelo menos um dado adicional alem do PID antes de enviar sinal de parada.
12. O sistema nao deve enviar sinal quando houver mismatch entre o processo observado e a identidade persistida do runtime.
13. O sistema deve tratar mismatch de identidade como estado `inconsistent`.
14. O sistema deve restringir ou validar o diretorio configuravel do estado dentro do recorte do workspace/local esperado pelo MVP.

# Requisitos nao funcionais

- A implementacao deve permanecer pequena o suficiente para 1 a 3 dias de trabalho.
- A persistencia deve ser local, simples e endurecida, sem exigir banco dedicado ou servico externo.
- A integracao deve reutilizar a CLI Python existente do projeto.
- O processo persistente do container deve ser um processo legitimo da aplicacao e nao um placeholder para manter o container vivo.
- A feature deve continuar compativel com o modelo Docker e com o fluxo `DOCKER_PREFLIGHT -> SPEC -> TEST_RED -> CODE_GREEN -> REFACTOR -> SECURITY_REVIEW -> REPORT -> COMMIT`.
- A implementacao nao deve introduzir dependencias operacionais pesadas sem necessidade clara.
- A escrita do estado deve ser atomica.
- Diretorio e arquivo de estado devem usar permissoes restritas adequadas ao uso local do MVP.

# Casos de erro

- tentativa de `start` com runtime ja ativo
- tentativa de `stop` sem runtime ativo
- arquivo de estado ausente
- arquivo de estado corrompido
- pid persistido que nao corresponde a processo vivo
- pid persistido que corresponde a outro processo sem identidade valida de runtime
- mismatch entre metadados persistidos e identidade observada do processo
- compose apontando para um comando que encerra imediatamente e nao representa runtime persistente real
- readiness/healthcheck sem base legitima no runtime da aplicacao
- diretorio configuravel de estado fora da area permitida pelo contrato local do MVP
- falha para atualizar o estado persistido durante start ou stop

# Cenarios verificaveis

## Cenario 1: start inicial

- Dado que nao existe runtime ativo
- Quando o usuario executa o comando `start`
- Entao um unico processo residente e iniciado
- E um estado local minimo e persistido

## Cenario 2: status com runtime ativo

- Dado que o runtime esta ativo e o estado persistido esta coerente
- Quando o usuario executa o comando `status`
- Entao a CLI informa que o runtime esta `running`

## Cenario 3: start com runtime ja ativo

- Dado que ja existe runtime ativo para o workspace
- Quando o usuario executa `start`
- Entao a CLI nao cria um segundo processo
- E retorna resultado previsivel informando que o runtime ja esta ativo

## Cenario 4: status inconsistente

- Dado que existe estado persistido com pid inexistente ou invalido
- Quando o usuario executa `status`
- Entao a CLI informa estado `inconsistent`

## Cenario 5: stop normal

- Dado que existe runtime ativo
- Quando o usuario executa `stop`
- Entao o processo residente e encerrado
- E o estado persistido passa a refletir que o runtime nao esta mais ativo

## Cenario 6: stop com mismatch de identidade

- Dado que existe um PID persistido, mas a identidade observada do processo nao corresponde ao runtime esperado
- Quando o usuario executa `stop`
- Entao nenhum sinal e enviado ao processo observado
- E a CLI trata o estado como `inconsistent`

## Cenario 7: persistencia endurecida

- Dado que o runtime grava o estado local em disco
- Quando o arquivo de estado e criado ou atualizado
- Entao a escrita ocorre de forma atomica
- E diretorio e arquivo usam permissoes restritas adequadas ao uso local do MVP

## Cenario 8: modo persistente para container

- Dado que o container da aplicacao precisa permanecer em execucao por um runtime real
- Quando o `compose` usa o comando persistente da aplicacao
- Entao o processo principal do container permanece ativo ate receber sinal ou erro real
- E o comportamento nao depende de keepalive artificial

## Cenario 9: readiness minima do runtime

- Dado que existe um runtime persistente legitimo em execucao
- Quando uma verificacao de prontidao e executada
- Entao ela retorna resultado verificavel compativel com uso posterior em healthcheck/readiness
- E falha de forma previsivel quando o runtime nao estiver pronto ou estiver inconsistente

# Observabilidade minima

- O estado persistido deve ser legivel localmente para inspecao operacional.
- Os comandos de lifecycle devem retornar saida limpa e verificavel para testes.
- A verificacao minima de prontidao deve produzir resultado limpo e automatizavel.

# Observacoes

Esta feature nao entrega um worker completo de execucao de runs nem uma plataforma completa de processamento em background. Ela entrega apenas a base minima de lifecycle para o runtime persistente do MVP e o contrato necessario para que o container da aplicacao possa atingir `CONTAINER_UP/HEALTHY` de forma legitima.

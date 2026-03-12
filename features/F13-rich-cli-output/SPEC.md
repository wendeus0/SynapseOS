---
id: F13-rich-cli-output
type: feature
summary: Enriquecer a saida do comando `aignt runtime status` com Rich, mantendo o recorte pequeno e sem abrir uma TUI.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - memory.md
  - PENDING_LOG.md
  - src/aignt_os/cli/app.py
outputs:
  - rich_runtime_status_output
  - cli_rendering_helper
  - runtime_status_tests
constraints:
  - manter o AIgnt-Synapse-Flow como engine propria de pipeline do AIgnt OS
  - manter o recorte limitado ao comando `aignt runtime status`
  - nao introduzir Textual, watch mode ou nova TUI
  - nao alterar o comportamento operacional do runtime nem o contrato de erro
  - nao exigir DOCKER_PREFLIGHT, pois a frente nao depende de validacao pratica em Docker
acceptance_criteria:
  - "`aignt runtime status` usa Rich para apresentar o estado do runtime em formato mais legivel do que a linha crua atual."
  - "Existe pelo menos um teste de integracao cobrindo a saida enriquecida do comando para runtime em execucao."
  - "Existe pelo menos um teste cobrindo o caso inconsistente sem perder a saida em `stderr` nem o exit code de falha."
  - "A saida enriquecida continua utilizavel em ambiente sem TTY e em captura de testes."
  - "A frente nao amplia a CLI publica nem adiciona dependencia nova."
non_goals:
  - criar `aignt tui`
  - enriquecer todos os comandos da CLI na mesma feature
  - mudar o lifecycle do runtime
  - adicionar observabilidade nova ou watch mode
security_notes:
  - manter a frente restrita a apresentacao de dados ja existentes
  - nao introduzir subprocessos, shell ou leitura adicional de paths
dependencies:
  - F08-worker-runtime-dual
  - f11-runtime-persistente-minimo
---

# Contexto

O MVP inicial ja entrega runtime persistente minimo, worker leve e o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS. Porem, a CLI ainda apresenta `aignt runtime status` com `typer.echo()` em formato cru, suficiente para maquina mas pouco legivel para uso operacional diario.

Rich ja faz parte da stack de producao do projeto e ainda nao foi usado no codigo de `src/`. Isso abre uma frente pequena e de baixo risco para melhorar UX de terminal sem alterar arquitetura, sem dependencias novas e sem abrir uma TUI completa.

# Objetivo

Entregar a primeira saida CLI enriquecida com Rich no projeto, restrita ao comando `aignt runtime status`, preservando a semantica atual de sucesso e falha e garantindo boa degradacao fora de TTY.

# Escopo

## Incluido

- helper interna de apresentacao para o comando `runtime status`
- uso de Rich no caminho de saida desse comando
- testes de integracao para os estados `running` e `inconsistent`
- teste unitario do rendering helper para ambiente sem TTY

## Fora de escopo

- TUI com Textual
- watch command
- enriquecimento de `runtime start`, `runtime stop` ou outros comandos
- mudancas em pipeline, worker, supervisor ou adapters

# Requisitos funcionais

1. O comando `aignt runtime status` deve continuar refletindo o estado real do runtime.
2. Quando o runtime estiver em execucao, a saida deve exibir o status de forma enriquecida e incluir o PID persistido.
3. Quando o runtime estiver inconsistente, a saida enriquecida deve continuar indo para `stderr` e o comando deve continuar encerrando com codigo de falha.
4. O comando nao deve depender de TTY para produzir saida legivel.

# Requisitos nao funcionais

- A implementacao deve reutilizar apenas Rich ja presente no projeto.
- O recorte deve permanecer pequeno e local na camada de CLI.
- A saida capturada por testes deve permanecer assertavel sem depender de ANSI.

# Casos de erro

- estado persistido inconsistente
- runtime parado sem PID persistido
- execucao em ambiente nao interativo

# Cenarios verificaveis

## Cenario 1: runtime em execucao

- Dado um runtime ativo
- Quando `aignt runtime status` for executado
- Entao a CLI exibe uma saida enriquecida com Rich
- E a saida inclui pelo menos o status e o PID

## Cenario 2: runtime inconsistente

- Dado um estado persistido inconsistente
- Quando `aignt runtime status` for executado
- Entao a saida enriquecida e emitida em `stderr`
- E o comando falha com exit code diferente de zero

## Cenario 3: captura sem TTY

- Dado um console sem TTY
- Quando o helper de apresentacao for usado
- Entao a saida continua legivel sem depender de sequencias ANSI

# Observacoes

Esta frente existe para inaugurar Rich no produto com risco baixo. Qualquer expansao para watch mode, observabilidade rica ou Textual deve ser tratada como feature propria posterior.

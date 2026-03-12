---
id: F17-artifact-preview
type: feature
summary: Adicionar preview textual controlado de artifacts uteis em `aignt runs show <run_id>` sem abrir leitura arbitraria do host nem dump irrestrito de outputs.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/architecture/PHASE_2_ROADMAP.md
  - features/F16-run-detail-expansion/SPEC.md
  - features/F21-cli-error-model-and-exit-codes/SPEC.md
  - src/aignt_os/cli/app.py
  - src/aignt_os/cli/rendering.py
  - src/aignt_os/persistence.py
outputs:
  - artifact_preview_cli_contract
  - artifact_preview_tests
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "manter a superficie publica concentrada no comando existente `aignt runs show <run_id>`"
  - "usar um unico seletor opcional de preview: `--preview <target>`"
  - "limitar os targets suportados a `report` e `<STEP_STATE>.clean`"
  - "nao permitir leitura arbitraria por path informado pelo usuario"
  - "nao alterar schema SQLite, layout de artifacts no filesystem, worker ou pipeline"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente so le sinais persistidos locais"
acceptance_criteria:
  - "`aignt runs show <run_id>` continua exibindo o detalhe atual por padrao e passa a aceitar `--preview <target>` sem quebrar o caminho existente."
  - "`aignt runs show <run_id> --preview report` exibe um preview textual do `RUN_REPORT.md` persistido para a run, incluindo o path de origem e um trecho truncado quando necessario."
  - "`aignt runs show <run_id> --preview <STEP_STATE>.clean` exibe um preview textual do `clean_output` persistido do step solicitado, sem expor `raw_output`."
  - "O preview e limitado ao inicio do arquivo, com truncamento explicito apos no maximo 40 linhas, para evitar dump irrestrito de artifacts grandes."
  - "Preview alvo invalido retorna `Usage error:` com exit code `2`, e preview solicitado para conteudo inexistente retorna `Not found:` com exit code `3`, sempre sem traceback cru."
  - "Existe pelo menos um teste de integracao cobrindo preview de report e pelo menos um teste de integracao cobrindo target invalido ou preview ausente via CLI publica."
non_goals:
  - "preview de `raw.txt`, dumps integrais de arquivo ou paginação interativa"
  - "leitura de named artifacts arbitrarios como `plan_md.txt` por path livre"
  - "watch mode, streaming, TUI ou subcomando novo para artifacts"
  - "hardening amplo de mascaramento de secrets fora do contrato atual de outputs limpos"
security_notes:
  - "resolver o preview apenas a partir de paths persistidos da propria run e de targets controlados pela CLI"
  - "rejeitar qualquer alvo fora do conjunto permitido, sem interpolar path do usuario no filesystem"
  - "manter o preview textual e truncado, evitando exposicao ampla de artifacts grandes ou ruidosos"
dependencies:
  - F16-run-detail-expansion
  - F18-canonical-happy-path
  - F21-cli-error-model-and-exit-codes
---

# Contexto

Depois da `F16`, a CLI publica do AIgnt OS ja consegue explicar melhor o estado de uma run e listar onde estao seus outputs e artifacts persistidos, enquanto o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS. Porem, o operador ainda precisa sair da superficie publica da CLI para abrir manualmente `RUN_REPORT.md` ou um `clean_output` relevante quando quer confirmar o conteudo de um sinal persistido.

A `F17` existe para reduzir esse atrito sem transformar `aignt runs show` em dump arbitrario de arquivos. O objetivo e oferecer preview controlado dos artifacts mais uteis ao fluxo publico atual, mantendo a leitura restrita a alvos explicitamente suportados e previsiveis.

# Objetivo

Entregar preview textual controlado de report e output limpo por step dentro de `aignt runs show <run_id>`, preservando o contrato atual da CLI e evitando leitura arbitraria de arquivos ou ampliacao indevida da superficie publica.

# Escopo

## Incluido

- extensao pequena de `aignt runs show <run_id>` com `--preview <target>`
- preview de `RUN_REPORT.md` persistido da run
- preview de `clean_output` persistido por step
- truncamento explicito para manter a leitura curta e segura
- testes unitarios de rendering e testes de integracao da CLI
- `NOTES.md` da feature para registrar as decisoes de recorte

## Fora de escopo

- preview de `raw_output`
- leitura de arquivo arbitrario por path
- dump completo de artifacts grandes
- subcomando novo `runs artifact` ou similar
- watch mode, TUI, streaming ou exportacao

# Requisitos funcionais

1. `aignt runs show <run_id>` deve manter o comportamento atual quando `--preview` nao for informado.
2. A CLI deve aceitar um unico argumento opcional `--preview <target>`.
3. Os targets validos devem ser:
   - `report`
   - `<STEP_STATE>.clean`
4. Quando o target for `report`, a CLI deve localizar o `RUN_REPORT.md` persistido da run e renderizar:
   - o tipo de preview solicitado
   - o path de origem
   - o trecho textual inicial do arquivo
5. Quando o target for `<STEP_STATE>.clean`, a CLI deve localizar o `clean_output_path` persistido do step com `state` correspondente e renderizar:
   - o tipo de preview solicitado
   - o path de origem
   - o trecho textual inicial do arquivo
6. O preview deve ler apenas o inicio do conteudo e truncar explicitamente o restante apos no maximo 40 linhas.
7. O preview de step deve permanecer restrito a `clean_output`; `raw_output` continua apenas como metadado/path na saida.
8. Se `--preview` receber target fora do contrato suportado, a CLI deve falhar com `Usage error:` e exit code `2`.
9. Se o target for valido, mas a run nao tiver o artifact correspondente persistido, a CLI deve falhar com `Not found:` e exit code `3`.
10. Todas as falhas desta frente devem permanecer sem traceback cru.

# Requisitos nao funcionais

- A implementacao deve permanecer concentrada na camada de CLI, rendering e leitura controlada de artifacts persistidos.
- O preview deve continuar legivel em ambiente sem TTY e em captura de testes.
- A frente nao deve exigir mudanca em schema SQLite nem no layout de persistencia ja estabelecido.
- O recorte deve continuar pequeno o bastante para caber em uma unica feature da etapa 2, sem abrir follow-up de seguranca por inercia.

# Casos de erro

- `run_id` inexistente
- `--preview` com target invalido
- run existente sem `RUN_REPORT.md` persistido
- run existente sem `clean_output_path` para o step solicitado
- artifact textual maior que o limite de preview
- path persistido ausente no disco no momento da leitura

# Cenarios verificaveis

## Cenario 1: preview do report da run

- Dado uma run com `RUN_REPORT.md` persistido
- Quando `aignt runs show <run_id> --preview report` for executado
- Entao a CLI retorna exit code `0`
- E exibe o path do report
- E exibe um preview textual truncado quando necessario

## Cenario 2: preview de output limpo por step

- Dado uma run com `clean_output` persistido para um step
- Quando `aignt runs show <run_id> --preview PLAN.clean` for executado
- Entao a CLI retorna exit code `0`
- E exibe o path de `clean_output`
- E nao exibe `raw_output` como conteudo do preview

## Cenario 3: target invalido ou preview ausente

- Dado um target invalido ou um artifact previewable ausente
- Quando `aignt runs show <run_id> --preview <target>` for executado
- Entao a CLI falha com o exit code correto do contrato da F21
- E a mensagem permanece curta e sem traceback cru

# Observacoes

Esta frente melhora a ergonomia da CLI publica por leitura controlada de sinais ja persistidos, sem transformar `runs show` em browser de filesystem. Se surgir evidencia real de vazamento de segredo ou de necessidade de mascaramento adicional para previews publicos, isso deve virar follow-up explicito ou endurecimento localizado, e nao ampliacao silenciosa desta feature.

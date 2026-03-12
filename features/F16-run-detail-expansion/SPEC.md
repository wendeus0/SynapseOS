---
id: F16-run-detail-expansion
type: feature
summary: Aprofundar o diagnostico de `aignt runs show <run_id>` para orientar o proximo passo operacional sem abrir preview de conteudo nem nova TUI.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - memory.md
  - PENDING_LOG.md
  - src/aignt_os/cli/app.py
  - src/aignt_os/cli/rendering.py
  - src/aignt_os/persistence.py
outputs:
  - expanded_run_detail_rendering
  - run_detail_tests
  - feature_notes_and_checklist
constraints:
  - manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS
  - manter a superficie publica restrita ao comando existente `aignt runs show <run_id>`
  - nao introduzir nova flag, novo subcomando, TUI, watch mode ou preview de conteudo de artifacts
  - reutilizar apenas `RunRepository`, `ArtifactStore` e os registros persistidos ja existentes
  - nao alterar schema SQLite nem layout de artifacts no filesystem
  - nao exigir DOCKER_PREFLIGHT, pois a frente nao depende de validacao pratica em Docker
acceptance_criteria:
  - "`aignt runs show <run_id>` passa a exibir um resumo de diagnostico com `status`, `current_state`, ultimo evento relevante, timestamp mais recente e orientacao objetiva de proximo passo."
  - "Quando houver steps persistidos, `aignt runs show <run_id>` exibe paths de `raw_output` e `clean_output` associados ao step, sem ler o conteudo desses arquivos."
  - "A secao de eventos passa a exibir timestamp persistido para facilitar diagnostico cronologico."
  - "Existe pelo menos um teste de integracao cobrindo run `completed` e pelo menos um cobrindo run `failed` ou `pending`, verificando o resumo de diagnostico e as novas informacoes operacionais."
  - "A saida enriquecida continua legivel sem TTY e `run_id` inexistente continua falhando sem traceback cru."
non_goals:
  - criar comando novo para artifacts
  - exibir conteudo de `raw.txt`, `clean.txt` ou `RUN_REPORT.md`
  - alterar o modelo global de erros e exit codes da CLI
  - mudar persistencia, worker ou pipeline
security_notes:
  - limitar a exibicao a metadados e paths ja persistidos sob `runs_db_path` e `artifacts_dir`
  - nao adicionar shell, subprocesso novo ou leitura arbitraria de arquivo
dependencies:
  - F14-runs-observability-cli
  - F15-public-run-submission
---

# Contexto

A CLI publica ja expõe `aignt runs list`, `aignt runs show <run_id>` e `aignt runs submit <spec_path>`, enquanto o AIgnt-Synapse-Flow continua como a engine propria de pipeline do AIgnt OS. Porem, o detalhe atual de `runs show` ainda exige leitura mental excessiva: faltam resumo de diagnostico, cronologia mais clara e indicacao objetiva do proximo ponto de investigacao.

A fila oficial da etapa 2 prioriza justamente reduzir esse atrito logo apos a submissao publica. A F16 deve aprofundar a visibilidade de uma run sem abrir nova superficie publica nem antecipar preview de artifacts, que permanece reservado para a F17.

# Objetivo

Entregar uma expansao pequena e localizada de `aignt runs show <run_id>` para que um operador consiga identificar rapidamente onde a run esta, qual foi o ultimo sinal persistido e qual e o proximo passo operacional mais util.

# Escopo

## Incluido

- resumo de diagnostico no detalhe da run
- timestamps nos eventos exibidos
- paths de outputs persistidos por step
- organizacao mais clara dos paths de artifacts ja existentes
- testes unitarios de rendering e testes de integracao da CLI
- notes e checklist proprios da feature

## Fora de escopo

- preview de conteudo de artifact
- filtros, watch mode ou streaming
- nova flag ou novo subcomando em `aignt runs`
- mudanca em schema SQLite, `RunRepository` ou `ArtifactStore`

# Requisitos funcionais

1. `aignt runs show <run_id>` deve apresentar um resumo de diagnostico no topo da saida.
2. O resumo deve incluir pelo menos:
   - `status`
   - `current_state`
   - ultimo evento persistido, quando existir
   - timestamp mais recente disponivel
   - orientacao objetiva de proximo passo
3. A tabela de steps deve continuar exibindo o status operacional e passar a listar os paths de `raw_output` e `clean_output`, quando existirem.
4. A tabela de eventos deve exibir o timestamp persistido de cada evento.
5. A secao de artifacts deve permanecer restrita a paths, com apresentacao legivel para diagnostico.
6. O comportamento para `run_id` inexistente deve permanecer previsivel e sem traceback cru.

# Requisitos nao funcionais

- A implementacao deve permanecer localizada na CLI e no helper de rendering.
- A saida deve continuar legivel em ambiente sem TTY e em captura de testes.
- A F16 nao deve antecipar a F17 nem a F21.

# Casos de erro

- `run_id` inexistente
- run sem steps persistidos
- run sem eventos persistidos
- run `pending` ou `failed` com poucos sinais persistidos
- run com paths de outputs ausentes em parte dos steps

# Cenarios verificaveis

## Cenario 1: run concluida com sinais persistidos

- Dado uma run concluida com steps, eventos e artifacts
- Quando `aignt runs show <run_id>` for executado
- Entao a CLI exibe um resumo de diagnostico
- E exibe o ultimo evento persistido
- E exibe paths de `raw_output` e `clean_output`
- E exibe timestamps de eventos

## Cenario 2: run falha ou pendente

- Dado uma run falha ou pendente com persistencia parcial
- Quando `aignt runs show <run_id>` for executado
- Entao a CLI informa o estado atual
- E informa o proximo passo operacional recomendado
- E continua legivel mesmo sem todos os dados opcionais

## Cenario 3: run ausente

- Dado um `run_id` inexistente
- Quando `aignt runs show <run_id>` for executado
- Entao a CLI falha sem traceback cru
- E informa que a run nao foi encontrada

# Observacoes

Esta frente existe para aprofundar diagnostico sem expandir a superficie publica. Preview de conteudo de artifacts continua fora de escopo e deve permanecer reservado para a `F17-artifact-preview`.

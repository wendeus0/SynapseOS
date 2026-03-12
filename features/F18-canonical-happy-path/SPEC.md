---
id: F18-canonical-happy-path
type: feature
summary: Consolidar o caminho canonico e reproduzivel da CLI publica para submeter e inspecionar uma run concluida no menor happy path estavel.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/architecture/PHASE_2_ROADMAP.md
  - src/aignt_os/cli/app.py
  - src/aignt_os/cli/rendering.py
  - tests/integration/test_runs_submit_cli.py
  - tests/integration/test_runs_cli.py
outputs:
  - canonical_happy_path_spec
  - canonical_cli_flow_tests
  - feature_notes_and_checklist
constraints:
  - manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS
  - manter o recorte restrito a um fluxo sincrono, auditavel e reproduzivel pela CLI publica ja existente
  - reutilizar apenas `aignt runs submit <spec_path>` e `aignt runs show <run_id>` como superficie publica obrigatoria do caminho canonico
  - nao introduzir novo subcomando, nova flag publica, TUI, watch mode, preview de artifact, schema SQLite novo ou runtime paralelo adicional
  - nao exigir DOCKER_PREFLIGHT nesta frente, porque o recorte default nao depende de Docker, boot completo de runtime nem integracao em container
acceptance_criteria:
  - "Existe um caminho canonico documentado pela feature em que `aignt runs submit <spec_path> --mode sync --stop-at SPEC_VALIDATION` conclui a run inline e retorna pelo menos `run_id`, `status=completed` e `mode=sync`."
  - "No recorte da F18, o sucesso terminal do happy path e definido explicitamente como `status=completed` com `current_state=SPEC_VALIDATION`, sem exigir execucao publica alem desse ponto."
  - "Apos a submissao bem-sucedida, `aignt runs show <run_id>` exibe sinais suficientes para auditoria do happy path: `status`, `current_state`, ultimo sinal relevante, `spec_path` e referencias a dados persistidos da run."
  - "Existe pelo menos um teste de integracao cobrindo a sequencia canonica completa da CLI publica: submeter uma SPEC valida em `sync`, capturar o `run_id` retornado e inspecionar a mesma run com `runs show`."
  - "A feature define explicitamente os pre-requisitos minimos da demonstracao e deixa fora de escopo runtime persistente, doctor de ambiente, onboarding publico e qualquer variante assincrona como caminho oficial primario."
non_goals:
  - transformar o happy path canonico em runtime persistente por default
  - exigir `runtime start`, `runtime ready` ou worker residente como parte obrigatoria da demonstracao inicial
  - adicionar comandos novos, preview de conteudo de artifact, doctor ou onboarding
  - ampliar a demo para multiplos adapters reais, multiplas SPECs de referencia ou cenarios paralelos
security_notes:
  - limitar a demonstracao a paths de SPEC explicitamente informados e a metadados ja persistidos pela run
  - nao introduzir shell, subprocesso novo ou leitura arbitraria de arquivo fora do contrato existente da CLI
  - manter o fluxo auditavel sem traceback cru e sem vazar conteudo de artifacts como requisito do caminho canonico
dependencies:
  - F15-public-run-submission
  - F16-run-detail-expansion
  - F21-cli-error-model-and-exit-codes
---

# Contexto

Depois de F15, F16 e F21, a CLI publica do AIgnt OS ja permite submeter uma SPEC valida, concluir uma run sincronamente no menor recorte suportado e inspecionar a run persistida. O AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS, mas ainda falta consolidar qual sequencia de comandos representa o happy path oficial da etapa 2.

A lacuna atual nao e de capacidade tecnica isolada, e sim de contrato operacional: sem uma definicao canonica, a demonstracao publica da ferramenta continua dispersa entre comandos existentes, defaults implicitos e variantes que aumentam custo de validacao sem necessidade.

# Objetivo

Definir o menor caminho publico, reproduzivel e auditavel de ponta a ponta para demonstrar sucesso na CLI do AIgnt OS: submeter uma SPEC valida em modo sincrono, obter uma run concluida e inspecionar essa run com `aignt runs show <run_id>`.

# Escopo

## Incluido

- formalizacao da sequencia oficial de comandos do happy path
- definicao explicita do estado terminal que comprova sucesso no recorte atual
- definicao dos sinais minimos que a CLI deve exibir na submissao e na inspecao da run
- testes de integracao cobrindo a sequencia publica canonica completa
- notes e checklist proprios da feature

## Fora de escopo

- runtime persistente como caminho oficial primario
- validacao pratica dependente de Docker ou container
- doctor de ambiente, onboarding publico ou quickstart enciclopedico
- nova superficie publica na CLI
- execucao publica alem do menor terminal estavel ja suportado

# Requisitos funcionais

1. A F18 deve definir como comando inicial canonico:
   - `aignt runs submit <spec_path> --mode sync --stop-at SPEC_VALIDATION`
2. A feature deve declarar explicitamente que, no recorte atual, o happy path oficial usa `--mode sync` para evitar pre-requisitos externos frageis.
3. O sucesso terminal do caminho canonico deve ser:
   - `status=completed`
   - `current_state=SPEC_VALIDATION`
4. A saida de `runs submit` no caminho canonico deve permitir ao operador recuperar o `run_id` sem consultar arquivos internos manualmente.
5. A feature deve definir como passo de auditoria obrigatorio:
   - `aignt runs show <run_id>`
6. A saida de `runs show` usada no happy path deve comprovar pelo menos:
   - identificacao da run
   - `status`
   - `current_state`
   - ultimo sinal relevante
   - `spec_path`
   - referencias persistidas suficientes para investigacao posterior
7. O acceptance check da feature deve provar que um operador consegue executar o caminho canonico apenas pela CLI publica, sem abrir SQLite nem navegar manualmente pelo filesystem de artifacts.

# Requisitos nao funcionais

- O recorte deve permanecer pequeno o suficiente para seguir direto para TEST_RED sem abrir subfeatures.
- O fluxo canonico deve continuar legivel sem TTY e assertavel em testes de integracao.
- A F18 nao deve redefinir o modelo global de erro, apenas consumir o contrato ja estabilizado pela F21.
- A F18 nao deve exigir `repo-preflight`, salvo se a SPEC for alterada no futuro para depender de Docker ou runtime persistente real.

# Casos de erro

- path de SPEC ausente
- SPEC invalida
- falha em capturar ou reutilizar o `run_id` retornado por `runs submit`
- `run_id` inexistente ao executar `runs show`
- ausencia de sinais minimos na saida da CLI para comprovar o caminho feliz

# Cenarios verificaveis

## Cenario 1: demonstracao canonica sincrona

- Dado uma SPEC valida acessivel por path
- Quando `aignt runs submit <spec_path> --mode sync --stop-at SPEC_VALIDATION` for executado
- Entao a CLI retorna `run_id`
- E retorna `status=completed`
- E retorna `mode=sync`
- E a run fica persistida com `current_state=SPEC_VALIDATION`

## Cenario 2: auditoria da run concluida

- Dado o `run_id` retornado pela submissao canonica
- Quando `aignt runs show <run_id>` for executado
- Entao a CLI exibe o resumo diagnostico da run concluida
- E exibe `status=completed`
- E exibe `current_state=SPEC_VALIDATION`
- E exibe `spec_path`
- E exibe sinais persistidos suficientes para auditoria

## Cenario 3: limites do caminho oficial

- Dado o recorte da F18
- Quando a feature documentar o caminho canonico oficial
- Entao runtime persistente, variantes `auto` ou `async`, doctor e onboarding ficam explicitamente fora do escopo primario
- E o operador entende que essas variantes nao sao pre-requisito para a primeira demonstracao oficial

# Observacoes

O estado terminal canonico da F18 nao representa a pipeline completa do produto; ele representa o menor sucesso publico estavel que ja pode ser demonstrado hoje sem acoplamento adicional. Se uma futura feature promover `PLAN` ou estados seguintes a caminho oficial minimo da CLI, a F18 podera ser revisitada, mas sem antecipar essa decisao agora.

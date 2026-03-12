---
id: F19-environment-doctor
type: feature
summary: Adicionar um doctor de ambiente pequeno e local para diagnosticar os pre-requisitos do fluxo publico atual da CLI sem autocorrecao.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/architecture/PHASE_2_ROADMAP.md
  - src/aignt_os/cli/app.py
  - src/aignt_os/config.py
  - src/aignt_os/runtime/service.py
  - src/aignt_os/persistence.py
outputs:
  - environment_doctor_cli_contract
  - doctor_rendering_and_exit_code_tests
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "manter o recorte restrito a diagnostico local e somente leitura logica, sem autocorrecao do ambiente"
  - "expor um unico comando publico novo: `aignt doctor`"
  - "reutilizar `AppSettings`, `RuntimeService`, `RunRepository` e `ArtifactStore` apenas para verificacoes leves do ambiente atual"
  - "nao exigir DOCKER_PREFLIGHT, porque o recorte default nao depende de Docker, build, boot completo de runtime nem integracao em container"
  - "nao introduzir TUI, watch mode, shell novo, subprocesso arbitrario nem verificacoes dependentes de credencial externa"
acceptance_criteria:
  - "`aignt doctor` passa a exibir um resumo legivel do ambiente local com status geral e checks nomeados para `runtime_state`, `runs_db` e `artifacts_dir`."
  - "Cada check informa `pass`, `warn` ou `fail` e uma orientacao objetiva de proximo passo, sem traceback cru."
  - "O doctor detecta pelo menos: estado de runtime inconsistente, parent directory nao gravavel para `runs_db_path` e parent directory nao gravavel para `artifacts_dir`."
  - "Quando o ambiente minimo do fluxo publico atual estiver pronto, `aignt doctor` retorna exit code `0`; quando houver falha bloqueante de ambiente, retorna exit code `5` conforme o contrato da F21."
  - "Existe pelo menos um teste de integracao cobrindo ambiente saudavel e pelo menos um cobrindo falha bloqueante de ambiente via CLI publica."
non_goals:
  - "autocorrigir permissoes, criar containers ou iniciar/parar o runtime"
  - "validar credenciais de adapters reais, autenticacao externa ou MCPs"
  - "substituir `repo-preflight` ou antecipar `DOCKER_PREFLIGHT`"
  - "validar uma `SPEC.md` especifica informada pelo usuario"
  - "abrir onboarding publico, quickstart enciclopedico ou preview de artifacts"
security_notes:
  - "limitar as verificacoes a paths resolvidos por `AppSettings` e ao estado local do runtime ja persistido"
  - "nao adicionar leitura arbitraria de arquivo fora dos paths configurados nem execucao de shell"
dependencies:
  - F18-canonical-happy-path
  - F21-cli-error-model-and-exit-codes
---

# Contexto

Depois de `F15`, `F16`, `F21` e `F18`, a CLI publica do AIgnt OS ja expõe um caminho canonico minimo para submeter e inspecionar uma run, enquanto o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS. O atrito seguinte nao e de fluxo da run em si, mas de diagnostico do ambiente local antes da primeira execucao real por um operador.

Hoje, quando o diretório de estado, o banco SQLite ou a area de artifacts estao mal configurados, o operador precisa inferir isso indiretamente por falhas em `runs submit`, `runtime status` ou outros comandos. A `F19` existe para transformar esse diagnostico em um comando publico pequeno, objetivo e testavel.

# Objetivo

Entregar um doctor de ambiente enxuto, acessivel por `aignt doctor`, capaz de verificar os pre-requisitos locais minimos do fluxo publico atual e orientar o operador sobre o proximo passo sem alterar o ambiente automaticamente.

# Escopo

## Incluido

- um comando publico novo: `aignt doctor`
- resumo geral do ambiente com checks nomeados
- verificacao leve de paths configurados para runtime state, SQLite e artifacts
- verificacao do estado atual do runtime como `pass`, `warn` ou `fail`
- orientacao objetiva de proximo passo por check
- testes unitarios de rendering/classificacao e testes de integracao da CLI
- `NOTES.md` da feature para registrar escolhas de recorte

## Fora de escopo

- auto-fix de permissao, bootstrap de diretórios ou correcoes no filesystem
- validacao de Docker, compose, imagem, container ou runtime completo
- verificacao de credenciais do Codex, GitHub ou outros providers
- validacao de uma SPEC fornecida por path
- onboarding publico e documentacao de quickstart

# Requisitos funcionais

1. A CLI deve expor `aignt doctor` como comando publico de diagnostico local.
2. O comando deve apresentar um resumo com status geral do ambiente.
3. O doctor deve listar checks nomeados, no minimo:
   - `runtime_state`
   - `runs_db`
   - `artifacts_dir`
4. Cada check deve exibir:
   - status `pass`, `warn` ou `fail`
   - alvo verificado
   - mensagem curta de diagnostico
   - proximo passo recomendado
5. O check `runtime_state` deve:
   - retornar `pass` quando o runtime estiver coerente e utilizavel
   - retornar `warn` quando o runtime estiver parado, mas o ambiente local continuar apto ao fluxo canonico sincrono
   - retornar `fail` quando o estado persistido do runtime estiver inconsistente
6. O check `runs_db` deve validar se o parent directory de `runs_db_path` existe ou pode ser criado e se permanece gravavel para o processo atual.
7. O check `artifacts_dir` deve validar se o parent directory de `artifacts_dir` existe ou pode ser criado e se permanece gravavel para o processo atual.
8. O status geral do doctor deve ser:
   - `pass` quando nao houver falhas bloqueantes
   - `fail` quando houver ao menos uma falha bloqueante
9. O comando deve retornar:
   - exit code `0` em estado geral `pass`, mesmo que haja `warn`
   - exit code `5` em estado geral `fail`

# Requisitos nao funcionais

- A implementacao deve permanecer pequena e localizada na camada de CLI e em helpers leves de diagnostico.
- O comando deve operar sem TTY e sem depender de Rich interativo.
- O doctor nao deve mutar o ambiente como efeito colateral necessario para diagnosticar.
- O recorte deve continuar suficiente para 1 a 3 dias de trabalho e nao deve substituir `repo-preflight`.

# Casos de erro

- `runtime_state.json` presente com PID/process identity incoerentes
- parent directory de `runs_db_path` indisponivel ou sem permissao de escrita
- parent directory de `artifacts_dir` indisponivel ou sem permissao de escrita
- paths configurados invalidos ou rejeitados pela protecao de runtime state
- excecao inesperada durante a coleta de um check

# Cenarios verificaveis

## Cenario 1: ambiente minimo saudavel

- Dado um ambiente local com paths configurados acessiveis
- E runtime parado de forma coerente
- Quando `aignt doctor` for executado
- Entao a CLI retorna exit code `0`
- E exibe status geral `pass`
- E exibe checks nomeados para `runtime_state`, `runs_db` e `artifacts_dir`
- E informa pelo menos um proximo passo objetivo

## Cenario 2: runtime inconsistente

- Dado um estado persistido de runtime inconsistente
- Quando `aignt doctor` for executado
- Entao a CLI retorna exit code `5`
- E o check `runtime_state` aparece como `fail`
- E a saida continua sem traceback cru

## Cenario 3: path nao gravavel para persistencia

- Dado um ambiente em que `runs_db_path` ou `artifacts_dir` nao pode ser preparado pelo processo atual
- Quando `aignt doctor` for executado
- Entao a CLI retorna exit code `5`
- E o check correspondente aparece como `fail`
- E a orientacao sugere corrigir permissao ou configuracao de path

# Observacoes

Esta frente diagnostica apenas os pre-requisitos locais minimos do fluxo publico atual, cujo caminho canonico continua sincrono e para em `SPEC_VALIDATION`. Se o projeto passar a exigir Docker, runtime persistente ativo ou credenciais externas como parte do fluxo oficial minimo, isso deve ser tratado em revisao explicita desta feature ou em frente propria, sem expandir a `F19` por inercia.

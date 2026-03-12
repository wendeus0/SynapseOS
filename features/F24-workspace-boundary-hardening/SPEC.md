---
id: F24-workspace-boundary-hardening
type: feature
summary: Endurecer o boundary de workspace e artifacts publicos em runs submit e runs show, impedindo leituras publicas fora das roots confiaveis sem alterar a superficie CLI.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - src/aignt_os/config.py
  - src/aignt_os/runtime/dispatch.py
  - src/aignt_os/cli/app.py
  - src/aignt_os/persistence.py
  - src/aignt_os/security.py
outputs:
  - workspace_boundary_guards
  - boundary_regression_tests
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "trabalhar apenas o recorte de G-05 + G-10 restante apos a F23"
  - "nao alterar schema SQLite ou adicionar migrations"
  - "nao alterar a superficie publica do CLI alem do endurecimento de erros de boundary"
  - "preservar `stdout_raw`, `stderr_raw`, `raw_output` e `raw.txt` intactos e fora de preview publico"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente nao depende de boot, ciclo de vida em container ou integracao real"
acceptance_criteria:
  - "Existe configuracao explicita em `AppSettings` para `workspace_root`, com default em `Path.cwd()` e override por ambiente."
  - "`RunDispatchService` aceita SPEC apenas quando o path resolvido fica dentro de `workspace_root`, persistindo `spec_path` canonicalizado em runs validas."
  - "`runs submit` trata SPEC fora de `workspace_root` ou via symlink de escape com o mesmo boundary publico de `Not found`, sem persistir a run."
  - "`runs show --preview report` e `runs show --preview <STEP_STATE>.clean` rejeitam qualquer path resolvido fora de `artifacts_dir`, inclusive quando o path vier do banco ou via symlink."
  - "`ArtifactStore.list_artifact_paths()` nao anuncia arquivos ou symlinks cujo destino resolvido escape `artifacts_dir`."
  - "Existe cobertura unitaria e de integracao para submit valido, SPEC fora da root, symlink de escape, preview bloqueado e listagem publica filtrada."
non_goals:
  - "introduzir campo `workspace` obrigatorio no schema de SPEC"
  - "retroagir artifacts ja persistidos no disco"
  - "alterar o contrato de preview para expor `raw.txt`"
  - "introduzir autenticacao, RBAC, audit trail, circuit breaker ou scanning AST"
security_notes:
  - "SPEC fora da root confiavel deve ser tratada como indisponivel para evitar disclosure do host"
  - "checagens de path devem usar canonicalizacao (`resolve`) antes de `relative_to`"
  - "listagem publica nao deve anunciar artifacts escapados mesmo que o preview posterior os bloqueie"
dependencies:
  - F15-public-run-submission
  - F17-artifact-preview
  - F21-cli-error-model-and-exit-codes
  - F23-security-sanitization-foundation
---

# Contexto

Depois da F23, o projeto passou a higienizar conteudo publico, mas ainda aceita e exibe caminhos com boundary parcial. `runs submit` hoje valida existencia e formato da SPEC, porem nao limita a origem do arquivo a uma raiz confiavel do workspace. `runs show --preview` ja canonicaliza alguns caminhos, mas a listagem publica de artifacts ainda pode anunciar entradas escapadas por symlink e a run continua aceitando `clean_output_path` persistido externamente ao diretório de artifacts.

No MVP, o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS e trabalha com um unico workspace local por run. A F24 fecha esse contrato de isolamento sem abrir migrations, auth ou runtime completo.

# Objetivo

Endurecer o boundary de workspace e artifacts publicos da CLI, aceitando SPEC apenas dentro de uma raiz confiavel do workspace e garantindo que previews/listagens publicas nunca leiam nem anunciem arquivos fora de `artifacts_dir`.

# Escopo

## Incluido

- `AppSettings.workspace_root` com default seguro para o MVP
- canonicalizacao de `spec_path` no dispatch antes de persistir a run
- rejeicao previsivel para SPEC fora de `workspace_root`
- helper compartilhado de boundary de path reutilizavel
- endurecimento de preview e listagem publica de artifacts contra symlink/path escape
- cobertura unitaria e de integracao para os cenarios acima
- `NOTES.md`, `CHECKLIST.md` e `REPORT.md` da feature

## Fora de escopo

- mudancas de schema SQLite
- novo campo `workspace` obrigatorio no validator da SPEC
- autenticacao/autorizacao
- Docker/runtime preflight
- saneamento retroativo de artifacts historicos

# Requisitos funcionais

1. O projeto deve expor uma raiz confiavel de workspace por configuracao.
2. O dispatch deve canonicalizar `spec_path` e rejeitar SPEC fora dessa root antes de criar ou executar runs.
3. O boundary publico de erro para SPEC fora da root deve ser equivalente ao caso de SPEC inexistente.
4. A listagem publica de artifacts deve filtrar entradas escapadas por symlink ou path resolvido fora de `artifacts_dir`.
5. O preview publico deve continuar restrito a `report` e `<STEP_STATE>.clean`.
6. Paths de preview vindos do banco ou filesystem devem ser canonicalizados contra `artifacts_dir` antes de leitura.
7. O contrato de outputs brutos versus limpos da F23 deve permanecer intacto.

# Requisitos nao funcionais

- o recorte deve permanecer pequeno e reversivel
- as checagens de boundary devem reutilizar helper compartilhado em vez de duplicar `resolve().relative_to(...)`
- o CLI deve continuar com os exit codes publicos ja consolidados na F21
- a feature nao deve exigir mudanca arquitetural ou ADR nova

# Casos de erro

- SPEC fora de `workspace_root`
- SPEC via symlink que resolve fora de `workspace_root`
- preview apontando para artifact fora de `artifacts_dir`
- listagem contendo symlink que resolve fora de `artifacts_dir`
- `clean_output_path` persistido no banco apontando para fora da root de artifacts

# Cenarios verificaveis

## Cenario 1: submit aceita SPEC interna e canonicaliza o path

- Dado uma SPEC valida dentro de `workspace_root`
- Quando `runs submit` ou `RunDispatchService.dispatch()` forem executados
- Entao a run e criada normalmente
- E `spec_path` e persistido como path canonicalizado

## Cenario 2: submit rejeita SPEC fora da root

- Dado uma SPEC valida fora de `workspace_root`
- Quando o dispatch for executado
- Entao a run nao e persistida
- E o boundary publico de erro e `Not found`

## Cenario 3: preview e listagem nao escapam artifacts root

- Dado um artifact ou `clean_output_path` que resolve fora de `artifacts_dir`
- Quando `runs show` listar ou previsualizar artifacts
- Entao o arquivo escapado nao aparece na listagem publica
- E qualquer tentativa de preview retorna `Not found` sem expor conteudo externo

# Observacoes

Esta feature fecha o endurecimento de boundary de paths do backlog de guardrails sem reabrir a fundacao textual da F23. `G-03` em diante continuam em features posteriores da IDEA-001.

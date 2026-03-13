---
id: F39-persistence-path-root-hardening
type: feature
summary: Endurecer os paths de persistencia de runs e artifacts para a raiz confiavel do workspace.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - src/aignt_os/config.py
  - src/aignt_os/cli/app.py
  - src/aignt_os/runtime/worker.py
  - src/aignt_os/cli/dashboard.py
  - tests/unit/test_config.py
  - tests/integration/test_runs_submit_cli.py
  - tests/integration/test_runs_cli.py
  - tests/integration/test_doctor_cli.py
outputs:
  - trusted_persistence_paths
  - persistence_boundary_red_tests
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "restringir a frente a `runs_db_path` e `artifacts_dir`, sem tocar TUI como produto, auth remota ou transporte"
  - "preservar a CLI publica atual, mudando apenas o erro configuracional para paths de persistencia fora da raiz confiavel"
  - "nao exigir DOCKER_PREFLIGHT porque a frente nao depende de Docker, build, boot em container ou integracao externa"
acceptance_criteria:
  - "`AIGNT_OS_RUNS_DB_PATH` passa a resolver apenas para um path canonico dentro de `workspace_root`, rejeitando escapes por path absoluto fora da raiz ou por symlink."
  - "`AIGNT_OS_ARTIFACTS_DIR` passa a resolver apenas para um path canonico dentro de `workspace_root`, rejeitando escapes por path absoluto fora da raiz ou por symlink."
  - "`aignt runs submit`, `aignt runs list` e `aignt runs show` falham com `Environment error:` previsivel quando o banco ou artifacts configurados escapam da raiz confiavel."
  - "`aignt doctor` marca `runs_db` e `artifacts_dir` como `fail` sem traceback quando a configuracao de persistencia escapa do `workspace_root`."
  - "Existe cobertura unitaria e de integracao para configuracao valida, path invalido fora do workspace e escape por symlink."
non_goals:
  - "alterar `runtime_state_dir`, que ja foi endurecido na F38"
  - "mudar a experiencia visual da TUI ou ampliar watch mode"
  - "introduzir migracao de schema, nova persistencia ou mudancas de produto fora do boundary de path"
dependencies:
  - F24-workspace-boundary-hardening
  - F38-runtime-state-root-hardening
---

# Contexto

O projeto ja protege alguns boundaries de filesystem com `workspace_root`, inclusive SPECs,
artifacts salvos por run e o state-dir compartilhado do runtime. Ainda faltava alinhar os
dois pontos centrais de persistencia configuravel: `runs_db_path` e `artifacts_dir`.

Essa lacuna permite que a configuracao aponte para um banco SQLite ou diretorio de artifacts
fora da raiz confiavel do workspace, o que quebra a consistencia do boundary operacional do
AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS.

# Objetivo

Aplicar o mesmo boundary confiavel de `workspace_root` aos paths configuraveis de banco de
runs e diretório base de artifacts, mantendo erros previsiveis na CLI e sem ampliar escopo.

# Escopo

## Incluido

- adicionar accessors resolvidos em `AppSettings` para banco de runs e diretório de artifacts
- atualizar os consumidores principais de persistencia para usar apenas paths resolvidos
- falhar cedo com `Environment error:` nas CLIs publicas quando a configuracao escapar da raiz confiavel
- ajustar fixtures de integracao que antes usavam paths fora do `workspace_root`

## Fora de escopo

- mudar `runtime_state_dir` ou auth registry
- alterar o comportamento visual da TUI
- migracao de schema SQLite, novo layout de artifacts ou novas features de observabilidade

# Casos de erro

- `runs_db_path` absoluto fora de `workspace_root` continuar aceito
- `artifacts_dir` symlinkado dentro do workspace escapar para target externo
- `runs list` ou `runs show` exibirem traceback cru em vez de erro de ambiente previsivel
- `doctor` continuar marcando ambiente como saudavel quando a persistencia configurada escapa da raiz

# Cenarios verificaveis

## Cenario 1: paths validos seguem funcionais

- Dado `workspace_root` configurado para o diretório temporario do teste
- E `runs_db_path` e `artifacts_dir` configurados dentro dessa raiz
- Quando a configuracao for resolvida
- Entao a persistencia continua funcional sem mudar a superficie publica

## Cenario 2: banco fora da raiz confiavel e rejeitado

- Dado `workspace_root` configurado
- E `runs_db_path` apontando para um path absoluto fora dessa raiz
- Quando `aignt runs submit` ou `aignt runs list` forem executados
- Entao a CLI falha com `Environment error:` previsivel

## Cenario 3: artifacts nao permitem escape por symlink

- Dado `artifacts_dir` configurado como symlink dentro do workspace
- E o target real apontando para fora da raiz confiavel
- Quando a configuracao for resolvida ou consumida pela CLI
- Entao o path e rejeitado como escape do root confiável

# Observacoes

Esta frente endurece apenas o boundary de configuracao para persistencia local de runs e
artifacts. Ela nao reabre a frente visual da TUI, nao altera runtime remoto e nao mexe em
schema de dados existente.

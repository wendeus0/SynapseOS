---
id: F38-runtime-state-root-hardening
type: feature
summary: Endurecer o diretório de estado compartilhado do runtime para uma raiz confiável do workspace.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - src/aignt_os/config.py
  - src/aignt_os/runtime/state.py
  - src/aignt_os/auth.py
  - src/aignt_os/runtime/circuit_breaker.py
  - src/aignt_os/cli/app.py
outputs:
  - trusted_runtime_state_root
  - state_dir_hardening_red_tests
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "restringir a frente ao state-dir compartilhado de runtime/auth/circuit-breaker; sem tocar TUI, socket, IPC ou transporte remoto"
  - "preservar a CLI publica atual, mudando apenas o erro configuracional para state-dir fora da raiz confiável"
  - "nao exigir DOCKER_PREFLIGHT porque a frente nao depende de Docker, build, boot em container ou integracao externa"
acceptance_criteria:
  - "`AIGNT_OS_RUNTIME_STATE_DIR` passa a resolver apenas para um path canonico dentro de `workspace_root`, rejeitando escapes por path absoluto fora da raiz ou por symlink."
  - "`runtime_state_file`, `auth_registry_file` e `adapter_circuit_breaker_state_file` passam a herdar o mesmo boundary confiável."
  - "`aignt runtime start` e `aignt auth init` falham com erro configuracional previsivel quando o state-dir configurado escapa da raiz confiável."
  - "A configuracao valida atual continua funcionando quando `AIGNT_OS_WORKSPACE_ROOT` aponta para a raiz usada nos testes e no fluxo local."
  - "Existe cobertura unitaria e de integracao para configuracao valida, path invalido fora do workspace e escape por symlink."
non_goals:
  - "alterar `runs_db_path` ou `artifacts_dir`"
  - "mudar o contrato de `runs submit`, `runtime run` ou da TUI em desenvolvimento paralelo"
  - "abrir auth remota, multi-host ou novo contrato de configuracao"
dependencies:
  - F24-workspace-boundary-hardening
  - F37-post-f36-g11-sync
---

# Contexto

O baseline atual ja endureceu paths de SPEC e artifacts contra escapes do workspace, mas o
diretorio compartilhado de estado do runtime ainda usa validacao basica. `runtime-state.json`,
`auth-registry.json` e `adapter-circuit-breakers.json` vivem sob `runtime_state_dir`, e hoje
esse path ainda pode ser configurado de forma menos restrita do que os demais boundaries.

Como a TUI esta sendo desenvolvida em outra frente, o proximo recorte nao conflitante e um
hardening pequeno e local do state-dir compartilhado, sem tocar watch mode, dashboard ou
outras superficies de UX.

# Objetivo

Restringir explicitamente o state-dir compartilhado do runtime a uma raiz confiável do
workspace, reutilizando canonicalizacao de path ja existente e mantendo erros previsiveis na CLI.

# Escopo

## Incluido

- validar `runtime_state_dir` contra `workspace_root` em path canonico
- fazer `runtime_state_file`, `auth_registry_file` e `adapter_circuit_breaker_state_file` herdarem o mesmo boundary
- ajustar a CLI para devolver erro de ambiente previsivel quando o state-dir for invalido
- atualizar fixtures/envs de teste que usam `tmp_path` como workspace confiável

## Fora de escopo

- qualquer mudanca de TUI, dashboard ou watch mode
- alteracao de `runs_db_path` ou `artifacts_dir`
- qualquer transporte autenticado entre processos ou hosts

# Casos de erro

- `runtime_state_dir` absoluto fora de `workspace_root` continuar aceito
- symlink dentro do workspace escapar para um target fora da raiz confiável
- `aignt auth init` gerar traceback em vez de erro previsivel para state-dir invalido
- fixtures atuais de runtime falharem por nao declarar `workspace_root`

# Cenarios verificaveis

## Cenario 1: state-dir valido segue funcional

- Dado `workspace_root` configurado para o diretório temporario do teste
- E `runtime_state_dir` configurado dentro dessa raiz
- Quando a configuracao for resolvida
- Entao os arquivos derivados do state-dir permanecem validos e funcionais

## Cenario 2: state-dir fora da raiz confiável e rejeitado

- Dado `workspace_root` configurado
- E `runtime_state_dir` apontando para path absoluto fora dessa raiz
- Quando a CLI de runtime ou auth for executada
- Entao ela falha com erro de ambiente previsivel

## Cenario 3: symlink nao permite escape

- Dado um `runtime_state_dir` que e um symlink dentro do workspace
- E o target real aponta para fora da raiz confiável
- Quando a configuracao for resolvida
- Entao o path e rejeitado como escape do root confiável

# Observacoes

Esta frente endurece apenas o diretório de estado compartilhado do runtime. Ela nao altera
o boundary de banco, artifacts ou qualquer fluxo de observabilidade/TUI em desenvolvimento
paralelo.

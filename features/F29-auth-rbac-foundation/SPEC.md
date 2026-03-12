---
id: F29-auth-rbac-foundation
type: feature
summary: Introduzir autenticacao opt-in com RBAC estrutural para comandos mutaveis da CLI, sem abrir socket nem gerenciamento completo de credenciais.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - src/aignt_os/cli/app.py
  - src/aignt_os/cli/errors.py
  - src/aignt_os/config.py
  - src/aignt_os/runtime/dispatch.py
  - src/aignt_os/persistence.py
outputs:
  - auth_rbac_contract
  - cli_auth_guards
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "trabalhar apenas o menor recorte util de G-11 no baseline atual"
  - "proteger apenas `runs submit` e `runtime start|run|stop` nesta frente"
  - "manter leitura local (`doctor`, `version`, `runs list|show`, `runtime status|ready`) sem token"
  - "nao introduzir socket, daemon remoto, RBAC distribuido, SQLite nova ou gerenciamento de usuarios"
  - "ativar enforcement apenas por opt-in de configuracao, preservando o baseline atual por default"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente nao depende de boot em container ou integracao externa"
acceptance_criteria:
  - "AppSettings expoe `auth_enabled: bool = False` e o path derivado `auth_registry_file` sob `runtime_state_dir`."
  - "Existe um registry local em arquivo JSON com escrita atomica e permissoes restritas para principals e tokens por hash SHA-256, sem persistir token em claro."
  - "Quando `auth_enabled=false`, o comportamento atual da CLI publica permanece inalterado."
  - "Quando `auth_enabled=true`, `runs submit` e `runtime start|run|stop` exigem autenticacao via `--auth-token` com fallback em `AIGNT_OS_AUTH_TOKEN`."
  - "A CLI diferencia falha de autenticacao (`Authentication error:`, exit code `7`) e falha de autorizacao (`Authorization error:`, exit code `8`)."
  - "O papel `viewer` continua restrito a leitura e o papel `operator` permite `runs.submit` e `runtime.manage`."
  - "Um submit autenticado com sucesso persiste `initiated_by` com o `principal_id` autenticado em vez de `local_cli`."
  - "Existe cobertura unitaria e de integracao para registry, permissao por papel, comandos mutaveis protegidos e nao-regressao do baseline com auth desabilitada."
non_goals:
  - "expor socket, handshake remoto ou transporte autenticado novo"
  - "criar CLI para provisionar, rotacionar ou revogar tokens"
  - "exigir autenticacao para comandos de leitura local"
  - "introduzir politicas dinamicas, hierarquia ampla de roles ou coordenacao entre hosts"
security_notes:
  - "persistir apenas hash SHA-256 do token, nunca o token bruto"
  - "falhar em modo fail-closed para comandos protegidos quando auth estiver habilitada e o registry estiver ausente ou corrompido"
  - "nao vazar token, hash ou payload completo do registry em mensagens de erro"
dependencies:
  - F15-public-run-submission
  - F21-cli-error-model-and-exit-codes
  - F26-run-provenance-integrity
---

# Contexto

Depois da `F28`, o backlog remanescente da `IDEA-001` ficou concentrado em `G-11`: autenticacao e autorizacao. No baseline atual, a CLI publica do AIgnt OS ja expoe `runs submit`, `runs list`, `runs show`, `doctor` e o grupo `runtime`, enquanto o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS. Porem, ainda nao existe qualquer camada de auth local, e a ideia original menciona `socket + RBAC`, algo grande demais para abrir diretamente no MVP atual.

O menor recorte util e coerente com o estado real do repositorio e introduzir uma base opt-in de autenticacao com RBAC estrutural apenas na CLI local. Isso permite endurecer os comandos mutaveis agora, reaproveitar `initiated_by` para provenance e evitar abrir transporte novo antes da hora.

# Objetivo

Adicionar uma fundacao local de autenticacao e autorizacao para a CLI do AIgnt OS, com registry privado de credentials por hash, papeis estaticos (`viewer` e `operator`) e enforcement apenas nos comandos mutaveis atuais, preservando o baseline existente quando auth estiver desabilitada.

# Escopo

## Incluido

- registry local de auth em arquivo JSON privado
- modelos/contratos para principal, token hash e roles
- enforcement opt-in em `runs submit` e `runtime start|run|stop`
- fallback de token por `--auth-token` ou `AIGNT_OS_AUTH_TOKEN`
- extensao do contrato publico de erro da CLI para authn/authz
- wiring de `principal_id` em `initiated_by` para submit autenticado
- testes unitarios e de integracao para auth/RBAC
- `NOTES.md`, `CHECKLIST.md` e `REPORT.md` proprios da feature

## Fora de escopo

- socket autenticado
- RBAC remoto/distribuido
- cadastro/rotacao de token via subcomando
- enforcement em comandos de leitura
- policy engine generica alem do necessario para o baseline atual

# Requisitos funcionais

1. O sistema deve permitir habilitar auth por configuracao sem alterar o baseline default.
2. O registry deve associar token hash a um principal e a um conjunto pequeno de roles.
3. O sistema deve suportar pelo menos os papeis `viewer` e `operator`.
4. `runs submit` deve exigir autenticacao quando auth estiver habilitada.
5. `runtime start`, `runtime run` e `runtime stop` devem exigir autenticacao quando auth estiver habilitada.
6. `doctor`, `version`, `runs list`, `runs show`, `runtime status` e `runtime ready` devem permanecer acessiveis sem token.
7. Falha de token ausente/invalido deve retornar erro publico de autenticacao.
8. Falha de papel insuficiente deve retornar erro publico de autorizacao.
9. Submit autenticado com sucesso deve persistir o `principal_id` autenticado em `initiated_by`.

# Requisitos nao funcionais

- a feature deve caber em 1 a 3 dias
- o registry deve reutilizar o padrao de escrita atomica e permissoes privadas do runtime state
- a implementacao deve ficar restrita ao baseline CLI-first atual
- a mudanca deve permanecer reversivel e sem ADR nova

# Casos de erro

- auth habilitada com registry ausente
- auth habilitada com registry corrompido
- token ausente em comando protegido
- token invalido
- token valido com role insuficiente
- role desconhecida no registry

# Cenarios verificaveis

## Cenario 1: baseline permanece aberto por default

- Dado `auth_enabled=false`
- Quando `runs submit` e `runtime start` forem executados
- Entao o comportamento atual permanece inalterado
- E nenhum token e exigido

## Cenario 2: autenticacao protege submit

- Dado `auth_enabled=true` e um registry valido
- Quando `runs submit` for executado sem token ou com token invalido
- Entao a CLI retorna `Authentication error:`
- E usa exit code `7`

## Cenario 3: autorizacao bloqueia papel insuficiente

- Dado `auth_enabled=true` e um principal `viewer`
- Quando `runs submit` ou `runtime start` for executado com esse token
- Entao a CLI retorna `Authorization error:`
- E usa exit code `8`

## Cenario 4: operator autentica submit e registra provenance

- Dado `auth_enabled=true` e um principal `operator`
- Quando `runs submit` for executado com token valido
- Entao a run e aceita normalmente
- E `initiated_by` persiste o `principal_id` autenticado

# Observacoes

Esta frente fecha apenas a fundacao local de auth/RBAC para a CLI atual. Socket, handshake remoto, revogacao de tokens, auditoria expandida e politicas mais amplas continuam fora para manter o repositorio fiel ao modelo spec-first, feature-by-feature e uma frente por vez.

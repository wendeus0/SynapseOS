---
id: F25-generated-artifact-ast-guard
type: feature
summary: Bloquear a promocao de artifacts Python inseguros via validacao AST antes da persistencia publica, cobrindo o guardrail G-03 sem ampliar o escopo arquitetural.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - src/aignt_os/parsing.py
  - src/aignt_os/persistence.py
  - src/aignt_os/pipeline.py
outputs:
  - ast_guard_validation
  - artifact_promotion_guard
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "trabalhar apenas o recorte de G-03"
  - "nao alterar schema SQLite ou adicionar migrations"
  - "nao alterar a superficie publica do CLI alem do comportamento ja audivel de falha da run"
  - "manter F23 e F24 intactas: sanitizacao textual e boundary de path nao podem regredir"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente nao depende de boot, ciclo de vida em container ou integracao real"
acceptance_criteria:
  - "Existe validacao AST reutilizavel para artifacts Python que rejeita `eval`, `exec`, `os.system` e chamadas `subprocess.*(..., shell=True)`."
  - "A validacao cobre aliases simples de `os` e `subprocess`, inclusive `import os as x`, `import subprocess as sp` e `from subprocess import run as r`."
  - "A promocao de named artifacts Python e bloqueada antes da persistencia publica quando o codigo for inseguro."
  - "Artifacts nao-Python continuam sendo persistidos sem passar pelo scanner AST."
  - "Existe cobertura unitaria e de integracao para artifact Python seguro, artifact Python inseguro, alias simples e ausencia de persistencia quando o guardrail dispara."
non_goals:
  - "introduzir sandboxing, execucao isolada ou policy engine mais ampla"
  - "bloquear APIs alem da denylist minima decidida para o MVP"
  - "introduzir metadata nova por artifact ou alteracoes de schema"
  - "tratar markdown, shell scripts ou outras linguagens como alvo do scanner desta feature"
security_notes:
  - "o guardrail deve impedir que artifact Python inseguro seja promovido a artifact persistido e publicamente listavel"
  - "o enforcement principal deve ocorrer no caminho de persistencia do produto, nao apenas em helper isolado"
  - "a checagem defensiva em `ArtifactStore` deve evitar bypass por chamada direta"
dependencies:
  - F23-security-sanitization-foundation
  - F24-workspace-boundary-hardening
---

# Contexto

Depois de endurecer conteudo publico na F23 e boundary de paths na F24, o proximo gap prioritario da IDEA-001 fica na promocao de artifact Python gerado por agentes. O projeto ja valida sintaxe Python em `validate_python_artifact()`, mas essa validacao ainda nao impede que codigo perigoso seja promovido e persistido como named artifact publico.

No estado atual do produto, o caminho util de promocao passa por `PipelinePersistenceObserver.on_step_completed()` e `ArtifactStore.save_named_artifact()`. Se o guardrail ficar apenas no parsing, ele continua fora do caminho efetivo que grava o artifact em disco e o torna listavel pela CLI.

# Objetivo

Bloquear a promocao de artifacts Python inseguros antes da persistencia publica, usando validacao AST minima e reutilizavel, sem ampliar o escopo para sandboxing, execucao real ou novas estruturas arquiteturais.

# Escopo

## Incluido

- evolucao de `validate_python_artifact()` para sintaxe + denylist AST
- suporte a aliases simples de `os` e `subprocess`
- enforcement no caminho de persistencia do produto antes da escrita do named artifact
- checagem defensiva adicional no `ArtifactStore`
- cobertura unitaria e de integracao para promocao segura e bloqueada
- `NOTES.md`, `CHECKLIST.md` e `REPORT.md` da feature

## Fora de escopo

- migrations SQLite
- novos eventos persistidos ou audit trail dedicado
- sandboxing de execucao
- scanner amplo para filesystem, rede ou outras linguagens
- alteracao do contrato publico de CLI alem da falha auditavel da run

# Requisitos funcionais

1. O projeto deve reconhecer artifacts Python por nome logico claro (`.py`, `_py`, `_python`).
2. O helper AST deve rejeitar `eval`, `exec`, `os.system` e `subprocess.*(..., shell=True)`.
3. O helper deve resolver aliases simples de import para `os` e `subprocess`.
4. A promocao de artifact Python inseguro deve falhar antes da escrita em disco.
5. Artifacts nao-Python nao devem ser impactados por esse guardrail.
6. O caminho de falha deve permanecer auditavel via status/eventos normais da run.

# Requisitos nao funcionais

- o recorte deve permanecer pequeno e reversivel
- a validacao AST deve ser deterministica e baseada apenas em analise estatica local
- o enforcement deve ocorrer no caminho de persistencia do produto, com defesa em profundidade
- a feature nao deve exigir ADR nova

# Casos de erro

- artifact Python com `eval`
- artifact Python com `exec`
- artifact Python com `os.system`
- artifact Python com `subprocess.*(..., shell=True)`
- artifact Python com aliases simples dessas chamadas

# Cenarios verificaveis

## Cenario 1: artifact Python seguro e promovido

- Dado um artifact `code_py` com codigo Python valido e sem patterns bloqueados
- Quando a persistencia do step promover o artifact
- Entao o arquivo e gravado normalmente

## Cenario 2: artifact Python inseguro e bloqueado

- Dado um artifact `code_py` com `eval`, `exec`, `os.system` ou `subprocess(..., shell=True)`
- Quando a persistencia do step tentar promover o artifact
- Entao a promocao falha antes da escrita em disco
- E a run fica auditavel como falha do fluxo normal

## Cenario 3: artifacts nao-Python seguem intactos

- Dado um artifact `plan_md` ou outro artifact nao-Python
- Quando a persistencia do step ocorrer
- Entao a promocao nao passa pelo guardrail AST de Python

# Observacoes

Esta feature cobre apenas a denylist AST minima com aliases simples, deliberadamente menor que um scanner amplo. Integridade da SPEC, audit trail, rate limiting, circuit breaker e autenticacao continuam em frentes posteriores.

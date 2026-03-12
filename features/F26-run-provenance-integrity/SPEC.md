---
id: F26-run-provenance-integrity
type: feature
summary: Persistir provenance minimo de runs com hash SHA-256 da SPEC, initiated_by e security events reutilizaveis, cobrindo G-06 e G-08 sem ampliar o escopo arquitetural.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - src/aignt_os/runtime/dispatch.py
  - src/aignt_os/persistence.py
  - src/aignt_os/reporting.py
outputs:
  - run_provenance_persistence
  - security_audit_trail
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "trabalhar apenas o recorte de G-06 e G-08"
  - "nao introduzir Alembic ou infraestrutura nova de migration"
  - "nao alterar a CLI publica alem da exposicao de provenance em runs show e RUN_REPORT.md"
  - "manter F23, F24 e F25 intactas: sanitizacao, boundary e AST guard nao podem regredir"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente nao depende de boot, ciclo de vida em container ou integracao real"
acceptance_criteria:
  - "RunRecord passa a persistir `spec_hash` e `initiated_by`, incluindo upgrade local de schema para bases SQLite existentes."
  - "A criacao de runs persiste `spec_hash` como SHA-256 do arquivo canonizado e `initiated_by` como origem explicita da submissao."
  - "Runs pendentes revalidam o hash da SPEC antes da execucao; se a SPEC mudar apos o submit, a run falha em `REQUEST` com event type `security_spec_hash_mismatch`."
  - "O audit trail passa a registrar `security_provenance_recorded` para novas runs e `security_guardrail_triggered` para falhas de guardrail mapeadas."
  - "Existe cobertura unitaria e de integracao para schema legado, persistence de provenance, tampering de SPEC, rendering de `runs show` e RUN_REPORT.md com os novos campos."
non_goals:
  - "introduzir autenticacao, RBAC, rate limiting ou circuit breaker"
  - "criar tabela nova, audit trail dedicado ou infraestrutura Alembic"
  - "mudar runs list, preview de artifacts ou o contrato publico de erro da CLI"
  - "expandir security events para todas as categorias de falha fora das explicitamente mapeadas nesta frente"
security_notes:
  - "o hash da SPEC deve proteger runs pendentes contra alteracao do arquivo entre submit e execucao"
  - "security events devem reutilizar o sistema atual de run_events sem criar canal paralelo"
  - "o initiated_by deve ser explicito para novas runs e receber default seguro para caminhos internos"
dependencies:
  - F23-security-sanitization-foundation
  - F24-workspace-boundary-hardening
  - F25-generated-artifact-ast-guard
---

# Contexto

Depois de fechar sanitizacao publica na F23, boundary de workspace na F24 e AST guard na F25, o proximo gap de seguranca da IDEA-001 fica na rastreabilidade da run. Hoje o AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS, persiste `spec_path`, steps e events, mas ainda nao registra quem iniciou a run nem garante que a SPEC consumida pelo worker continua identica ao arquivo validado no submit.

Esse gap aparece com mais clareza no runtime dual: uma run pode ser enfileirada em `async`, a SPEC pode ser alterada no workspace antes do worker consumi-la e o sistema atual nao deixa evidencias suficientes para auditoria posterior. A mesma superficie tambem limita a explicacao de falhas de guardrail ja existentes, porque o audit trail atual se resume a `run_failed` e `supervisor_decision`.

# Objetivo

Persistir provenance minimo por run usando hash SHA-256 da SPEC, `initiated_by` e security events reutilizaveis, sem introduzir infraestrutura nova de migrations, auth ou audit trail paralelo.

# Escopo

## Incluido

- extensao do `RunRecord` com `spec_hash` e `initiated_by`
- evolucao local de schema SQLite dentro do `RunRepository`
- calculo e persistencia do SHA-256 da SPEC validada
- revalidacao do hash quando a run pendente for retomada
- novos event types `security_provenance_recorded`, `security_spec_hash_mismatch` e `security_guardrail_triggered`
- exposicao de provenance em `runs show` e `RUN_REPORT.md`
- `NOTES.md`, `CHECKLIST.md` e `REPORT.md` da feature

## Fora de escopo

- Alembic ou pasta de migrations dedicada
- autenticacao, principals ou RBAC
- rate limiting, circuit breaker ou novos guardrails de adapters
- nova tabela de auditoria ou esquema de eventos tipados fora de `run_events`
- mudancas no `runs list`

# Requisitos funcionais

1. O repositório deve aceitar bases SQLite existentes e adicionar `spec_hash` e `initiated_by` sem apagar dados.
2. Toda nova run deve persistir `spec_hash` e `initiated_by` no momento da criacao.
3. `spec_hash` deve ser calculado sobre os bytes da SPEC canonizada em disco.
4. Runs pendentes devem revalidar o hash antes de o worker iniciar a pipeline.
5. Se a SPEC tiver sido alterada apos o submit, a run deve falhar ainda em `REQUEST`.
6. `runs show` e `RUN_REPORT.md` devem exibir `Spec Hash` e `Initiated By`.
7. Falhas de guardrail explicitamente mapeadas nesta frente devem gerar `security_guardrail_triggered` antes de `run_failed`.

# Requisitos nao funcionais

- o recorte deve permanecer pequeno e reversivel
- a migration deve ser leve e autocontida no runtime atual
- o audit trail deve continuar legivel via CLI-first e sem nova superficie publica
- a feature nao deve exigir ADR nova

# Casos de erro

- base SQLite antiga sem as novas colunas
- SPEC removida antes de a run pendente ser consumida
- SPEC alterada depois do submit e antes do worker
- falha de guardrail AST ja existente disparando audit trail adicional

# Cenarios verificaveis

## Cenario 1: provenance persistida no submit

- Dado um submit valido
- Quando a run for criada em `sync` ou `async`
- Entao `spec_hash` e `initiated_by` ficam persistidos no `RunRecord`
- E um evento `security_provenance_recorded` e registrado

## Cenario 2: tampering de SPEC bloqueia run pendente

- Dado uma run `async` criada com SPEC valida
- Quando o arquivo da SPEC for alterado antes de o worker consumir a run
- Entao a run falha em `REQUEST`
- E o audit trail registra `security_spec_hash_mismatch`

## Cenario 3: guardrail mapeado gera security event

- Dado uma run que dispara o guardrail da F25
- Quando a persistencia reprovar o artifact inseguro
- Entao o audit trail registra `security_guardrail_triggered`
- E a falha continua auditavel pelo fluxo normal da run

## Cenario 4: legado continua legivel

- Dado um banco SQLite antigo sem `spec_hash` e `initiated_by`
- Quando o repositorio for inicializado
- Entao o schema e atualizado localmente
- E runs antigas continuam legiveis com defaults de compatibilidade

# Observacoes

Esta feature fecha apenas provenance minima e audit trail essencial da IDEA-001. Auth, rate limiting, circuit breaker e um sistema formal de migrations continuam em frentes posteriores para manter o repositório fiel ao modelo spec-first, feature-by-feature e uma frente por vez.

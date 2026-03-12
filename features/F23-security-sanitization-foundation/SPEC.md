---
id: F23-security-sanitization-foundation
type: feature
summary: Introduzir a fundacao compartilhada de sanitizacao de seguranca para outputs limpos e artefatos publicos, cobrindo strip de bidi controls, normalizacao NFKC e masking de segredos sem alterar outputs brutos.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - src/aignt_os/config.py
  - src/aignt_os/adapters.py
  - src/aignt_os/parsing.py
  - src/aignt_os/persistence.py
outputs:
  - security_sanitization_module
  - security_sanitization_tests
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "trabalhar apenas o recorte de G-01, G-02 e G-04"
  - "preservar `stdout_raw`, `stderr_raw`, `raw_output` e qualquer output bruto intactos"
  - "aplicar strip de bidi controls, normalizacao NFKC e masking apenas em campos `*_clean` e artefatos publicos"
  - "introduzir um modulo compartilhado de seguranca em vez de duplicar regexes e helpers"
  - "nao alterar schema SQLite, migrations, worker, rate limiting, circuit breaker ou autenticacao"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente nao depende de boot, ciclo de vida, persistencia operacional em container ou integracao real"
acceptance_criteria:
  - "Existe um modulo compartilhado de seguranca reutilizavel por adapters, parsing e persistencia publica, concentrando strip de bidi controls, normalizacao Unicode NFKC e masking configuravel de segredos."
  - "`CLIExecutionResult.stdout_clean` e `stderr_clean` removem sequencias ANSI, stripam bidi controls, normalizam texto em NFKC e mascaram segredos, sem alterar `stdout_raw` e `stderr_raw`."
  - "`ParsedOutput.stdout_clean` recebe strip de bidi controls, normalizacao NFKC e masking de segredos, sem alterar `stdout_raw` e sem quebrar a extracao de artifacts."
  - "`ArtifactStore` aplica masking apenas a `clean_output`, named artifacts publicos e `RUN_REPORT.md`, preservando `raw.txt` intacto."
  - "Existe configuracao explicita em `AppSettings` para padroes de masking de segredos, com defaults seguros e extensibilidade por ambiente."
  - "Existe pelo menos um teste unitario cobrindo strip de bidi controls e normalizacao NFKC, pelo menos um teste unitario cobrindo masking em campos `*_clean`, e pelo menos um teste de integracao cobrindo que preview publico nao expoe segredo persistido."
non_goals:
  - "AST scanning de artefatos Python gerados por IA"
  - "migrations SQLite, `spec_hash`, `initiated_by` ou security events"
  - "rate limiting, circuit breaker ou qualquer resiliencia de adapter alem da sanitizacao"
  - "autenticacao, RBAC, socket auth ou controle de principals"
  - "mascaramento retroativo de artifacts historicos ja persistidos no disco"
security_notes:
  - "o masking deve atuar sobre segredos reconhecidos em superficies legiveis/publicas sem destruir a trilha bruta necessaria para diagnostico controlado"
  - "bidi controls e normalizacao Unicode devem ser tratados como higiene de seguranca antes da exibicao e persistencia de campos limpos"
  - "qualquer ampliacao para scanning AST, audit trail ou auth fica fora desta feature e deve virar frente propria"
dependencies:
  - F12-codex-adapter-operational-hardening
  - F17-artifact-preview
  - F21-cli-error-model-and-exit-codes
---

# Contexto

Depois do fechamento da etapa 2, o AIgnt OS ja expoe uma superficie publica CLI-first com submit, diagnostico, detail, preview e release readiness, enquanto o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS. Porem, a IDEA-001 registrou que ainda faltam guardrails basicos de sanitizacao antes de avancar para endurecimentos maiores.

Os riscos mais imediatos neste recorte sao:

- controles bidi e variacoes Unicode que tornam o texto limpo visualmente enganoso;
- segredos persistidos ou exibidos em campos `*_clean` e artefatos publicos;
- duplicacao tecnica de regexes e sanitizacao leve entre adapters e parsing.

A F23 existe para criar a fundacao compartilhada de sanitizacao de seguranca sem abrir migrations, auth ou outras frentes estruturais do backlog.

# Objetivo

Entregar a fundacao compartilhada de sanitizacao de seguranca do projeto, cobrindo strip de bidi controls, normalizacao Unicode NFKC e masking configuravel de segredos em campos `*_clean` e artefatos publicos, preservando outputs brutos intactos.

# Escopo

## Incluido

- novo modulo compartilhado de seguranca reutilizavel por adapters, parsing e persistencia publica
- strip de bidi controls em superficies limpas
- normalizacao Unicode NFKC em superficies limpas
- masking configuravel de segredos em `stdout_clean`, `stderr_clean`, `clean_output`, named artifacts publicos e `RUN_REPORT.md`
- extensao minima de configuracao em `AppSettings`
- testes unitarios e de integracao cobrindo o contrato acima
- `NOTES.md`, `CHECKLIST.md` e `REPORT.md` da feature

## Fora de escopo

- AST scanning de artefatos Python
- migrations SQLite
- audit trail de seguranca
- rate limiting ou circuit breaker
- autenticacao e autorizacao
- rotacao, revogacao ou descoberta de segredos fora do masking textual

# Requisitos funcionais

1. O projeto deve expor um helper compartilhado de seguranca para sanitizacao textual.
2. Esse helper deve permitir strip de bidi controls sem alterar o output bruto original.
3. Esse helper deve aplicar normalizacao Unicode NFKC em superficies limpas.
4. Esse helper deve mascarar padroes de segredo configurados em `AppSettings`.
5. `BaseCLIAdapter` deve continuar preservando `stdout_raw` e `stderr_raw`, mas endurecer `stdout_clean` e `stderr_clean` com o helper compartilhado.
6. O parsing deve continuar preservando `stdout_raw`, mas endurecer `stdout_clean` com o helper compartilhado sem quebrar a extracao atual de artifacts.
7. O `ArtifactStore` deve preservar `raw.txt` intacto e aplicar masking apenas a `clean.txt`, named artifacts publicos e `RUN_REPORT.md`.
8. A feature nao deve alterar schema, contratos de persistencia relacional nem o fluxo da state machine.

# Requisitos nao funcionais

- o recorte deve permanecer pequeno e reversivel
- a implementacao deve manter baixo acoplamento entre config, parsing, adapters e persistencia
- o contrato de outputs brutos vs. limpos deve permanecer explicito
- a fundacao criada aqui deve ser reutilizavel pelas frentes futuras de guardrails sem reescrever regexes

# Casos de erro

- texto limpo contendo controles bidi deve sair higienizado
- texto limpo com segredo reconhecido deve sair mascarado
- output bruto com segredo deve permanecer bruto e inalterado
- configuracao invalida de patterns de segredo nao deve quebrar o contrato tipado de `AppSettings`
- artifacts publicos persistidos com segredo nao devem reaparecer em preview publico sem masking

# Cenarios verificaveis

## Cenario 1: adapter preserva raw e endurece clean

- Dado um output de CLI com ANSI, bidi e um segredo reconhecivel
- Quando o adapter produzir `CLIExecutionResult`
- Entao `stdout_raw` e `stderr_raw` permanecem intactos
- E `stdout_clean` e `stderr_clean` removem ANSI, stripam bidi, normalizam NFKC e mascaram o segredo

## Cenario 2: parsing endurece `stdout_clean` sem quebrar artifacts

- Dado um output com texto ruidoso, segredo em texto livre e artifact fenced valido
- Quando `parse_cli_output()` for executado
- Entao `stdout_raw` permanece intacto
- E `stdout_clean` fica higienizado
- E a extracao de artifacts continua funcionando

## Cenario 3: persistencia publica mascara segredo e preserva raw

- Dado um step com `raw_output` e `clean_output` contendo segredo
- Quando o `ArtifactStore` persistir os outputs
- Entao `raw.txt` preserva o conteudo bruto
- E `clean.txt`, named artifacts publicos e `RUN_REPORT.md` nao expõem o segredo em leitura publica

# Observacoes

Esta feature implementa a fundacao de sanitizacao da IDEA-001, mas nao esgota o programa de guardrails. `G-03` em diante permanecem fora do recorte e devem seguir em features posteriores para manter o repositório fiel ao modelo spec-first, feature-by-feature e uma frente por vez.

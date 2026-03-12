---
id: F22-release-readiness
type: feature
summary: Consolidar a etapa 2 como primeira release tecnica coerente, alinhando docs publicos, notas de release e validacoes finais da superficie atual.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/architecture/PHASE_2_ROADMAP.md
  - README.md
  - CHANGELOG.md
  - features/F17-artifact-preview/SPEC.md
  - features/F20-public-onboarding/SPEC.md
  - src/aignt_os/cli/app.py
outputs:
  - release_readiness_docs
  - release_readiness_tests
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "nao abrir nova superficie publica de produto alem da CLI e docs ja existentes"
  - "nao alterar schema SQLite, worker, state machine ou pipeline por inercia"
  - "preservar o quickstart publico atual como local e sync-first"
  - "documentar preview de artifacts apenas dentro dos limites ja estabelecidos pela F17"
  - "nao exigir DOCKER_PREFLIGHT, porque a release tecnica continua ancorada no fluxo publico local atual"
acceptance_criteria:
  - "Existe um `CHANGELOG.md` versionado resumindo a release tecnica `0.1.0` e a superficie publica consolidada ate a F22."
  - "Existe uma nota de release versionada em `docs/release/phase-2-technical-release.md` com escopo, fluxo publico suportado, limites operacionais e validacoes executadas."
  - "O `README.md` documenta o boundary entre quickstart sync-first e preview de artifacts, incluindo exemplos de `--preview report` e `<STEP_STATE>.clean`."
  - "Existe pelo menos um teste unitario validando changelog/release notes/README da readiness."
  - "Existe pelo menos um teste de integracao validando a leitura de `--preview report` sobre um `RUN_REPORT.md` real persistido e pelo menos um teste mantendo o quickstart publico atual executavel."
  - "A feature termina com `CHECKLIST.md` e `REPORT.md` proprios, sem prometer release publica acima da maturidade real."
non_goals:
  - "mudar versionamento do pacote alem da documentacao da release tecnica atual"
  - "adicionar instalador, packaging distribuivel ou automacao de publish"
  - "abrir novo fluxo publico que exija Docker, runtime persistente ou credenciais externas"
  - "redefinir a demo oficial para exigir stop_at `DOCUMENT` no quickstart minimo"
security_notes:
  - "nao ampliar o preview para `raw_output` nem para leitura arbitraria de artifacts"
  - "manter a readiness centrada em docs, contratos publicos e validacao local controlada"
dependencies:
  - F17-artifact-preview
  - F20-public-onboarding
  - F21-cli-error-model-and-exit-codes
---

# Contexto

A etapa 2 do AIgnt OS ja consolidou submit publico, detalhe de run, contrato de erros, caminho canonico, doctor, onboarding e preview controlado de artifacts, enquanto o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS. Falta empacotar esse estado como uma release tecnica coerente e auditavel, sem prometer maturidade acima da realmente entregue.

# Objetivo

Consolidar a etapa 2 como primeira release tecnica coerente por meio de changelog, nota de release, README alinhado e validacoes finais da superficie publica atual, sem abrir nova feature de produto.

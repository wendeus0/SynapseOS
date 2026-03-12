# Phase 2 Technical Release

## Summary

Esta release tecnica consolida a etapa 2 do AIgnt OS sem abrir nova feature de produto alem da superficie publica ja entregue. O AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS, e a release foca em tornar o fluxo atual mais auditavel, documentado e reproduzivel.

## Public surface

- `aignt doctor`
- `aignt runs submit <spec_path>`
- `aignt runs show <run_id>`
- `aignt runs show <run_id> --preview report`
- `aignt runs show <run_id> --preview <STEP_STATE>.clean`

## Supported flow

O fluxo minimo oficial continua local e `sync-first`:

1. `aignt doctor`
2. `aignt runs submit <spec_path> --mode sync --stop-at SPEC_VALIDATION`
3. `aignt runs show <run_id>`

Artifact preview permanece opcional e depende de artifacts persistidos ja existentes, como `RUN_REPORT.md` e `clean_output` por step.

## Operational boundaries

- `repo-preflight` continua obrigatorio apenas para cenarios que dependem de Docker, imagem, boot, persistencia operacional ou integracao real.
- `raw_output` nao entra no preview publico.
- A release tecnica nao promete instalador, publish automatizado, runtime distribuido nem validacao com credenciais externas.

## Validation evidence

- quickstart publico executavel em testes de integracao
- preview de report validado sobre `RUN_REPORT.md` real persistido
- quality gate local completo com pytest, Ruff e mypy
- security gate local aprovado

# README Baseline Refresh Report

## Resumo executivo

- A `chore-readme-current-baseline-refresh` atualiza o `README.md` para funcionar como snapshot tecnico atual do repositorio no GitHub.
- A frente permaneceu doc-only: nao houve mudanca funcional em CLI, runtime, auth, persistencia ou no AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS.
- O README deixa de depender de uma narrativa antiga centrada em `F18`/`F22` e passa a refletir o baseline pos-`F23 -> F47`.

## Escopo alterado

- `features/chore-readme-current-baseline-refresh/{SPEC.md,NOTES.md,CHECKLIST.md,REPORT.md}` criados
- `README.md` reescrito no recorte editorial do snapshot tecnico atual
- `tests/unit/test_readme_current_baseline_docs.py` criado para travar o novo baseline documental

## Validacoes executadas

- `validate_spec_file(Path("features/chore-readme-current-baseline-refresh/SPEC.md"))`
- `python -m pytest tests/unit/test_public_onboarding_docs.py tests/unit/test_release_readiness_docs.py tests/unit/test_watch_and_cancellation_docs.py tests/unit/test_readme_current_baseline_docs.py -q`
- `./scripts/commit-check.sh --no-sync --skip-branch-validation --skip-docker --skip-security`
- `./scripts/security-gate.sh`

## Riscos residuais

- o README continua sendo um resumo tecnico; detalhes operacionais profundos permanecem em `docs/operations/LIFECYCLE.md`
- historico detalhado de releases e features continua fora do README e segue em `CHANGELOG.md` e `docs/release/`

## Status final da frente

- `READY_FOR_COMMIT`

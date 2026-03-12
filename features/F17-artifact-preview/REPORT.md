# F17 Report

## Resumo executivo

- A F17 adiciona preview textual controlado de artifacts uteis diretamente em `aignt runs show <run_id>`.
- O recorte permaneceu pequeno: `--preview report` para `RUN_REPORT.md` e `--preview <STEP_STATE>.clean` para output limpo persistido por step.
- O contrato da F21 foi preservado: target invalido retorna `Usage error:`/`2`, artifact ausente retorna `Not found:`/`3`, sempre sem traceback cru.

## Escopo alterado

- Extensao de `aignt runs show <run_id>` com a opcao `--preview`.
- Rendering de preview como painel adicional na CLI, sem quebrar o detalhe atual da run.
- Leitura controlada de artifacts persistidos da propria run, com truncamento explicito apos no maximo 40 linhas.
- Materializacao da feature em `features/F17-artifact-preview/` com `SPEC.md`, `NOTES.md`, `CHECKLIST.md` e este `REPORT.md`.

## Validacoes executadas

- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync python -m pytest tests/unit/test_cli_runs_rendering.py tests/integration/test_runs_cli.py -q`
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync python -m pytest tests/unit/test_cli_runs_rendering.py tests/integration/test_runs_cli.py tests/integration/test_cli_error_model.py tests/integration/test_runs_submit_cli.py -q`
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync ruff check src/aignt_os/cli/app.py src/aignt_os/cli/rendering.py tests/unit/test_cli_runs_rendering.py tests/integration/test_runs_cli.py`
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync python -m mypy src/aignt_os/cli/app.py src/aignt_os/cli/rendering.py tests/unit/test_cli_runs_rendering.py tests/integration/test_runs_cli.py`
- `./scripts/security-gate.sh`

## Security review

- Risco identificado: baixo. O delta nao adiciona shell, subprocesso, Docker, rede nem leitura arbitraria por path informado pelo usuario.
- Mitigacao aplicada: o preview so resolve `RUN_REPORT.md` e `clean_output_path` persistidos da propria run e valida que o arquivo solicitado permanece sob a raiz controlada pelo `ArtifactStore`.
- Parecer: aprovado com ressalvas baixas.

## Riscos residuais

- O preview nao mascara segredos de forma adicional; ele assume o contrato atual de outputs limpos da pipeline. Se surgir evidencia real de vazamento em `_clean`, isso deve virar endurecimento proprio.
- O preview de `clean_output` depende de path persistido ainda existente no disco no momento da leitura; se o artifact tiver sido removido, a CLI retorna `Not found:`.
- O recorte continua intencionalmente sem `raw_output`, named artifacts arbitrarios, paginacao ou browser de filesystem.

## Follow-ups

- Usar `branch-sync-guard` antes do fechamento Git da branch.
- Abrir a `F22-release-readiness` somente em branch empilhada sobre a HEAD da `F17`.

## Status final da frente

- `READY_FOR_COMMIT`

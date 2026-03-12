# F25 Report

## Resumo executivo

- A F25 foi implementada como guardrail AST para promocao de artifacts Python gerados.
- O recorte ficou fechado em `G-03`, com denylist minima + aliases simples, sem ampliar para migration, auth, Docker ou policy engine ampla.
- O enforcement principal ficou no caminho real do produto: `PipelinePersistenceObserver` valida antes da promocao e `ArtifactStore.save_named_artifact()` mantém a defesa final contra bypass.

## Escopo entregue

- Evolucao de `validate_python_artifact()` para sintaxe + denylist AST.
- Cobertura de `eval`, `exec`, `os.system` e `subprocess.*(..., shell=True)`.
- Cobertura de aliases simples para `os` e `subprocess`.
- Helper de validacao por nome logico do artifact Python (`.py`, `_py`, `_python`).
- Enforcement no observer antes de qualquer persistencia publica do step.
- Defesa adicional em `ArtifactStore.save_named_artifact()` para bloquear chamada direta.
- Cobertura unitaria e de integracao para artifact seguro, artifact inseguro e ausencia de persistencia quando o guardrail dispara.

## Validacoes executadas

- Leitura e alinhamento com `CONTEXT.md`, `docs/architecture/SDD.md`, `docs/architecture/TDD.md` e `docs/architecture/SPEC_FORMAT.md`.
- Validacao da SPEC com `validate_spec_file(Path('features/F25-generated-artifact-ast-guard/SPEC.md'))`.
- `uv run --no-sync python -m pytest tests/unit/test_parsing_engine.py tests/unit/test_persistence.py tests/unit/test_report_generator.py tests/integration/test_pipeline_persistence.py tests/integration/test_adapter_parser_flow.py tests/integration/test_runs_cli.py -q`
- `uv run --no-sync ruff check src/aignt_os/parsing.py src/aignt_os/persistence.py tests/unit/test_parsing_engine.py tests/unit/test_persistence.py tests/unit/test_report_generator.py tests/integration/test_pipeline_persistence.py tests/integration/test_adapter_parser_flow.py tests/integration/test_runs_cli.py`
- `uv run --no-sync mypy src/aignt_os/parsing.py src/aignt_os/persistence.py`
- `./scripts/security-gate.sh`

## Security review

- O review local identificou um bypass real: `raw.txt` e `clean.txt` ainda eram gravados antes da validacao AST e podiam permanecer listaveis quando a promocao do artifact falhava.
- O fluxo foi corrigido movendo a validacao dos artifacts Python para antes de `save_step_outputs()`, preservando a defesa adicional em `ArtifactStore` contra chamadas diretas.
- O guardrail agora bloqueia promocao de artifact Python inseguro sem deixar residuo publico do step reprovado e sem alterar o contrato da CLI.
- Artifacts nao-Python seguem fora do escopo do scanner AST por decisao explicita de recorte.

## Riscos residuais

- A heuristica de artifact Python por nome logico e propositalmente minima; nomes fora de `.py`, `_py` ou `_python` nao entram no scanner desta feature.
- O scanner nao tenta cobrir aliases complexos, reexportacoes profundas ou APIs perigosas fora da denylist minima.
- Audit trail mais rico e tipado para esse tipo de falha continua fora desta frente.

## Proximos passos

- Executar o fluxo Git completo da F25 ate merge e sync final.

## Status final da frente

- `READY_FOR_COMMIT`

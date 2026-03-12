# F23 Report

## Resumo executivo

- A F23 foi implementada como a fundacao de sanitizacao de seguranca da IDEA-001.
- O recorte ficou fechado em `G-01 + G-02 + G-04`: strip de bidi controls, normalizacao NFKC e masking de segredos em superficies limpas/publicas.
- O contrato de preservacao de outputs brutos foi mantido: `stdout_raw`, `stderr_raw`, `raw_output` e `raw.txt` seguem intactos, enquanto campos `*_clean`, artifacts publicos e `RUN_REPORT.md` passam pela sanitizacao compartilhada.

## Escopo entregue

- Novo modulo compartilhado `src/aignt_os/security.py` concentrando strip de bidi controls, normalizacao Unicode NFKC, remocao opcional de ANSI e masking configuravel de segredos.
- Endurecimento de `BaseCLIAdapter` para sanitizar `stdout_clean` e `stderr_clean` sem tocar `stdout_raw` e `stderr_raw`.
- Endurecimento do parsing para sanitizar `stdout_clean` sem quebrar a extracao de artifacts fenced.
- Endurecimento de `ArtifactStore` para sanitizar `clean.txt`, named artifacts publicos e `RUN_REPORT.md`, preservando `raw.txt` intacto.
- Extensao minima de configuracao em `AppSettings` com `secret_mask_patterns`.
- Testes unitarios e de integracao cobrindo bidi, NFKC, masking em `*_clean`, persistencia publica e previews publicos.

## Validacoes executadas

- Leitura e alinhamento com `CONTEXT.md`, `docs/architecture/SDD.md`, `docs/architecture/TDD.md` e `docs/architecture/SPEC_FORMAT.md`.
- Validacao da SPEC da feature com `validate_spec_file(Path('features/F23-security-sanitization-foundation/SPEC.md'))`.
- `uv run --no-sync python -m pytest tests/unit/test_security.py tests/unit/test_config.py tests/unit/test_cli_adapter.py tests/unit/test_parsing_engine.py tests/unit/test_persistence.py tests/integration/test_runs_cli.py -q`
- `uv run --no-sync ruff check src/aignt_os/security.py src/aignt_os/config.py src/aignt_os/adapters.py src/aignt_os/parsing.py src/aignt_os/persistence.py tests/unit/test_security.py tests/unit/test_config.py tests/unit/test_cli_adapter.py tests/unit/test_parsing_engine.py tests/unit/test_persistence.py tests/integration/test_runs_cli.py`
- `uv run --no-sync mypy src/aignt_os/security.py src/aignt_os/config.py src/aignt_os/adapters.py src/aignt_os/parsing.py src/aignt_os/persistence.py`
- `./scripts/security-gate.sh`

## Security review

- O boundary de seguranca da feature foi respeitado: sem schema changes, sem migrations, sem auth, sem circuit breaker e sem scanning AST.
- O principal risco funcional era mascarar cedo demais e quebrar a extracao de artifacts; a implementacao resolveu isso extraindo artifacts a partir do output limpo nao mascarado e aplicando masking apenas na superficie publicada em `stdout_clean`.
- O gate local de seguranca passou sem ressalvas abertas.

## Riscos residuais

- Os defaults de masking cobrem apenas padroes textuais conhecidos; segredos fora desses formatos seguem dependendo de ampliacoes futuras da IDEA-001.
- Ainda nao existe scanning AST de artifacts Python gerados por IA, audit trail de seguranca, rate limiting, circuit breaker ou autenticacao local; esses itens permanecem nas proximas frentes do programa.
- O contrato atual evita vazamento em superficies publicas e legiveis, mas nao faz saneamento retroativo de artifacts historicos ja persistidos.

## Proximos passos

- Abrir a proxima feature da IDEA-001 por SPEC propria, seguindo a ordem planejada para `G-03` em diante.
- Submeter a F23 para review e aprovacao antes de mergear, mantendo o modelo uma feature por vez.

## Status final da frente

- `READY_FOR_REVIEW`

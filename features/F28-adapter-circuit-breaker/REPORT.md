# F28 Report

## Resumo executivo

- A F28 foi implementada como um circuit breaker persistido para o adapter real atual.
- O recorte ficou fechado em `G-09`, limitado ao `CodexCLIAdapter`, sem reabrir auth, SQLite, CLI publica ou coordenacao distribuida do AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS.
- O breaker agora persiste estado local em arquivo, bloqueia spawns repetidos durante cooldown e volta a permitir probe apos expirar a janela.

## Escopo entregue

- Novo store local em `src/aignt_os/runtime/circuit_breaker.py` com escrita atomica e permissoes restritas.
- `AppSettings` estendido com threshold, cooldown e path derivado do arquivo do breaker.
- `CodexCLIAdapter` endurecido para consultar o breaker antes do spawn e atualizar o estado apos classificar o resultado.
- `CodexExecutionAssessment` ampliado com a categoria `circuit_open`.
- Cobertura unitaria e de integracao para persistencia, bloqueio sem spawn, reset apos cooldown e nao-regressao das classificacoes atuais.

## Validacoes executadas

- Leitura e alinhamento com `CONTEXT.md`, `docs/architecture/SDD.md`, `docs/architecture/TDD.md` e `docs/architecture/SPEC_FORMAT.md`.
- Validacao da SPEC com `validate_spec_file(Path('features/F28-adapter-circuit-breaker/SPEC.md'))`.
- `uv run --no-sync python -m pytest tests/unit/test_config.py tests/unit/test_adapter_circuit_breaker.py tests/unit/test_cli_adapter.py tests/integration/test_codex_adapter_operational.py -q`
- `uv run --no-sync ruff check src/aignt_os/adapters.py src/aignt_os/config.py src/aignt_os/contracts.py src/aignt_os/runtime/circuit_breaker.py tests/unit/test_config.py tests/unit/test_adapter_circuit_breaker.py tests/unit/test_cli_adapter.py tests/integration/test_codex_adapter_operational.py`
- `uv run --no-sync python -m mypy src/aignt_os/adapters.py src/aignt_os/config.py src/aignt_os/contracts.py src/aignt_os/runtime/circuit_breaker.py`

## Security review

- O review local nao deixou findings bloqueantes no recorte.
- O principal risco da frente era persistir estado operacional em path inseguro ou deixar o breaker mascarar falhas funcionais do adapter.
- Isso foi mitigado com path derivado de `runtime_state_dir`, rejeicao basica de paths com `..`, escrita atomica com permissoes privadas e ativacao do breaker apenas para categorias operacionais explicitas.

## Riscos residuais

- Arquivo de breaker corrompido e tratado de forma fail-open, reiniciando o estado local do breaker; isso preserva disponibilidade, mas reduz a memoria de cooldown ate a proxima falha operacional.
- O recorte continua limitado ao `codex`; outros adapters futuros precisarao de wiring proprio se herdarem o mesmo contrato.
- O breaker permanece local ao workspace/host atual e nao coordena multiplos processos concorrentes em maquinas diferentes.

## Proximos passos

- Executar o fluxo Git completo da F28 ate merge e sync final.
- Manter `G-11` fora desta frente e decidir a proxima feature apenas apos o fechamento desta branch.

## Status final da frente

- `READY_FOR_COMMIT`

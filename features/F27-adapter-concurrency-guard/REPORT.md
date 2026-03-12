# F27 Report

## Resumo executivo

- A F27 foi implementada como um guard de concorrencia local no adapter layer.
- O recorte ficou fechado em `G-07`, sem abrir circuit breaker persistido, coordenacao cross-process ou mudancas no runtime do AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS.
- A mitigacao central ficou em `BaseCLIAdapter.execute()`, que agora adquire um `asyncio.Semaphore` compartilhado por processo antes de abrir o subprocesso.

## Escopo entregue

- Adicao de `AppSettings.max_concurrent_adapters` com default `4` e override por ambiente.
- Introducao de um guard por processo reutilizado entre instancias de `BaseCLIAdapter`.
- Aplicacao do limite antes de `asyncio.create_subprocess_exec`, preservando timeout, sanitizacao e classificacao operacional ja existentes.
- Cobertura unitaria e de integracao para espera por slot, compartilhamento entre instancias e wiring via configuracao.

## Validacoes executadas

- Leitura e alinhamento com `CONTEXT.md`, `docs/architecture/SDD.md`, `docs/architecture/TDD.md` e `docs/architecture/SPEC_FORMAT.md`.
- Validacao da SPEC com `validate_spec_file(Path('features/F27-adapter-concurrency-guard/SPEC.md'))`.
- `uv run --no-sync python -m pytest tests/unit/test_config.py tests/unit/test_cli_adapter.py tests/integration/test_adapter_concurrency_flow.py -q`
- `uv run --no-sync ruff check src/aignt_os/adapters.py src/aignt_os/config.py tests/unit/test_cli_adapter.py tests/unit/test_config.py tests/integration/test_adapter_concurrency_flow.py`
- `uv run --no-sync mypy src/aignt_os/adapters.py src/aignt_os/config.py`
- `./scripts/security-gate.sh`

## Security review

- O review local nao deixou findings bloqueantes no recorte.
- O principal risco da frente era explosao de subprocessos simultaneos no adapter layer; isso foi mitigado com um guard compartilhado por processo antes da abertura do subprocesso.
- Nao houve creep para `G-09`: nenhum estado persistido, cooldown, circuit breaker ou coordenacao distribuida foi introduzido.

## Riscos residuais

- O limite da F27 vale apenas para o processo atual; execucoes em processos distintos continuam independentes por desenho.
- O mapa de semaphores fica em memoria de processo e nao oferece isolamento por workspace ou por run, o que permanece coerente com o recorte do MVP.
- Protecoes de health/cooldown para adapters continuam fora desta frente e devem ser tratadas em follow-up proprio.

## Proximos passos

- Executar o fluxo Git completo da F27 ate merge e sync final.

## Status final da frente

- `READY_FOR_COMMIT`

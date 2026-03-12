# F18 Notes

- A F18 nao cria comando novo; ela consolida a sequencia oficial `runs submit` seguido de `runs show`.
- O default desta SPEC e demonstracao sincrona e auditavel pela CLI, sem runtime persistente como pre-requisito obrigatorio.
- O sucesso terminal canonico desta frente e `completed @ SPEC_VALIDATION`, porque esse e o menor caminho publico estavel ja suportado.
- A feature deve provar que o operador consegue recuperar o `run_id` pela propria saida da CLI e reutiliza-lo em `runs show`.
- `repo-preflight` fica fora desta frente enquanto o recorte permanecer local e sem dependencia de Docker/container.
- Variantes `auto` e `async` continuam existentes por causa da F15, mas nao entram como caminho oficial primario da F18.
- Doctor de ambiente, onboarding e preview de artifact permanecem explicitamente fora de escopo para evitar drift com F19, F20 e F17.
- Se surgir ambiguidade futura sobre promover estados apos `SPEC_VALIDATION` ao happy path oficial, isso deve virar nova decisao de feature e nao expandir a F18 por inercia.
- A implementacao minima da frente ficou restrita ao rendering de `runs show`: runs `completed @ SPEC_VALIDATION` agora exibem orientacao explicita de happy path canonico concluido.
- O teste de integracao da F18 extrai o `run_id` diretamente da saida de `runs submit` e reutiliza esse valor em `runs show`, sem consultar SQLite nem filesystem manualmente.
- Validacao local executada com `uv run --no-sync pytest tests/integration/test_runs_submit_cli.py tests/integration/test_runs_cli.py tests/unit/test_cli_runs_rendering.py`, `uv run --no-sync ruff check src/aignt_os/cli/rendering.py tests/integration/test_runs_submit_cli.py tests/unit/test_cli_runs_rendering.py`, `uv run --no-sync python -m mypy src/aignt_os/cli/rendering.py` e `./scripts/security-gate.sh`.
- Security review local fechou sem ressalvas: a frente nao adiciona shell, subprocesso, leitura arbitraria de arquivo nem ampliacao de superficie publica.

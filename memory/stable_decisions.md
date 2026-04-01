# Stable Decisions — SynapseOS

## Arquitetura

1. **Synapse-Flow** é a engine própria de pipeline do SynapseOS — pipeline linear state-driven evoluído para DAG.
2. **CLI-first** — interface primária é CLI; UI desktop (Textual) somente quando houver demanda concreta.
3. **Core em Python** — runtime central permanece em Python; TypeScript limitado a shell/UI opcional.
4. **Container-first** — execução prática via Docker/Compose, com preflight leve (`compose config`).

## Boundaries e contratos

5. `ToolSpec`/capabilities formalizado — contratos explícitos de capabilities registradas.
6. `WorkspaceProvider` com isolation auditável — workspace path persistido e provider `run-scoped`.
7. `RunContext` enriquecido — eventos de lifecycle (`run_context_initialized`, `step_started`, `state_transitioned`).

## Multi-agent e orquestração

8. **Multi-Agent Session Orchestration** — registry/capabilities e coordenação entre adapters sem UI desktop.
9. **Supervisor deterministico** — decisões entre retry, reroute, return_to_code_green, fail.
10. **Runtime persistente** — Linux-first, identidade de processo validada via `/proc/<pid>/cmdline`.

## Execução e qualidade

11. **TDD explícito** — RED → GREEN → REFACTOR; testes antes do código de produção.
12. **Quality gates** — ruff, mypy, pytest como gates obrigatórios antes de SECURITY_REVIEW.
13. **Branch Sync Gate** — drift detection e atualização conservadora via scripts.

## Decisões de produto

14. **Desktop-shell fora da fila principal** — só retorna após runtime boundaries, workspace isolation, observability e control plane estabilizados.
15. **TypeScript-first runtime migration descartado** — por ora, TypeScript apenas para shell/UI opcional.
16. **Remote multi-host auth adiado** — só quando houver demanda concreta e recorte verificável.

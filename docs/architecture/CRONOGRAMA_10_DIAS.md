# Cronograma de 10 dias — AIgnt OS MVP

> Documento histórico do MVP inicial. O roadmap ativo da etapa 2, agora pos-F15, está em `docs/architecture/PHASE_2_ROADMAP.md`.

## Premissa de carga
Cronograma pensado para uma rotina apertada, com **3 a 4 horas líquidas por dia**, priorizando foco profundo e escopo pequeno. O objetivo aqui não é terminar "a plataforma inteira", mas **entregar um MVP funcional do núcleo**.

## Meta do MVP ao final do dia 10
- CLI inicial funcional
- SPEC válida bloqueando avanço quando inválida
- state machine da pipeline principal
- parser básico robusto
- adapter base assíncrono
- engine própria de pipeline linear
- persistência operacional
- worker leve
- supervisor básico
- `RUN_REPORT.md`
- 1 adapter real integrado

## Dia 1 — Recorte de escopo + bootstrap
- fechar backlog de features
- criar branches/worktrees
- montar `pyproject.toml`, Ruff, mypy, pytest
- criar estrutura de pastas e modelos base

**Saída do dia:** repositório pronto para trabalhar feature por feature.

## Dia 2 — F02 SPEC Engine MVP
- implementar parser de front matter YAML
- validar SPEC híbrida com Pydantic/JSON Schema
- criar fixtures válida/inválida
- testes de bloqueio do `PLAN`

**Saída do dia:** `SPEC_VALIDATION` confiável.

## Dia 3 — F03 State Machine MVP
- implementar estados principais
- validar transições
- testar caminhos válidos e inválidos
- preparar integração com pipeline manager

**Saída do dia:** state machine estável.

## Dia 4 — F04 Parsing Engine MVP
- cleaners
- remoção de ANSI e ruído
- extração de blocos
- validação mínima para código e SPEC
- testes com outputs ruidosos

**Saída do dia:** parsing robusto suficiente para hand-offs básicos.

## Dia 5 — F05 CLI Adapter Base Async
- contrato do adapter
- subprocess async
- timeout, stderr/stdout, sanitização
- testes de timeout e erro de retorno

**Saída do dia:** adapter base pronto para fake tools e 1 tool real depois.

## Dia 6 — F06 Engine Própria de Pipeline Linear
- `PipelineStep`
- `StepExecutor`
- `PipelineEngine`
- fluxo linear com fake environment
- integração básica SPEC -> PLAN -> TEST_RED

**Saída do dia:** pipeline executando em ambiente controlado.

## Dia 7 — F07 Persistência + Artifact Store
- SQLite
- repositório de run/step/event
- persistir raw/clean outputs
- salvar artefatos da run

**Saída do dia:** run reproduzível e auditável.

## Dia 8 — F08 Worker Leve + Runtime Dual
- fila simples de runs pendentes
- worker polling
- lock/lease simples
- regra inicial para sync vs async

**Saída do dia:** run longa já pode ser despachada.

## Dia 9 — F09 Supervisor MVP
- retry determinístico
- reroute simples
- falha terminal
- retorno controlado de etapas

**Saída do dia:** resiliência mínima do sistema.

## Dia 10 — F10 RUN_REPORT + 1 adapter real + hardening
- gerar `RUN_REPORT.md`
- integrar 1 adapter real
- rodar happy path ponta a ponta
- corrigir falhas finais
- fechar documentação mínima do MVP

**Saída do dia:** MVP demonstrável.

## Regra de ouro do cronograma
Se um dia atrasar, **não empurre tudo adiante sem cortar escopo**. Corte primeiro:
1. adapters reais extras
2. refinamentos de observabilidade
3. inteligência do supervisor
4. memória semântica avançada

## O que não pode cortar
- SPEC válida
- state machine
- parsing básico
- adapter base
- engine própria de pipeline linear
- persistência
- worker leve
- RUN_REPORT

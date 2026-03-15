---
id: F50-state-machine-hardening
type: feature
summary: "Formalizar estados do pipeline com Enums e definir estados terminais explícitos"
inputs:
  - N/A (Refatoração interna)
outputs:
  - Código usando PipelineState(StrEnum)
  - Comportamento consistente em estados terminais
acceptance_criteria:
  - Todos os estados do pipeline devem ser definidos em um StrEnum
  - Literais de string soltos devem ser removidos do código core
  - Estados terminais (COMPLETED, FAILED, CANCELLED) devem ser definidos em um set imutável
  - O worker deve parar imediatamente ao encontrar um estado terminal
non_goals:
  - Alterar a lógica de transição existente (apenas a representação dos estados)
  - Adicionar novos estados
---

## Contexto
Atualmente, os estados do pipeline (ex: "PLAN", "TEST_RED") são strings literais espalhadas pelo código (`pipeline.py`, `state_machine.py`, `worker.py`). Isso é propenso a erros de digitação e dificulta a análise estática. Além disso, a definição de "estado terminal" está implícita em algumas verificações, mas não centralizada.

## Objetivo
1.  Criar `class PipelineState(StrEnum)` em `src/aignt_os/state_machine.py`.
2.  Definir `TERMINAL_STATES` como um conjunto de `PipelineState`.
3.  Refatorar `PipelineEngine`, `RuntimeWorker` e testes para usar o Enum.

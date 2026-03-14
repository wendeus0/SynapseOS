---
id: F48-spec-validation-gate
type: feature
summary: "Bloquear execução de runs com SPEC inválida antes da etapa PLAN"
inputs:
  - Caminho da SPEC
outputs:
  - Run com status FAILED se inválido
  - Erro detalhado no RUN_REPORT.md
acceptance_criteria:
  - Run deve falhar imediatamente se a SPEC não tiver campos obrigatórios
  - Run deve falhar se o YAML frontmatter for inválido
  - Erro de validação deve ser persistido em RUN_REPORT.md
non_goals:
  - Validação semântica profunda do conteúdo (apenas estrutural)
  - Alteração no formato da SPEC
---

## Contexto
Atualmente, o `PipelineEngine` assume que a SPEC é válida ou falha de forma não tratada durante a execução. O `SpecValidator` existe (`src/aignt_os/specs/validator.py`), mas não é invocado obrigatoriamente no início do pipeline de execução. Isso permite que SPECs quebradas avancem para estados inconsistentes.

## Objetivo
Tornar a validação da SPEC um gate obrigatório na máquina de estados. Se a validação falhar:
1.  O estado da run deve transicionar para `FAILED`.
2.  O motivo da falha deve ser registrado.
3.  Nenhum step posterior (PLAN, RED, GREEN) deve ser executado.

---
id: F52-workspace-isolation-foundation
type: feature
summary: "Introduzir isolamento operacional de workspace por run sobre o WorkspaceProvider do Synapse-Flow"
inputs:
  - WorkspaceProvider introduzido pela F51
  - Boundary de workspace já endurecido em F24, F38 e F39
outputs:
  - Provider capaz de materializar um workspace operacional por run
  - Metadados persistidos para rastrear o workspace resolvido da run
  - Compatibilidade com o modo atual de workspace único quando o isolamento não for solicitado
acceptance_criteria:
  - O runtime deve conseguir resolver um workspace operacional por run sem quebrar o MVP de um único workspace local por execução
  - O caminho efetivo do workspace usado pela run deve ficar auditável para pipeline, persistência e observabilidade local
  - O sistema deve continuar rejeitando escapes fora da raiz confiável de workspace
  - O modo atual deve permanecer compatível quando nenhum isolamento adicional for solicitado
  - Deve existir cobertura de teste para resolução do workspace da run e para persistência do contexto correspondente
non_goals:
  - Criar múltiplos workspaces por uma mesma run
  - Implementar git worktree obrigatório nesta fase
  - Alterar a CLI pública para um modelo desktop-first
  - Introduzir scheduling distribuído ou coordenação multi-host
---

# Contexto
Com a `F51-runtime-boundaries-foundation`, o SynapseOS passou a expor contratos explícitos para `WorkspaceProvider`, `RunContext` e lifecycle hooks. Isso resolve o primeiro problema estrutural: o core agora tem boundary para runtime, workspace e extensibilidade.

O próximo gap prático é que o Synapse-Flow, a engine própria de pipeline do SynapseOS, ainda opera sobre um root local único, sem materializar um workspace operacional por run. Hoje já existe endurecimento de boundary em `workspace_root`, persistência e runtime state, especialmente nas frentes `F24`, `F38` e `F39`, mas isso ainda protege a raiz; não isola a execução.

Esse isolamento operacional é o pré-requisito mais útil para evoluções futuras como:

1. worktree por tarefa quando isso realmente compensar;
2. artifacts e diff por run com menos ambiguidade;
3. multi-agent orchestration com contexto de filesystem previsível;
4. control plane local com status de workspace explícito.

# Objetivo
Criar a fundação de isolamento operacional de workspace por run sem abrir ainda a ambição completa de `git worktree per task`.

O recorte desta feature deve:

1. permitir que o `WorkspaceProvider` resolva um workspace efetivo por run, ainda dentro de uma raiz confiável local;
2. tornar esse workspace auditável em persistência e observabilidade local;
3. preservar compatibilidade com o modelo atual quando o isolamento adicional não estiver habilitado;
4. preparar o terreno para uma futura frente específica de `git worktree` sem assumir esse custo agora.

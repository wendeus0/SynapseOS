---
id: F51-runtime-boundaries-foundation
type: refactor
summary: "Introduzir boundaries internos para tools, workspace, run context e lifecycle do Synapse-Flow"
inputs:
  - Arquitetura atual do SynapseOS
  - Padrões arquiteturais extraídos de Superset, Mastra e coding-agent
outputs:
  - Contratos internos explícitos para tools, workspace, run context e lifecycle
  - Integração do runtime atual com os novos contratos sem regressão funcional
  - Base estável para worktrees, multi-agent orchestration e control plane local em fases futuras
acceptance_criteria:
  - O core deve expor um contrato explícito para tool/capability sem depender da implementação concreta de adapter
  - O core deve expor um contrato explícito para workspace provider sem introduzir multi-workspace por run no MVP
  - O core deve expor um run context/lifecycle hook utilizável por pipeline, runtime e persistência
  - O comportamento atual do Synapse-Flow deve permanecer compatível com a pipeline linear state-driven existente
  - Deve existir cobertura de teste para os novos contratos internos e para a compatibilidade do fluxo atual com esses contratos
non_goals:
  - Implementar shell desktop
  - Migrar runtime central para TypeScript, Node ou Bun
  - Introduzir worktree por tarefa nesta fase
  - Introduzir memória semântica ativa ou roteamento automático por memória
  - Reestruturar o monorepo para o modelo do Superset
---

# Contexto
O SynapseOS já possui um núcleo coerente e auditável para o Synapse-Flow, a engine própria de pipeline do projeto, com pipeline linear state-driven, runtime dual simples, persistência local e adapters CLI. Esse núcleo está visível principalmente em `src/synapse_os/pipeline.py`, `src/synapse_os/state_machine.py`, `src/synapse_os/runtime/` e `src/synapse_os/adapters.py`.

A análise comparativa com Superset, Mastra e coding-agent mostrou que o maior ganho imediato não está em copiar stack, Electron ou o produto completo deles, mas em absorver boundaries mais fortes para:

1. tool/capability registry
2. workspace abstraction
3. run context e lifecycle hooks
4. observability e extensibilidade por contrato

Hoje esses pontos existem de forma parcial ou implícita. Isso dificulta evoluções incrementais como worktree por run, multi-agent orchestration, control plane local e uma UX mais rica sem aumentar acoplamento.

# Objetivo
Criar a primeira camada de fundação arquitetural inspirada em Superset e Mastra, mas implementada de forma nativa e incremental no SynapseOS.

O recorte desta feature deve:

1. introduzir contratos internos mínimos para `ToolSpec`/capabilities, `WorkspaceProvider`, `RunContext` e lifecycle hooks;
2. integrar esses contratos ao Synapse-Flow atual sem quebrar a pipeline linear do MVP;
3. preparar o terreno para features futuras de worktree isolation, observability mais rica, multi-agent orchestration e eventual control plane local;
4. preservar os princípios atuais de CLI-first, spec-first, local-first e auditabilidade.

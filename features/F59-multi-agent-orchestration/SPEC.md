---
id: F59-multi-agent-orchestration
type: feature
summary: Formalize adapter registry with capabilities and multi-agent session coordination
inputs:
    - Existing BaseCLIAdapter implementations (Codex, Gemini)
    - ToolSpec and capability contracts from runtime_contracts.py
    - PipelineEngine with executor routing support
outputs:
    - AdapterRegistry with capability-based routing
    - Multi-agent session coordination in Synapse-Flow
    - Capability-based task assignment logic
    - Tests for registry, routing, and multi-agent coordination
acceptance_criteria:
    - "AdapterRegistry deve registrar adapters por nome e expor capabilities consultaveis"
    - "CapabilityRouter deve selecionar adapter adequado com base em capability requerida"
    - "PipelineEngine deve suportar execucao de step com adapter selecionado por capability"
    - "Multi-agent handoff deve registrar qual adapter executou qual step no contexto"
    - "Fallback para adapter generico quando nenhum adapter especializado estiver disponivel"
    - "Teste de integracao deve validar fluxo completo de registro + routing + execucao"
non_goals:
    - Nao implementar comunicacao direta entre adapters (IPC, sockets)
    - Nao adicionar novos adapters externos nesta feature
    - Nao implementar load balancing ou escalabilidade horizontal
---

# Contexto

O SynapseOS atualmente suporta apenas um adapter por execucao de pipeline. O `PipelineEngine` aceita executores configurados por estado, mas nao ha registro central de adapters nem selecao automatica baseada em capacidades. O SDD lista 8 adapters planejados (Codex, Gemini, Copilot, OpenCode, DeepSeek, Claude, Local LLM), mas apenas Codex e Gemini existem.

A coordenacao multi-agent e um requisito fundamental do projeto: diferentes ferramentas de IA tem capacidades diferentes (code generation, planning, analysis, etc) e o Synapse-Flow deve saber qual adapter usar para cada tipo de tarefa.

# Objetivo

Criar um sistema de registro de adapters com capacidades explicitas e roteamento automatico baseado em capabilities, permitindo que o Synapse-Flow coordene multiplas ferramentas de IA dentro de uma mesma sessao de execucao.

## Escopo tecnico

1. **AdapterRegistry**: registro central de adapters disponiveis
2. **CapabilityRouter**: logica de selecao de adapter por capability requerida
3. **Integration com PipelineEngine**: execucao de steps com adapter selecionado automaticamente
4. **Handoff tracking**: registro de qual adapter executou qual step

## Capacidades planejadas

| Capability          | Descricao                  | Adapters Candidatos    |
| ------------------- | -------------------------- | ---------------------- |
| `cli_execution`     | Execucao CLI generica      | Todos                  |
| `code_generation`   | Geracao de codigo          | Codex, Copilot, Claude |
| `planning`          | Planejamento e arquitetura | Gemini, Claude         |
| `code_review`       | Revisao de codigo          | Claude, OpenCode       |
| `security_analysis` | Analise de seguranca       | Claude, DeepSeek       |
| `local_execution`   | Execucao local sem cloud   | Local LLM              |

## Design proposto

```python
# Adapter registry
class AdapterRegistry:
    def register(self, adapter: BaseCLIAdapter) -> None
    def get(self, name: str) -> BaseCLIAdapter | None
    def list_all(self) -> list[BaseCLIAdapter]
    def find_by_capability(self, capability: str) -> list[BaseCLIAdapter]

# Capability router
class CapabilityRouter:
    def __init__(self, registry: AdapterRegistry)
    def select_adapter(self, required_capabilities: set[str]) -> BaseCLIAdapter | None
    def get_best_match(self, required_capabilities: set[str]) -> BaseCLIAdapter | None
```

## Impacto no Synapse-Flow

O Synapse-Flow (engine propria de pipeline do SynapseOS) passara a:

1. Consultar o CapabilityRouter antes de cada step
2. Selecionar o adapter mais adequado para o tipo de tarefa
3. Registrar o adapter usado no contexto da run
4. Permitir fallback para adapter generico quando necessario

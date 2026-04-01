# ADR-004 — Implementar uma camada de abstração para adapters CLI com Multi-Agent Orchestration

## Status

Aceito (atualizado para multi-agent)

## Contexto

Cada ferramenta externa difere em sintaxe de comando, comportamento operacional, timeouts, autenticação e formato de output. Com múltiplos agentes disponíveis, o sistema precisa:

- Registrar adapters dinamicamente;
- Rotear tarefas para o agente mais adequado baseado em capability;
- Suportar fallback entre agentes quando um falha.

## Decisão

Criar uma camada dedicada de adapters CLI com:

1. **Interface compartilhada** (`BaseCLIAdapter`) para execução padronizada;
2. **AdapterRegistry**: registro dinâmico de adapters disponíveis;
3. **CapabilityRouter**: roteamento baseado em capabilities declaradas por cada adapter:
    - Cada adapter declara capabilities (ex: `code_generation`, `refactoring`, `testing`);
    - Router seleciona adapter mais adequado para a tarefa;
    - Suporte a fallback automático em caso de falha;
    - Política configurável (custo, latência, qualidade);
4. **Implementações específicas por ferramenta**: Gemini, Codex, Copilot, OpenCode, DeepSeek, Claude, LLMs locais.

## Consequências

### Positivas

- desacoplamento entre orquestrador e ferramentas;
- melhor testabilidade;
- extensão simplificada para novos agentes (apenas registrar no AdapterRegistry);
- centralização de políticas de execução;
- roteamento inteligente permite otimizar custo/qualidade por tarefa;
- resiliência via fallback entre múltiplos agentes.

### Negativas

- necessidade de manutenção contínua dos adapters;
- risco de abstração ruim esconder comportamentos úteis específicos;
- complexidade adicional do CapabilityRouter (decisão de roteamento);
- necessidade de mapear capabilities de forma consistente entre adapters.

## Alternativas consideradas

- chamadas diretas a subprocess espalhadas pelo código: rejeitado — sem abstração;
- adapter único parametrizado para tudo: rejeitado — não lida com diferenças semânticas;
- scripts shell externos como wrappers: rejeitado — difícil testar e manter;
- roteamento hardcoded por tarefa: rejeitado — não é extensível.

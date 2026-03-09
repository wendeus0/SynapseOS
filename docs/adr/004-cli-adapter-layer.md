# ADR-004 — Implementar uma camada de abstração para adapters CLI

## Status
Aceito

## Contexto
Cada ferramenta externa difere em sintaxe de comando, comportamento operacional, timeouts, autenticação e formato de output.

## Decisão
Criar uma camada dedicada de adapters CLI com interface compartilhada e implementações específicas por ferramenta.

## Consequências
### Positivas
- desacoplamento entre orquestrador e ferramentas;
- melhor testabilidade;
- extensão simplificada para novos agentes;
- centralização de políticas de execução.

### Negativas
- necessidade de manutenção contínua dos adapters;
- risco de abstração ruim esconder comportamentos úteis específicos de uma ferramenta.

## Alternativas consideradas
- chamadas diretas a subprocess espalhadas pelo código;
- adapter único parametrizado para tudo;
- scripts shell externos como wrappers.

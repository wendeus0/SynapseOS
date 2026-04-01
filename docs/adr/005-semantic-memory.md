# ADR-005 — Implementar memória semântica com papel advisory no MVP e indexing

## Status

Aceito (atualizado para indexing)

## Contexto

A memória semântica pode futuramente influenciar roteamento e planejamento, mas isso aumenta risco de comportamento pouco previsível. Além disso, o volume de artefatos gerados demanda indexação eficiente para consultas rápidas.

## Decisão

No MVP, a memória semântica será implementada com:

1. **Papel advisory/read-only**: apoio de execução, enriquecimento de contexto e análise posterior, sem alterar automaticamente o roteamento;
2. **IndexedArtifactStore**: armazenamento de artefatos com índices para consulta rápida:
    - Índice por run_id, step_id, tipo de artefato;
    - Índice por timestamp para consultas temporais;
    - Índice por hash de conteúdo para deduplicação;
3. **Namespacing**: isolamento de memória por:
    - Workspace (diferentes projetos);
    - Run (contexto de execução);
    - Step (contexto de step específico);
    - Global (padrões compartilhados entre runs).

## Consequências

### Positivas

- comportamento mais previsível com memória advisory;
- melhor auditabilidade;
- consultas rápidas a artefatos históricos via índices;
- deduplicação automática reduz storage;
- namespacing permite contextos isolados e seguros;
- base para futura evolução de memória semântica com roteamento.

### Negativas

- menos adaptação automática no curto prazo;
- overhead de manutenção de índices;
- complexidade de gerenciamento de namespaces;
- necessidade de estratégia de expiração/limpeza de índices antigos.

## Alternativas consideradas

- operação totalmente stateless: rejeitado — perde aprendizado;
- memória semântica com roteamento automático desde o MVP: rejeitado — risco prematuro;
- apenas logs sem sumarização semântica: rejeitado — perde valor analítico;
- armazenamento sem índice: rejeitado — escalabilidade ruim com volume;
- índice único global: rejeitado — sem isolamento de contexto.

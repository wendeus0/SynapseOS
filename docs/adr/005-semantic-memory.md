# ADR-005 — Implementar memória semântica com papel advisory no MVP

## Status
Aceito

## Contexto
A memória semântica pode futuramente influenciar roteamento e planejamento, mas isso aumenta risco de comportamento pouco previsível e difícil de explicar no primeiro release.

## Decisão
No MVP, a memória semântica será implementada com papel **advisory/read-only**. Ela servirá para apoio de execução, enriquecimento de contexto e análise posterior, sem alterar automaticamente o roteamento.

## Consequências
### Positivas
- comportamento mais previsível;
- melhor auditabilidade;
- menor risco de decisões automáticas ruins;
- possibilidade de aprender com histórico sem automatizar cedo demais.

### Negativas
- menos adaptação automática no curto prazo;
- supervisor determinístico continua responsável pelas decisões principais.

## Alternativas consideradas
- operação totalmente stateless;
- memória semântica com roteamento automático desde o MVP;
- apenas logs sem sumarização semântica.

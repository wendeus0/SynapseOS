# ADR-007 — Integrar LLMs locais para raciocínio offline de apoio

## Status
Aceito

## Contexto
O AIgnt OS busca eficiência de custo, resiliência parcial offline e mais privacidade para tarefas auxiliares.

## Decisão
Integrar LLMs locais para tarefas de suporte, como sumarização semântica, explicações, extração de padrões e geração de commit messages.

## Consequências
### Positivas
- menor dependência externa;
- menor custo marginal para tarefas auxiliares;
- melhor privacidade em alguns cenários.

### Negativas
- consumo local de CPU/RAM;
- qualidade potencialmente inferior em tarefas complexas.

## Alternativas consideradas
- somente CLIs remotas;
- regras determinísticas locais apenas;
- modelos auxiliares via API.

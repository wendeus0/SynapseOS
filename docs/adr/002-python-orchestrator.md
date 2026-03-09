# ADR-002 — Adotar Python como linguagem do orquestrador

## Status
Aceito

## Contexto
O sistema requer alta produtividade, excelente suporte a subprocess, ecossistema maduro de testes e forte capacidade de parsing e automação em ambiente Linux.

## Decisão
Implementar o orquestrador principal em Python.

## Consequências
### Positivas
- desenvolvimento rápido;
- ecossistema rico para testes, parsing e automação;
- forte aderência a Linux e ferramentas CLI;
- boa ergonomia para desenvolvimento assistido por IA.

### Negativas
- menor performance bruta que linguagens compiladas;
- necessidade de disciplina maior em tipagem e estrutura.

## Alternativas consideradas
- Go;
- Rust;
- TypeScript/Node.js;
- Bash com helpers.

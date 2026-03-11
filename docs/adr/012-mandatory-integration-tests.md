# ADR-012 — Exigir testes de integração para features com I/O, persistência, lifecycle ou entrypoint público

## Status
Aceito

## Contexto
O AIgnt OS adota TDD explícito com cobertura progressiva das features. Até a feature F07, os testes eram predominantemente unitários — suficientes para validar contratos isolados, mas insuficientes para garantir comportamento real em features que envolvem I/O de filesystem, lifecycle de processo, adaptadores com subprocesso ou encadeamento entre módulos via entrypoint público.

A expansão da suíte para 215 testes (F01–F07 + TDD hardening) evidenciou que certos critérios de aceite não podem ser verificados com testes unitários puros: um test unitário com mocks pode passar mesmo quando a integração real falha silenciosamente.

## Decisão
Toda feature que se enquadre em pelo menos uma das categorias abaixo **deve incluir no mínimo um** `acceptance_criterion` verificável exclusivamente via teste de integração — sem mocks totais:

| Categoria | Exemplos |
|---|---|
| Lifecycle de runtime | start/stop/status do processo residente via CLI |
| Persistência | SQLite, filesystem de artefatos |
| Entrypoint público da CLI | comandos que orquestram módulos reais |
| Adapter com subprocesso | execução de ferramenta externa real |
| Pipeline com módulos reais | pipeline engine + validator real integrados |

O critério de integração deve constar explicitamente no front matter `acceptance_criteria` da SPEC, e deve existir pelo menos um teste correspondente em `tests/integration/` ou `tests/pipeline/`.

Testes puramente unitários **não substituem** testes de integração nessas categorias.

## Consequências
### Positivas
- garante que comportamento de I/O real seja verificado antes de merge;
- reduz risco de regressão silenciosa em encadeamentos entre módulos;
- torna os `acceptance_criteria` da SPEC diretamente rastreáveis para testes concretos;
- alinha o processo de feature com a pirâmide de testes (unit + integration).

### Negativas
- aumenta o esforço por feature nas categorias afetadas;
- testes de integração são mais lentos e têm mais pontos de falha ambiental;
- exige disponibilidade de fixtures realistas para simular I/O sem dependências externas reais.

## Alternativas consideradas
- Manter apenas testes unitários com mocks totais: rejeitado, pois não detecta falhas de contrato entre módulos reais.
- Exigir testes de integração para todas as features sem distinção de categoria: rejeitado, pois aumentaria custo desnecessariamente em features puramente de lógica interna (ex: state machine, contratos Pydantic).
- Deixar a decisão implícita na documentação sem ADR: rejeitado, pois a regra afeta todas as features futuras e precisa de rastreabilidade.

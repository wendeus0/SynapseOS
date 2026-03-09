# ADR-003 — Adotar state machine + engine própria de pipeline

## Status
Aceito

## Contexto
O AIgnt OS precisa coordenar uma esteira com estados explícitos, retries, rollback lógico, hand-offs auditáveis e futura evolução para DAG. Scripts lineares isolados comprometeriam rastreabilidade, manutenção e controle fino do domínio.

## Decisão
O sistema adotará:
- **state machine** para governar estados e transições;
- uma **engine própria de pipeline** em Python para coordenar os steps, hand-offs, retries e integração com o supervisor.

## Consequências
### Positivas
- transições explícitas e auditáveis;
- forte aderência ao domínio do produto;
- menor complexidade operacional no MVP do que orquestradores pesados;
- caminho claro para evolução futura para DAG e paralelismo.

### Negativas
- maior responsabilidade de implementação interna;
- necessidade de testes rigorosos da engine própria de pipeline.

## Alternativas consideradas
- pipeline linear hardcoded;
- Prefect desde o MVP;
- Temporal desde o MVP;
- fila sem modelagem explícita de estado.

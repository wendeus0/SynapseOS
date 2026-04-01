# ADR-003 — Adotar state machine + Synapse-Flow

## Status

Aceito (atualizado para DAG pipeline)

## Contexto

O SynapseOS precisa coordenar uma esteira com estados explícitos, retries, rollback lógico, hand-offs auditáveis e execução paralela. Scripts lineares isolados comprometeriam rastreabilidade, manutenção e controle fino do domínio.

## Decisão

O sistema adotará:

- **state machine** para governar estados e transições;
- o **Synapse-Flow**, a **engine própria de pipeline** do SynapseOS, em Python para coordenar os steps, hand-offs, retries e integração com o supervisor;
- **DAG pipeline execution** com suporte a:
    - steps com dependências explícitas;
    - execução paralela de steps independentes via `asyncio.gather`;
    - fan-out/fan-in para steps que precisam aguardar múltiplas dependências;
    - detecção de ciclos no grafo de dependências.

O Synapse-Flow mantém compatibilidade com pipelines lineares (DAG de 1 caminho) enquanto evolui para execução paralela real.

## Consequências

### Positivas

- transições explícitas e auditáveis;
- forte aderência ao domínio do produto;
- execução paralela reduz tempo total de runs com steps independentes;
- caminho claro para evolução futura para workers distribuídos;
- modelo de dependências explícitas melhora documentação e rastreabilidade.

### Negativas

- maior responsabilidade de implementação interna;
- necessidade de testes rigorosos do Synapse-Flow;
- complexidade adicional de scheduling paralelo e sincronização;
- detecção de ciclos e validação de DAG adicionam overhead.

## Alternativas consideradas

- pipeline linear hardcoded: rejeitado — não aproveita paralelismo;
- Prefect desde o MVP: rejeitado — complexidade operacional prematura;
- Temporal desde o MVP: rejeitado — overkill para estado atual;
- fila sem modelagem explícita de estado: rejeitado — perde rastreabilidade.

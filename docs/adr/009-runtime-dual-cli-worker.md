# ADR-009 — Adotar runtime dual com CLI efêmero + worker residente leve

## Status
Aceito

## Contexto
O AIgnt OS será usado principalmente via CLI, mas certas runs exigirão retries longos, acompanhamento de estado e execução sem bloquear a interface. Adotar uma infraestrutura de filas distribuídas desde o início aumentaria desnecessariamente a complexidade operacional do MVP.

## Decisão
O MVP adotará um runtime dual:
- **CLI efêmero** para iniciar, executar inline ou inspecionar runs;
- **worker/daemon residente leve** em Python para consumir runs pendentes, aplicar retries e finalizar artefatos.

## Consequências
### Positivas
- suporte a tarefas longas desde o início;
- reaproveitamento da mesma base técnica do AIgnt-Synapse-Flow, a engine própria de pipeline do AIgnt OS;
- menor complexidade que Celery/Temporal no MVP;
- preservação da experiência CLI.

### Negativas
- exige modelagem explícita de locking, polling e retomada;
- pode precisar ser substituído ou expandido quando houver múltiplos workers distribuídos.

## Alternativas consideradas
- apenas CLI efêmero;
- Celery no MVP;
- Temporal no MVP.

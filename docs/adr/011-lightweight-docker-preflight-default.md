# ADR-011 — Manter DOCKER_PREFLIGHT leve por padrão

## Status
Aceito

## Contexto
O fluxo oficial do projeto exige `DOCKER_PREFLIGHT` antes de iniciar a execução prática de uma feature. Ao mesmo tempo, subir o container completo em todo check local ou toda execução de CI aumenta tempo, custo operacional e pontos de falha, inclusive para mudanças que não tocam ciclo de vida, boot, persistência ou integração real do runtime.

O projeto também busca preservar segurança operacional e previsibilidade sem bloquear desnecessariamente o desenvolvimento feature-by-feature.

## Decisão
Manter o `DOCKER_PREFLIGHT` leve por padrão:
- em CI, o padrão é validar `compose config` e build com `--skip-up`;
- no fluxo local e hooks, o padrão é preflight leve, sem bloquear commits com `docker compose up`;
- build real Docker só acontece quando explicitamente pedido ou em contextos especiais;
- subir o container completo fica reservado para workflow dedicado de runtime/integração ou para tarefas explícitas de boot, ciclo de vida, persistência ou integração.

## Consequências
### Positivas
- reduz custo e tempo da automação operacional padrão;
- diminui flakiness em CI e no fluxo local;
- preserva o papel do Docker como isolamento sem transformar todo commit em validação pesada;
- mantém `repo-automation` como dona do preflight operacional com menor privilégio por padrão.

### Negativas
- parte dos problemas de runtime completo pode aparecer apenas no workflow dedicado ou na execução explícita;
- exige disciplina para acionar o preflight completo quando a feature realmente tocar ciclo de vida ou persistência;
- adiciona mais um modo operacional para o time entender.

## Alternativas consideradas
- subir o container completo em todo `DOCKER_PREFLIGHT`;
- remover build do preflight padrão e validar apenas `compose config`;
- não ter workflow dedicado para runtime/integração.

---
name: debug-failure
description: Use esta skill quando a tarefa for diagnosticar uma falha real em CI, scripts, testes, Docker, runtime, Git ou ambiente local, classificando a causa inicial e indicando qual agent deve atuar em seguida. Não use esta skill para implementar a correção, priorizar backlog ou alterar arquitetura.
---

# Objetivo

Investigar falhas reais de forma objetiva, reproduzindo quando possível, classificando a falha e encaminhando o próximo agent adequado.

# Escopo

Esta skill:
- investiga falhas em CI, scripts, testes, Docker, runtime, Git e ambiente local
- tenta reproduzir a falha quando isso for viável
- classifica a falha
- sugere o próximo agent responsável pela ação seguinte
- pode consultar `ERROR_LOG.md` e `PENDING_LOG.md` para identificar reincidência, regressão ou mitigação parcial

Esta skill não:
- implementa a correção
- substitui `repo-automation`
- decide backlog
- abre feature
- cria ADR
- altera arquitetura
- abre PR

# Leia antes de agir

Leia nesta ordem:
1. `AGENTS.md`
2. `CONTEXT.md`
3. `ERROR_LOG.md`, se existir
4. `PENDING_LOG.md`, se existir
5. arquivos e logs diretamente ligados à falha
6. `git status`
7. `git diff --stat`
8. instrução atual do usuário

# Quando esta skill deve ser usada

Use esta skill quando:
- houver falha real sem classificação clara
- um script operacional falhar
- um teste falhar e a origem ainda não estiver clara
- houver erro em Docker/compose, runtime, Git/branch, workflow/CI ou ambiente local
- for preciso decidir qual agent deve atuar em seguida

# Quando esta skill NÃO deve ser usada

Não use esta skill para:
- implementar a correção da falha
- revisar segurança como etapa principal
- decidir a próxima feature ou backlog
- criar ADR diretamente
- substituir `technical-triage` em priorização

# Classificação obrigatória

Toda falha investigada deve ser classificada como uma das categorias:
- `código/runtime`
- `teste`
- `Docker/compose`
- `workflow/CI`
- `Git/branch`
- `ambiente local`

# Encaminhamento

Após classificar a falha, indique o próximo agent:
- `repo-automation` para Docker, scripts operacionais, build/rebuild, workflows e preflight
- `security-review` quando a falha revelar risco de segurança ou mitigação pendente
- `test-red` quando o problema estiver em teste incorreto ou cobertura faltante derivada da SPEC
- `green-refactor` quando a falha apontar correção de implementação já claramente delimitada
- `git-flow-manager` quando o bloqueio estiver no fluxo Git final
- `session-logger` quando a falha e a decisão precisarem ser registradas
- `technical-triage` apenas se a falha revelar possível nova feature ou dúvida real de priorização
- `adr-manager` apenas se a falha revelar possível decisão arquitetural ainda não formalizada

Para falhas da categoria `Git/branch`, prefira verificar drift e segurança de atualização pelos scripts `./scripts/branch-sync-check.sh` e `./scripts/branch-sync-update.sh`.

# Processo

1. Identifique a falha real e o contexto mínimo necessário.
2. Tente reproduzir a falha quando isso for seguro e viável.
3. Separe sintoma, causa provável e evidência observada.
4. Classifique a falha em uma única categoria principal.
5. Indique o próximo agent responsável.
6. Se houver incerteza, explicite o que falta validar.

# Regras obrigatórias

- Seja objetivo e operacional.
- Não amplie escopo para correção completa.
- Não invente causa sem evidência mínima.
- Se não for possível reproduzir, diga isso explicitamente.
- Não conclua que a falha está resolvida só porque já apareceu antes em `ERROR_LOG.md` ou `PENDING_LOG.md`.
- Se a falha apontar possível nova feature ou ADR, apenas encaminhe.

# Saída final esperada

Entregue apenas:
1. falha investigada
2. reprodução realizada ou não
3. evidências principais
4. classificação da falha
5. causa provável
6. próximo agent recomendado
7. pontos ainda a validar, se houver

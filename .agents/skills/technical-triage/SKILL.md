---
name: technical-triage
description: Use esta skill quando a tarefa for analisar o estado atual do projeto e recomendar o próximo passo lógico, considerando débito técnico, pendências, erros recentes, contexto arquitetural e progresso da feature atual. Não use esta skill para implementar código, escrever testes RED, editar SPECs ou alterar diretamente a arquitetura.
---

# Objetivo

Analisar o estado atual do projeto e recomendar o próximo passo mais lógico, com justificativa curta, prioridade e alternativa em caso de bloqueio.

Esta skill existe para ajudar na priorização prática do trabalho, especialmente quando houver:
- débito técnico
- múltiplas pendências abertas
- dúvidas sobre continuidade da feature atual
- necessidade de decidir entre corrigir baseline, seguir feature, ajustar docs ou abrir nova feature

# Escopo

Esta skill:
- analisa contexto
- avalia pendências e erros
- recomenda o próximo passo
- sugere qual skill deve ser chamada em seguida

Esta skill não:
- implementa código
- escreve testes
- edita SPECs
- altera workflows
- muda arquitetura
- atualiza ADRs por conta própria

# Leia antes de agir

Leia nesta ordem:
1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/architecture/SDD.md`
4. `docs/architecture/TDD.md`
5. `docs/architecture/IMPLEMENTATION_STACK.md`
6. `ERROR_LOG.md`, se existir
7. `PENDING_LOG.md`, se existir
8. `git status`
9. `git diff --stat`
10. instrução atual do usuário
11. feature atual em `features/<feature>/SPEC.md`, se houver

# Quando esta skill deve ser usada

Use esta skill quando:
- o usuário perguntar “qual o próximo passo?”
- houver dúvida entre continuar a feature atual ou corrigir débito técnico
- a baseline do projeto estiver instável
- houver muitas pendências abertas
- for necessário decidir qual skill chamar em seguida
- for necessário evitar abrir trabalho novo na hora errada

# Quando esta skill NÃO deve ser usada

Não use esta skill para:
- criar a SPEC da próxima feature
- gerar backlog completo do produto
- auditar segurança
- automatizar Docker/CI
- substituir o julgamento arquitetural formal de ADRs

# Critérios de análise

Ao avaliar o próximo passo, considere:
- estado atual da baseline
- erros relevantes ainda abertos
- pendências com prioridade alta
- bloqueios operacionais
- impacto arquitetural
- custo de abrir uma nova frente
- benefício de estabilizar o que já existe antes de avançar

# Prioridades de decisão

Em geral, a ordem de prioridade deve favorecer:
1. corrigir baseline quebrada
2. remover bloqueios operacionais
3. concluir a feature atual
4. consolidar handoff/logs, se necessário
5. só então abrir nova feature

Se houver motivo forte para fugir dessa ordem, explique claramente.

# Formato da saída

A resposta deve conter:
1. **Próximo passo recomendado**
2. **Motivo**
3. **O que não fazer agora**
4. **Skill recomendada para a próxima ação**
5. **Alternativa caso haja bloqueio**
6. **Prioridade**: P0 | P1 | P2

# Regras obrigatórias

- Seja objetivo.
- Não ofereça múltiplos caminhos equivalentes sem ordenar.
- Dê uma recomendação principal clara.
- Se o projeto estiver em estado instável, priorize estabilização.
- Se faltar contexto, diga exatamente o que falta.
- Não invente progresso inexistente.

# Processo

1. Identifique o estado atual do projeto.
2. Verifique baseline, erros e pendências.
3. Avalie se a feature atual deve continuar ou pausar.
4. Escolha um próximo passo principal.
5. Sugira a skill seguinte mais adequada.
6. Forneça uma alternativa apenas se houver bloqueio provável.

# Critérios de qualidade

Antes de encerrar, confirme:
- há uma recomendação principal clara
- a justificativa é curta e prática
- a sugestão respeita o estado real do projeto
- a skill seguinte foi indicada explicitamente
- não houve expansão indevida de escopo

# Saída final esperada

Entregue apenas:
1. próximo passo recomendado
2. motivo
3. o que não fazer agora
4. skill recomendada
5. alternativa em caso de bloqueio
6. prioridade

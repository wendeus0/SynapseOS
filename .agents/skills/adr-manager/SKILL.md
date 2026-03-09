---
name: adr-manager
description: Use esta skill quando a tarefa for avaliar se uma mudança do projeto exige criação ou atualização de ADR (Architectural Decision Record), e então redigir o ADR adequado no padrão do repositório. Não use esta skill para implementar código, alterar workflows, criar SPECs ou executar automações operacionais.
---

# Objetivo

Avaliar se uma mudança introduziu, alterou ou formalizou uma decisão arquitetural estável e, se necessário, criar ou atualizar ADRs do projeto.

# Escopo

Esta skill:
- avalia a necessidade de ADR
- identifica se a decisão já está coberta por ADR existente
- decide entre:
  - não criar ADR
  - atualizar ADR existente
  - criar novo ADR
- escreve o ADR no padrão do repositório

Esta skill não:
- implementa código
- altera Docker/workflows
- escreve testes
- cria SPEC de feature
- faz commit/push/PR
- executa revisão de segurança
- substitui a análise técnica geral do projeto

# Leia antes de agir

Leia nesta ordem:
1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/architecture/SDD.md`
4. `docs/architecture/TDD.md`
5. `docs/architecture/IMPLEMENTATION_STACK.md`
6. `docs/adr/*`
7. `git diff --stat`
8. `git diff`
9. instrução atual do usuário
10. outputs dos agentes envolvidos, quando relevantes

# Quando esta skill deve ser usada

Use esta skill quando:
- houver dúvida se uma mudança merece ADR
- uma nova convenção do projeto for adotada
- uma responsabilidade entre agents/skills mudar formalmente
- um novo fluxo estável do projeto for definido
- uma decisão arquitetural, operacional ou estrutural precisar ser registrada

# Quando esta skill NÃO deve ser usada

Não use esta skill para:
- registrar decisão local de implementação sem impacto durável
- registrar pequenos ajustes de código
- registrar correções de lint/format
- criar backlog
- resumir sessão
- fazer logging operacional

# Critérios para criar ou atualizar ADR

Considere ADR quando houver:
- decisão estável e durável
- impacto em múltiplas áreas do projeto
- alteração formal de fluxo
- nova convenção arquitetural ou operacional importante
- mudança de responsabilidade entre agents/skills
- trade-off relevante que precise de rastreabilidade futura

Em geral, NÃO crie ADR para:
- detalhe de implementação local
- correção de bug isolado
- renomeação sem impacto real
- ajustes táticos de curto prazo

# Processo

1. Identifique a mudança em análise.
2. Verifique se já existe ADR cobrindo esse tema.
3. Classifique a situação:
   - sem necessidade de ADR
   - atualizar ADR existente
   - criar ADR novo
4. Se necessário, produza o ADR no padrão do repositório.
5. Mantenha o texto curto, claro e objetivo.

# Formato esperado

Todo ADR deve conter:
- título
- status
- contexto
- decisão
- consequências
- alternativas consideradas

# Regras obrigatórias

- Não crie ADR desnecessário.
- Não duplique ADR existente sem motivo.
- Prefira atualizar ADR existente quando a decisão for extensão natural de algo já documentado.
- Se a mudança não justificar ADR, diga isso explicitamente.
- Seja conservador: ADR é para decisão durável, não para qualquer mudança.

# Critérios de qualidade

Antes de encerrar, confirme:
- a decisão realmente tem peso arquitetural/operacional durável
- não há ADR existente cobrindo o tema de forma suficiente
- o ADR está curto, claro e útil
- o texto não virou documentação excessiva

# Saída final esperada

Entregue apenas:
1. se a mudança exige ADR ou não
2. se deve criar novo ADR ou atualizar um existente
3. qual ADR foi criado ou atualizado, se houver
4. resumo curto da decisão registrada
5. pontos pendentes, se houver

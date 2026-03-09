---
name: spec-editor
description: Use esta skill quando a tarefa for transformar um pedido do usuário em uma SPEC de feature clara, enxuta e validável, ou quando for preciso revisar/editar features/*/SPEC.md ou docs/architecture/SPEC_FORMAT.md. Não use esta skill para implementar código de produção, escrever testes automatizados ou refatorar código.
---

# Objetivo

Transformar um pedido do usuário em uma SPEC de feature pequena, coerente com o AIgnt OS e pronta para alimentar TDD.

# Leia antes de agir

Leia nesta ordem:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/architecture/SDD.md`
4. `docs/architecture/TDD.md`
5. `docs/architecture/SPEC_FORMAT.md`
6. `features/<feature>/SPEC.md` se já existir

# Quando esta skill deve ser usada

Use esta skill quando:

- o usuário pedir para criar uma nova feature
- a feature ainda não tiver `SPEC.md`
- a `SPEC.md` existir, mas estiver ambígua, extensa demais ou inconsistente
- for necessário ajustar `SPEC_FORMAT.md` para melhorar o contrato das futuras features

# Quando esta skill NÃO deve ser usada

Não use esta skill para:

- implementar código de produção
- escrever testes automatizados
- refatorar módulos existentes
- resolver falhas de pipeline via código

# Restrições obrigatórias

- Trabalhe **uma feature por vez**.
- Nunca aumente escopo sem necessidade explícita.
- Se faltarem detalhes, **reduza o escopo** em vez de inventar comportamento.
- Só inicie após `DOCKER_PREFLIGHT` verde ou explicitamente validado pela skill `repo-automation`.
- A SPEC deve ser pequena o suficiente para caber em 1 a 3 dias de trabalho.
- A SPEC deve ser coerente com o MVP:
  - pipeline linear state-driven
  - AIgnt-Synapse-Flow como engine própria de pipeline
  - runtime dual simples
  - memória semântica apenas advisory
  - observabilidade local
  - 1 workspace por run

# Formato esperado da saída

A saída principal desta skill é um `SPEC.md` válido.

A SPEC deve:

- seguir `docs/architecture/SPEC_FORMAT.md`
- conter front matter YAML válido
- ter critérios de aceite verificáveis
- ter fora de escopo explícito
- ter casos de erro
- ter dependências/restrições técnicas quando necessário

# Processo

1. Resuma o pedido do usuário em 1 ou 2 frases.
2. Confirme que `DOCKER_PREFLIGHT` já liberou o início prático da feature.
3. Identifique o menor recorte útil da feature.
4. Verifique aderência ao MVP e à arquitetura.
5. Produza ou atualize `features/<feature>/SPEC.md`.
6. Se houver ambiguidade relevante, registre em `NOTES.md`.
7. Não siga para testes ou código.

# Checklist de qualidade

Antes de encerrar, confirme:

- a feature está pequena o suficiente
- o YAML está válido
- os critérios de aceite são testáveis
- o fora de escopo foi explicitado
- a SPEC não contradiz SDD, TDD ou ADRs

# Saída final esperada

Entregue:

1. `SPEC.md` atualizado
2. breve resumo do escopo definido
3. lista curta de ambiguidades remanescentes, se houver

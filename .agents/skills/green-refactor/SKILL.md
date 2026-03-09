---
name: green-refactor
description: Use esta skill quando os testes RED da feature já existirem e a próxima etapa for implementar o código mínimo para fazê-los passar, seguida de refatoração segura. Não use esta skill para criar SPEC, redefinir requisitos ou escrever a primeira versão dos testes.
---

# Objetivo

Implementar o mínimo necessário para passar nos testes da feature e, em seguida, refatorar com segurança, preservando o comportamento definido pela SPEC.

# Leia antes de agir

Leia nesta ordem:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/architecture/SDD.md`
4. `docs/architecture/TDD.md`
5. `features/<feature>/SPEC.md`
6. testes recém-criados para a feature
7. código existente relacionado

# Quando esta skill deve ser usada

Use esta skill quando:

- a SPEC estiver estável
- o `DOCKER_PREFLIGHT` já tiver sido validado pela skill `repo-automation`
- os testes RED já tiverem sido escritos
- a feature estiver pronta para a etapa GREEN

# Quando esta skill NÃO deve ser usada

Não use esta skill para:

- começar por código sem testes
- ampliar a feature por conta própria
- alterar a arquitetura central sem necessidade explícita
- reescrever a SPEC para justificar o código
- fazer refatorações amplas fora do escopo da feature

# Regras obrigatórias

- Primeiro faça os testes passarem com o menor código possível.
- Só depois refatore.
- Preserve contratos, nomes e limites arquiteturais do projeto.
- Use sempre o nome **AIgnt-Synapse-Flow** e deixe claro, ao menos uma vez, que ele é a engine própria de pipeline do AIgnt OS.
- Mantenha compatibilidade com o MVP:
  - pipeline linear
  - runtime dual simples
  - memória semântica advisory
  - observabilidade local
- Não introduza novas dependências sem necessidade clara.

# Estratégia GREEN

1. Rode mentalmente ou localmente os testes relevantes.
2. Implemente o menor código possível para passar.
3. Evite abstrações prematuras.
4. Valide que o comportamento corresponde à SPEC.

# Estratégia REFACTOR

Depois de verde:

1. remova duplicação
2. melhore nomes
3. extraia funções/coerência de módulos
4. preserve contratos e testes
5. não aumente escopo da feature

# Pontos de atenção no AIgnt OS

Tenha cuidado especial com:

- parsing em camadas
- separação entre output bruto e limpo
- transições da state machine
- persistência de runs e step_status
- código assíncrono em adapters e worker
- geração de `RUN_REPORT.md`

# Critérios de parada

Pare e sinalize quando:

- os testes parecerem errados ou contraditórios com a SPEC
- a implementação exigir mudança arquitetural relevante
- a feature estiver grande demais para o recorte atual
- for necessário mexer em múltiplas áreas fora do escopo definido

# Checklist de qualidade

Antes de encerrar, confirme:

- os testes estão verdes
- a implementação ficou mínima e legível
- a refatoração não quebrou contratos
- o escopo permaneceu controlado
- notas relevantes da feature foram registradas

# Saída final esperada

Entregue:

1. código da feature implementado
2. refatoração concluída
3. resumo curto do que foi alterado
4. riscos remanescentes ou follow-ups, se houver

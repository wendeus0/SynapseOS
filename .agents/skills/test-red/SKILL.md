---
name: test-red
description: Use esta skill quando existir uma SPEC aprovada para a feature atual e a próxima etapa for escrever testes RED antes de qualquer código de produção. Não use esta skill para criar SPEC, implementar o código da feature ou fazer refatoração ampla.
---

# Objetivo

Escrever testes que falham e que expressem corretamente o comportamento exigido pela SPEC da feature.

# Leia antes de agir

Leia nesta ordem:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/architecture/TDD.md`
4. `docs/architecture/SPEC_FORMAT.md`
5. `features/<feature>/SPEC.md`
6. arquivos de teste e código já existentes relacionados à feature, se houver

# Quando esta skill deve ser usada

Use esta skill quando:

- a `SPEC.md` da feature estiver pronta
- o `DOCKER_PREFLIGHT` já tiver sido validado pela skill `repo-automation`
- a feature ainda não tiver testes adequados
- a equipe quiser iniciar o ciclo RED → GREEN → REFACTOR

# Quando esta skill NÃO deve ser usada

Não use esta skill para:

- criar ou alterar a SPEC por iniciativa própria
- implementar código de produção
- refatorar código de produção além do mínimo necessário para preparar o teste
- “consertar” testes para que passem sem base na SPEC

# Regras obrigatórias

- Escreva testes **antes** do código de produção.
- Os testes devem refletir a `SPEC.md`, não suposições novas.
- Se a SPEC estiver ambígua, pare e sinalize.
- Mantenha os testes pequenos, legíveis e focados.
- Prefira começar por testes unitários; adicione integração quando a feature exigir.
- Não cubra cenários fora do escopo da feature.

# Estratégia

1. Extraia da SPEC:
   - comportamento principal
   - critérios de aceite
   - casos de erro
2. Converta isso em casos de teste pequenos.
3. Organize os testes por nível adequado:
   - unit
   - integration
   - pipeline
4. Garanta que os testes falham pelos motivos certos.
5. Não implemente o código da feature nesta etapa.

# Convenções para o AIgnt OS

Priorize testes para:

- contratos Pydantic
- validação do SPEC híbrido
- state machine
- parsing robusto
- adapters CLI
- decisões do supervisor
- artefatos e persistência de run

# Checklist de qualidade

Antes de encerrar, confirme:

- há rastreabilidade clara entre SPEC e testes
- os nomes dos testes expressam comportamento
- os testes falham no estado atual
- não há implementação acoplada escondida no teste
- a cobertura ficou restrita ao escopo da feature

# Saída final esperada

Entregue:

1. arquivos de teste criados/atualizados
2. resumo do que os testes cobrem
3. nota explícita de que a etapa está em RED

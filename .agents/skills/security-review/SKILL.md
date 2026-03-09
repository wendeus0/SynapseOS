---
name: security-review
description: Use esta skill quando a tarefa envolver análise de segurança, identificação de riscos e mitigação em código, Docker, workflows, scripts operacionais, Agents e Skills. Não use esta skill para criar SPEC de feature, implementar lógica de produto ou ser a principal responsável por editar a automação operacional do repositório.
---

# Objetivo

Realizar revisão de segurança prática e objetiva sobre mudanças no repositório, cobrindo:
- código Python
- Dockerfile / docker-compose / build container
- workflows de CI/CD
- scripts operacionais
- AGENTS.md
- skills em `.agents/skills/`

Esta skill atua como gate no estágio `SECURITY_REVIEW`, imediatamente antes de `REPORT` e `COMMIT` no fluxo oficial.

# Leia antes de agir

Leia nesta ordem:
1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/architecture/SDD.md`
4. `docs/architecture/TDD.md`
5. `docs/architecture/IMPLEMENTATION_STACK.md`
6. arquivos alterados pela feature atual
7. `.github/workflows/*`, `Dockerfile`, `docker-compose.yml`, `scripts/*`, `.agents/skills/*`

# Quando esta skill deve ser usada

Use esta skill quando:
- houver mudança em workflow, Docker, scripts ou automação operacional
- houver mudança em Agents ou Skills
- for necessário produzir análise de riscos e mitigação
- for necessário revisar uma alteração antes de merge

# Quando esta skill NÃO deve ser usada

Não use esta skill para:
- criar SPECs de feature
- escrever testes RED como etapa principal
- implementar a automação operacional do repositório do zero
- substituir a skill `repo-automation` como agente executor principal de workflows e scripts

# Escopo da revisão

Avalie no mínimo:
- privilégios excessivos em workflows
- execução arbitrária de comandos
- uso inseguro de secrets/tokens
- comandos destrutivos ou não validados
- gatilhos inseguros em CI
- acoplamento perigoso entre Agents/Skills e scripts operacionais
- risco de supply chain em build de container
- permissões e contexto de execução local/CI

# Regras obrigatórias

- Foque em riscos reais e acionáveis.
- Evite alarmismo genérico.
- Aponte mitigação objetiva.
- Se a mudança for aceitável com ressalvas, diga isso claramente.
- Não amplie escopo para arquitetura de produto.
- Se algo não puder ser validado empiricamente, sinalize como limitação da análise.
- Considere o `DOCKER_PREFLIGHT` e os workflows operacionais como parte obrigatória da superfície de ataque a revisar.

# Estratégia

1. Identifique os arquivos alterados.
2. Classifique a superfície de ataque afetada:
   - código
   - build
   - workflow
   - scripts
   - agent behavior
3. Avalie riscos por severidade:
   - alto
   - médio
   - baixo
4. Produza mitigação prática.
5. Se necessário, recomende que a skill `repo-automation` aplique as correções.

# Saída final esperada

Entregue apenas:
1. riscos identificados
2. severidade de cada risco
3. mitigação recomendada
4. limitações da análise
5. parecer final:
   - aprovado
   - aprovado com ressalvas
   - requer correção antes de merge

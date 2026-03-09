---
name: repo-automation
description: Use esta skill quando a tarefa envolver automação de repositório e entrega operacional, incluindo fluxo de commit para Git/GitHub, build e rebuild de container, gatilhos de rebuild por mudança de código, validação de compatibilidade com a main e criação/ajuste de arquivos de workflow e scripts operacionais. Não use esta skill para criar SPEC de feature, escrever a primeira versão dos testes de domínio ou implementar lógica de produto sem relação com automação do repositório.
---

# Objetivo

Implementar automações operacionais do repositório de forma prática e mínima, cobrindo:
- fluxo de commit para Git/GitHub
- build de container
- rebuild acionado por mudanças relevantes
- validação contra `main`
- workflows e scripts operacionais

Esta skill é a responsável por executar e validar o estágio `DOCKER_PREFLIGHT` do fluxo oficial:

```text
DOCKER_PREFLIGHT → SPEC → TEST_RED → CODE_GREEN → REFACTOR → SECURITY_REVIEW → REPORT → COMMIT
```

# Leia antes de agir

Leia nesta ordem:
1. `AGENTS.md`
2. `CONTEXT.md`
3. `docs/architecture/SDD.md`
4. `docs/architecture/TDD.md`
5. `docs/architecture/IMPLEMENTATION_STACK.md`
6. `README.md`
7. `pyproject.toml`
8. `Dockerfile`, `docker-compose.yml`, `.github/workflows/*`, `scripts/*` se existirem

# Quando esta skill deve ser usada

Use esta skill quando a tarefa pedir qualquer combinação de:
- automatizar commits ou instruções de commit
- automatizar build de imagem/container
- rebuild automático por mudança de código
- checagem de alinhamento/compatibilidade com `main`
- criação ou ajuste de GitHub Actions, hooks, Makefile, scripts shell ou scripts Python operacionais

# Quando esta skill NÃO deve ser usada

Não use esta skill para:
- criar ou revisar `SPEC.md` de uma feature de domínio
- escrever a primeira versão de testes RED de lógica de produto
- implementar componentes centrais do AIgnt-Synapse-Flow
- alterar arquitetura central sem necessidade operacional clara

# Restrições obrigatórias

- Mantenha o escopo estritamente operacional.
- Prefira soluções simples e auditáveis.
- Não introduza plataformas pesadas cedo demais.
- Preserve compatibilidade com o MVP do AIgnt OS.
- Não substitua a estratégia de desenvolvimento feature-by-feature.
- Não altere a branch `main` diretamente.
- Não assuma acesso real ao GitHub ou à registry se isso não estiver disponível; nesse caso, gere arquivos prontos para uso.
- Considere `spec-editor` bloqueada até o `DOCKER_PREFLIGHT` ficar verde ou explicitamente validado.

# Resultados esperados

Quando aplicável, esta skill pode:
- criar ou ajustar `.github/workflows/*.yml`
- criar ou ajustar `Dockerfile`
- criar ou ajustar `docker-compose.yml`
- criar ou ajustar `Makefile`
- criar ou ajustar scripts em `scripts/`
- criar ou ajustar hooks/documentação operacional
- criar checagens para:
  - build do projeto
  - build da imagem
  - rebuild por arquivos alterados
  - validação contra `main`

# Estratégia recomendada

## 1. Descoberta mínima
- identifique os arquivos operacionais já existentes
- descubra como o projeto é executado e testado
- identifique quais arquivos devem disparar rebuild
- valide como o `DOCKER_PREFLIGHT` libera o início prático da feature

## 2. Commit flow
Implemente automação prática para o fluxo de commit, priorizando:
- padronização de mensagem
- validações locais antes do commit
- documentação simples de uso
- opcionalmente hook local se fizer sentido

## 3. Container build/rebuild
Implemente automação de build com o menor número de peças possível.
Prefira:
- script shell simples
- Makefile opcional
- workflow do GitHub Actions para CI

O `DOCKER_PREFLIGHT` deve deixar claro quando o ambiente foi:
- validado estaticamente;
- buildado;
- efetivamente iniciado em Docker, quando aplicável.

Política operacional:
- o preflight padrão em CI e no fluxo local deve ser leve;
- subir o container completo é exceção, não padrão;
- runtime completo deve acontecer só em workflow dedicado ou quando explicitamente pedido para boot/ciclo de vida/persistência/integração.

## 4. Gatilho de rebuild
Considere como relevantes para rebuild:
- `src/**`
- `pyproject.toml`
- `Dockerfile`
- `docker-compose.yml`
- arquivos de runtime/build
- dependências e scripts que afetem a imagem

## 5. Validação contra main
Implemente validação explícita contra `main`, por exemplo:
- fetch de `origin/main`
- merge-base / diff
- execução de checks no contexto da branch atual comparada à `main`
- falha controlada quando a branch estiver desatualizada ou incompatível

## 6. Segurança operacional
Ao tocar workflow, hooks, scripts, Agents ou Skills:
- minimize permissões
- evite execução arbitrária sem validação
- deixe comandos explícitos e revisáveis
- não introduza segredos hardcoded
- documente riscos e mitigação

# Prioridades de implementação

Ordem preferida:
1. validar contexto atual do repo
2. criar/ajustar workflow CI
3. criar script local de build/rebuild
4. criar validação contra `main`
5. padronizar commit flow
6. registrar riscos e mitigação

# Checklist de qualidade

Antes de encerrar, confirme:
- a automação realmente modifica arquivos operacionais do repo
- build/rebuild ficou acionável e claro
- o `DOCKER_PREFLIGHT` ficou explícito como requisito antes da feature
- a validação contra `main` está explícita
- não houve ampliação indevida de escopo
- riscos operacionais e de segurança foram identificados

# Saída final esperada

Entregue apenas:
1. o que foi alterado
2. como a automação de commit e build foi implementada
3. como o rebuild é acionado quando houver mudança de código
4. como a validação contra `main` foi feita
5. análise de segurança com riscos e mitigação

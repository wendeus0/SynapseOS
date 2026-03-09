---
name: git-flow-manager
description: Use esta skill quando a tarefa envolver operações finais de fluxo Git, incluindo revisão do estado da branch atual, organização do commit, push e abertura/preparação de pull request. Não use esta skill para automação Docker, criação de SPEC, escrita de testes RED, implementação de código de produto ou revisão de segurança.
---

# Objetivo

Executar e organizar o fluxo final de Git da feature atual, incluindo:
- revisão do estado da branch
- preparação de commit limpo
- execução de commit
- push da branch
- abertura ou preparação de pull request

# Escopo

Esta skill atua sobre:
- `git status`
- `git diff`
- `git log`
- `git add`
- `git commit`
- `git push`
- abertura/preparação de PR

Ela pode também:
- verificar se há arquivos fora de escopo
- sugerir ou montar título/descrição da PR
- parar o fluxo quando houver bloqueio real

# Quando esta skill deve ser usada

Use esta skill quando:
- a feature já foi implementada
- os testes/checks relevantes já foram executados
- o `security-review` já terminou
- for hora de commitar a feature
- for hora de fazer push
- for hora de abrir ou preparar a pull request

# Quando esta skill NÃO deve ser usada

Não use esta skill para:
- criar ou editar `SPEC.md`
- escrever testes RED
- implementar código
- refatorar
- auditar segurança
- fazer Docker preflight, build ou rebuild
- atualizar arquitetura ou ADRs por conta própria

# Leia antes de agir

Leia nesta ordem:
1. `AGENTS.md`
2. `CONTEXT.md`
3. `git status`
4. `git diff --stat`
5. `git diff`
6. `git log --oneline -n 10`
7. `features/<feature>/SPEC.md`, se houver
8. resultado mais recente do `security-review`, se disponível
9. `ERROR_LOG.md` e `PENDING_LOG.md`, se forem relevantes para a PR

# Regras obrigatórias

- Trabalhe apenas sobre a branch atual.
- Não commite arquivos irrelevantes.
- Não misture mudanças paralelas sem necessidade.
- Se houver bloqueio crítico, pare.
- Se houver pendência grave do `security-review`, não finalize commit/PR.
- Se houver ressalvas aceitáveis, deixe isso explícito na PR.
- Não altere código de produto nesta etapa, salvo ajuste mínimo estritamente necessário para organizar o commit.
- Não faça merge em `main`.
- Não faça squash/rebase/merge automaticamente sem pedido explícito.
- Prefira mensagens de commit curtas, claras e alinhadas ao escopo da feature.
- Se não houver acesso para abrir a PR de fato, gere o conteúdo pronto para uso manual.

# Processo

## Etapa 1 — revisão do estado atual
1. Verifique `git status`.
2. Verifique `git diff --stat`.
3. Verifique `git diff`.
4. Identifique se há arquivos fora do escopo da feature.

## Etapa 2 — preparação do commit
1. Separe apenas os arquivos relevantes.
2. Verifique se a feature está em estado aceitável para commit.
3. Elabore uma mensagem de commit objetiva.

## Etapa 3 — commit
1. Faça o commit apenas se o estado estiver adequado.
2. Se hooks bloquearem por dívida técnica fora de escopo, reporte isso claramente.
3. Só use bypass como `--no-verify` quando explicitamente necessário e deixe isso registrado na resposta.

## Etapa 4 — push
1. Faça push da branch atual.
2. Se houver problema de autenticação/acesso, pare e explique.

## Etapa 5 — pull request
1. Se possível, abra a PR.
2. Se não for possível, gere:
   - título da PR
   - descrição da PR
   - base branch
   - comandos manuais necessários

# Conteúdo esperado da pull request

A descrição da PR deve conter:
- objetivo da feature
- o que foi alterado
- validações executadas
- riscos/ressalvas, se houver
- o que ficou fora do escopo, se aplicável
- referência ao parecer do `security-review`, quando existir

# Critérios de parada

Pare e sinalize quando:
- houver arquivos alterados claramente fora do escopo
- houver pendência crítica do `security-review`
- a árvore estiver inconsistente
- houver conflito Git não resolvido
- não houver contexto suficiente para elaborar commit/PR coerentes

# Critérios de qualidade

Antes de encerrar, confirme:
- o commit representa apenas a feature atual
- a mensagem de commit está coerente
- a PR está clara e objetiva
- riscos e ressalvas relevantes foram mencionados
- nada fora de escopo foi incluído por acidente

# Saída final esperada

Entregue apenas:
1. se o commit foi realizado ou não
2. a mensagem de commit usada
3. se o push foi realizado ou não
4. se a pull request foi aberta ou não
5. título da PR
6. descrição da PR
7. arquivos incluídos
8. itens deixados de fora, e por quê
9. bloqueios, se houver

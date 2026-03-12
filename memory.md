# Current project state

## Global project state

- AIgnt OS continua como meta-orquestrador CLI-first; o AIgnt-Synapse-Flow segue como a engine propria de pipeline do projeto.
- A baseline operacional atual combina `DOCKER_PREFLIGHT` leve por padrao, fluxo container-first para o Codex, Branch Sync Gate e separacao entre memoria duravel (`memory.md`) e log operacional (`PENDING_LOG.md` e `ERROR_LOG.md`).
- A governanca de prompts dos agents segue formato contextual explicito, com contexto, leituras obrigatorias, objetivo, escopo, nao-faca, criterios de aceite e formato de entrega.
- O MVP de produto agora chega ate `DOCUMENT`: a F10 adicionou `RUN_REPORT.md` por run e o primeiro adapter real via `CodexCLIAdapter`.

## Local snapshot

- `main` local esta limpo e sincronizado com `origin/main` apos o merge da PR `#38` da `F12-codex-adapter-operational-hardening`.
- A worktree atual foi aberta na branch `chore/post-f12-handoff-logs-memory` apenas para consolidar `PENDING_LOG.md`, `ERROR_LOG.md` e `memory.md`.
- O MVP inicial de 10 features foi concluido; o follow-up `F12` tambem foi mergeado, fechando o hardening operacional do primeiro adapter real.

# Stable decisions

- `DOCKER_PREFLIGHT` continua obrigatorio antes da execucao pratica de uma feature; o modo padrao permanece leve.
- O Codex opera em fluxo container-first via `./scripts/dev-codex.sh`, separado do servico `aignt-os`, onde o AIgnt-Synapse-Flow roda como engine propria de pipeline do AIgnt OS.
- A Branch Sync Gate usa `./scripts/branch-sync-check.sh` para detectar drift e `./scripts/branch-sync-update.sh` apenas quando a worktree estiver limpa e segura para atualizacao.
- `memory.md` guarda memoria duravel e reaproveitavel; `PENDING_LOG.md` e `ERROR_LOG.md` guardam detalhe operacional da sessao.
- O `memory-curator` pode ser acionado por `$memory-curator encerrar conversa` ou `$memory-curator close session` para atualizar `memory.md` e gerar handoff de encerramento.
- Com `network-access = true`, `git push` e `gh pr create` devem ser tentados primeiro no sandbox; fallback fora do sandbox fica restrito a falha real de rede ou sandbox.
- O `CodexCLIAdapter` permanece o primeiro adapter real integrado; a F12 fixou classificacao operacional explicita para timeout, return code nao zero e bloqueios de launcher/container/autenticacao sem reabrir a pipeline.
- Os artefatos operacionais padrao em `.aignt-os/` devem permanecer fora do versionamento.

# Active fronts

- Fechar a chore `post-f12-handoff-logs-memory` no fluxo Git.
- Abrir a proxima frente pequena de produto depois do merge desta chore, com `F13-rich-cli-output` como candidata principal.

# Open decisions

- Decidir se `F13-rich-cli-output` fica restrita a enriquecer `aignt runtime status` com Rich ou se tambem inclui pequenos componentes visuais em outras saidas CLI.
- Decidir em momento futuro se o smoke autenticado do Codex deve virar gate obrigatorio; por ora o `401 Unauthorized` ficou classificado como bloqueio operacional externo e nao como requisito de produto.

# Recurrent pitfalls

- `memory.md` perde valor quando mistura decisao estavel com snapshot local ou log de conversa.
- `memory.md` e `PENDING_LOG.md` ficam rapidamente obsoletos quando merges e PRs mudam o estado real do repositório e o handoff nao e consolidado em seguida.
- `uv` pode falhar no sandbox por cache fora da workspace ou indisponibilidade de rede.
- `branch-sync-update` nao e seguro com worktree suja, mesmo quando o drift contra `main` parece pequeno.
- Subir `codex-dev` manualmente em paralelo ao launcher pode causar corrida operacional.
- Smoke real do Codex sem credencial valida falha por autenticacao (`401 Unauthorized`) mesmo com launcher/container saudavel; isso deve ser tratado como bloqueio operacional externo.

# Next recommended steps

- Promover a chore de handoff atual para alinhar logs e memoria com o estado pos-F12.
- Depois disso, abrir a `F13-rich-cli-output` via `spec-editor` como proxima frente de produto de baixo risco.
- Manter revisoes amplas de docs antigas fora do caminho critico, salvo quando bloquearem validacao real.

# Last handoff summary

- Read before acting: releia `AGENTS.md`, `CONTEXT.md`, `memory.md`, `PENDING_LOG.md`, `ERROR_LOG.md`, `git status` e `git diff --stat`.
- Current state: `main` esta sincronizado apos o merge da PR `#38`; a worktree atual existe apenas para consolidar logs e memoria duravel.
- Open points: promover a chore de handoff e, em seguida, abrir a proxima frente pequena de produto.
- Recommended next front: `F13-rich-cli-output`, mantendo o recorte inicial pequeno e centrado em melhoria visual da CLI com Rich.

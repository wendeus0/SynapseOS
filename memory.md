# Current project state

## Global project state

- AIgnt OS continua como meta-orquestrador CLI-first; o AIgnt-Synapse-Flow segue como a engine propria de pipeline do projeto.
- A baseline operacional atual combina `DOCKER_PREFLIGHT` leve por padrao, fluxo container-first para o Codex, Branch Sync Gate e separacao entre memoria duravel (`memory.md`) e log operacional (`PENDING_LOG.md` e `ERROR_LOG.md`).
- A governanca de prompts dos agents segue formato contextual explicito, com contexto, leituras obrigatorias, objetivo, escopo, nao-faca, criterios de aceite e formato de entrega.

## Local snapshot

- `main` local esta limpo e sincronizado com `origin/main` apos os merges das PRs `#38` e `#39`, no commit `68892b1`.
- Nao ha branch ativa de produto nem delta local pendente; a proxima sessao deve partir de `main` limpa.
- O MVP inicial de 10 features foi concluido; o follow-up `F12` tambem foi mergeado, fechando o hardening operacional do primeiro adapter real e o handoff pos-F12.

# Stable decisions

- `DOCKER_PREFLIGHT` continua obrigatorio antes da execucao pratica de uma feature; o modo padrao permanece leve.
- O Codex opera em fluxo container-first via `./scripts/dev-codex.sh`, separado do servico `aignt-os`, onde o AIgnt-Synapse-Flow roda como engine propria de pipeline do AIgnt OS.
- A Branch Sync Gate usa `./scripts/branch-sync-check.sh` para detectar drift e `./scripts/branch-sync-update.sh` apenas quando a worktree estiver limpa e segura para atualizacao.
- `memory.md` guarda memoria duravel e reaproveitavel; `PENDING_LOG.md` e `ERROR_LOG.md` guardam detalhe operacional da sessao.
- O `memory-curator` pode ser acionado por `$memory-curator encerrar conversa` ou `$memory-curator close session` para atualizar `memory.md` e gerar handoff de encerramento.
- Com `network-access = true`, `git push` e `gh pr create` devem ser tentados primeiro no sandbox; fallback fora do sandbox fica restrito a falha real de rede ou sandbox.
- O `CodexCLIAdapter` permanece o primeiro adapter real integrado; a F12 fixou classificacao operacional explicita para timeout, return code nao zero e bloqueios de launcher/container/autenticacao sem reabrir a pipeline.
- A avaliacao de ADR pos-F12 concluiu que o hardening operacional do Codex e a chore de handoff estendem decisoes ja cobertas por ADR-004, ADR-011 e ADR-012; nao ha ADR nova nem atualizacao pendente por ora.
- Os artefatos operacionais padrao em `.aignt-os/` devem permanecer fora do versionamento.

# Active fronts

- Abrir a proxima frente pequena de produto, com `F13-rich-cli-output` como candidata principal.
- Manter apenas follow-ups operacionais realmente bloqueantes fora da trilha principal de produto.

# Open decisions

- Decidir se `F13-rich-cli-output` fica restrita a enriquecer `aignt runtime status` com Rich ou se tambem inclui pequenos componentes visuais em outras saidas CLI.
- Decidir em momento futuro se o smoke autenticado do Codex deve virar gate obrigatorio; por ora o `401 Unauthorized` ficou classificado como bloqueio operacional externo e nao como requisito de produto.

# Recurrent pitfalls

- `memory.md` perde valor quando mistura decisao estavel com snapshot local ou log de conversa.
- `uv` pode falhar no sandbox por cache fora da workspace ou indisponibilidade de rede.
- `branch-sync-update` nao e seguro com worktree suja, mesmo quando o drift contra `main` parece pequeno.
- Subir `codex-dev` manualmente em paralelo ao launcher pode causar corrida operacional.
- Smoke real do Codex sem credencial valida falha por autenticacao (`401 Unauthorized`) mesmo com launcher/container saudavel; isso deve ser tratado como bloqueio operacional externo.

# Next recommended steps

- Abrir a `F13-rich-cli-output` via `spec-editor` como proxima frente de produto de baixo risco.
- Validar o recorte minimo da F13 em torno de `aignt runtime status`, sem misturar TUI completa ou Textual nesta abertura.
- Manter revisoes amplas de docs antigas fora do caminho critico, salvo quando bloquearem validacao real.

# Last handoff summary

- Read before acting: releia `AGENTS.md`, `CONTEXT.md`, `memory.md`, `PENDING_LOG.md`, `ERROR_LOG.md`, `git status` e `git diff --stat`.
- Current state: `main` esta limpa e sincronizada apos os merges das PRs `#38` e `#39`; nao ha delta local pendente nem ADR nova requerida pelo estado atual da obra.
- Open points: definir o recorte exato da `F13-rich-cli-output` e manter o smoke autenticado do Codex como follow-up operacional nao bloqueante.
- Recommended next front: `F13-rich-cli-output`, mantendo o recorte inicial pequeno e centrado em melhoria visual da CLI com Rich.

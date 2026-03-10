# Current project state

- Repository: AIgnt OS, um meta-orquestrador CLI-first com AIgnt-Synapse-Flow como engine propria de pipeline.
- Branch atual: `feat/memory-curator-skill`.
- Baseline recente: infraestrutura isolada do Codex introduzida e governanca de branch/skills endurecida.

# Stable decisions

- `DOCKER_PREFLIGHT` continua obrigatorio antes da execucao pratica de uma feature.
- O preflight padrao segue leve por padrao.
- O Codex opera em fluxo container-first via `codex-dev`, separado do runtime `aignt-os`.
- No ambiente atual do Codex com `network-access = true`, `git push` e `gh pr create` funcionam no sandbox como caminho operacional padrao; fallback fora do sandbox fica restrito a contingencia por falha real de rede/sandbox.
- A Branch Sync Gate usa `./scripts/branch-sync-check.sh` e `./scripts/branch-sync-update.sh` como caminho padrao e conservador.
- `debug-failure` faz diagnostico inicial de falhas; `session-logger` continua responsavel pelo log operacional detalhado.
- O caminho operacional padrao para checks/testes locais passa a ser `./scripts/commit-check.sh --sync-dev`, mantendo `uv` como gerenciador de ambiente e evitando dependencia de virtualenv legada do host.

# Active fronts

- Frente atual: criacao da skill `memory-curator` e introducao de `memory.md` como memoria duravel do repositorio.
- Estado atual: branch aberta, sem PR nesta frente ainda.

# Open decisions

- Validar se o job `branch-validation` continua correto em GitHub Actions real.

# Recurrent pitfalls

- `uv` pode falhar no sandbox por cache fora da workspace ou falta de rede.
- `.venv` legada pode apontar para interpreter invalido.
- Subir `codex-dev` manualmente em paralelo ao launcher pode causar corrida operacional.
- Branches com worktree suja impedem atualizacao segura pela Branch Sync Gate.

# Next recommended steps

- Finalizar a skill `memory-curator` e validar seu papel em `AGENTS.md`.
- Validar os checks operacionais ainda pendentes fora do sandbox quando aplicavel.
- Usar `memory.md` como resumo duravel e `PENDING_LOG.md`/`ERROR_LOG.md` como detalhe operacional.

# Last handoff summary

- O repositorio saiu da frente de isolamento do Codex com security-review aprovado.
- A Branch Sync Gate foi incorporada com mitigacao final das ressalvas baixas.
- `debug-failure` foi introduzido para diagnostico inicial de falhas.
- A nova frente aberta e a criacao da skill `memory-curator`.

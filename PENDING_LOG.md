# PENDING_LOG

## Pendencias abertas
- Documentar no fluxo local que `scripts/commit-check.sh` agora usa `uv run --no-sync` por padrao e requer `--sync-dev` para bootstrap explicito.
- Resolver a divida de formatacao global do repositório para que `ruff format --check .` possa voltar a ser gate completo sem ressalvas.

## Pontos de atencao futuros
- O hardening do runtime valida identidade do processo por marcador + token em `/proc/<pid>/cmdline`; isso continua Linux-first.
- A validacao do diretorio configuravel de estado e propositalmente basica no MVP e pode ser endurecida depois com ancora explicita no workspace.
- O runtime persistente continua propositalmente restrito a processo unico local, sem scheduler, distribuicao ou recuperacao avancada.

## Decisoes incorporadas recentemente
- A SPEC da feature passou a exigir validacao adicional da identidade do processo antes de `stop`.
- O estado do runtime passou a exigir escrita atomica, permissoes restritas e tratamento seguro de corrupcao/adulteracao local.
- O `commit-check.sh` deixou de sincronizar dependencias dev como efeito colateral obrigatorio.
- O security-review final considerou a feature `aprovado com ressalvas`, com apenas riscos baixos residuais no escopo do MVP.

## Itens que podem virar novas features ou ajustes futuros
- Endurecimento adicional do path de estado para restringir explicitamente a uma raiz confiavel do workspace.
- Melhoria de portabilidade do runtime alem de Linux, caso isso entre no escopo futuro.
- Documentacao operacional curta para bootstrap local (`--sync-dev`) e para o lifecycle do runtime persistente.
- Limpeza operacional do repositório para remover debt de formatacao fora do escopo desta feature.

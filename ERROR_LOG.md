# ERROR_LOG

## 2026-03-09 - Docker preflight bloqueado no sandbox
- Contexto: validacao do `DOCKER_PREFLIGHT` da worktree antes de iniciar a feature.
- Acao/comando relacionado: `./scripts/docker-preflight.sh`
- Erro observado: build falhou com `Docker daemon is not accessible`.
- Causa identificada: limitacao de acesso ao daemon Docker no sandbox, nao erro do repositório.
- Acao tomada: reexecucao fora do sandbox; `compose config` e build passaram.
- Status: resolvido
- Observacao futura: manter diferenciacao explicita entre falha de sandbox e falha real do preflight.

## 2026-03-09 - Check local bloqueado por DNS no sandbox
- Contexto: execucao inicial de checks operacionais locais.
- Acao/comando relacionado: `./scripts/commit-check.sh --skip-branch-validation --skip-docker`
- Erro observado: `uv` falhou ao baixar dependencias com erro de DNS/resolucao.
- Causa identificada: restricao de rede no sandbox.
- Acao tomada: reexecucao fora do sandbox.
- Status: resolvido
- Observacao futura: manter cache local e usar elevacao apenas quando necessario para distinguir ambiente de repositório.

## 2026-03-09 - commit-check sem dependencias dev preparadas
- Contexto: validacao operacional local em ambiente limpo.
- Acao/comando relacionado: `./scripts/commit-check.sh --skip-branch-validation --skip-docker`
- Erro observado: `error: Failed to spawn: ruff`.
- Causa identificada: o script assumia ferramentas dev instaladas sem sincronizacao previa.
- Acao tomada: ajuste operacional posterior para tornar o sync explicito com `--sync-dev`, removendo instalacao obrigatoria do fluxo padrao.
- Status: resolvido
- Observacao futura: documentar uso de `--sync-dev` para bootstrap local.

## 2026-03-09 - Runtime stop aceitava risco de sinalizar PID arbitrario
- Contexto: implementacao inicial do runtime persistente minimo.
- Acao/comando relacionado: testes de seguranca do runtime (`pytest tests/integration/test_runtime_cli.py tests/unit/test_runtime_state.py tests/unit/test_runtime_service_security.py`)
- Erro observado: `stop` confiava em PID persistido e nao validava identidade adicional do processo.
- Causa identificada: hardening local ausente na primeira implementacao do lifecycle.
- Acao tomada: adicao de `process_identity`, validacao via `/proc/<pid>/cmdline`, falha segura em mismatch, escrita atomica e permissoes restritas no arquivo de estado.
- Status: resolvido
- Observacao futura: a validacao continua Linux-first e o endurecimento de path ainda e basico no MVP.

## 2026-03-09 - Formatação do repositório fora do escopo da feature
- Contexto: execucao do fluxo operacional completo.
- Acao/comando relacionado: `UV_CACHE_DIR=.cache/uv uv run ruff format --check .`
- Erro observado: arquivos preexistentes fora do padrao de formatacao.
- Causa identificada: divida de formatacao ja presente no repositório, nao ligada ao runtime persistente.
- Acao tomada: nenhuma nesta feature; mantido como pendencia separada.
- Status: aberto
- Observacao futura: tratar em ajuste operacional ou limpeza dedicada antes de usar o check completo como gate global.

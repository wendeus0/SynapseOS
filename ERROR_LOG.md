# ERROR_LOG

## 2026-03-09 06:00 - Falha de `uv run` por cache fora da workspace

- Contexto: validação operacional local durante revisão e correção de workflows/scripts.
- Ação/comando relacionado: `uv run pytest tests/unit/test_repo_automation.py`
- Erro observado: falha ao inicializar cache em `/home/g0dsssp33d/.cache/uv` com `Permission denied`.
- Causa identificada: ambiente sandbox bloqueando escrita no cache padrão do `uv` fora da workspace.
- Ação tomada: validação local migrou para `.venv` existente e, quando possível, para `UV_CACHE_DIR` dentro da workspace.
- Status: contornado na sessão.
- Observação futura: validar fora do sandbox se o fluxo padrão de `uv run` está consistente no ambiente do operador.

## 2026-03-09 06:02 - Falha de rede ao sincronizar dependências com `uv`

- Contexto: tentativa de executar `commit-check` e sincronizar dependências pelo caminho operacional padrão.
- Ação/comando relacionado: `uv sync --locked --extra dev`, `uv run ...`, `./scripts/commit-check.sh --skip-branch-validation --skip-docker`
- Erro observado: falha para baixar `pyyaml==6.0.3` por `dns error` e `Temporary failure in name resolution`.
- Causa identificada: ambiente sem acesso de rede para resolver/baixar dependências.
- Ação tomada: reexecução fora do sandbox quando necessário; validações locais alternativas usaram `.venv` já presente e testes com `PYTHONPATH=src`.
- Status: contornado na sessão; não validado pelo caminho de rede real.
- Observação futura: revalidar `uv sync --locked --extra dev` em ambiente com rede antes de concluir o ciclo operacional completo.

## 2026-03-09 06:04 - `commit-check` sem dependências dev preparadas

- Contexto: validação operacional local em ambiente limpo.
- Ação/comando relacionado: `./scripts/commit-check.sh --skip-branch-validation --skip-docker`
- Erro observado: `error: Failed to spawn: ruff`.
- Causa identificada: o script assumia ferramentas dev instaladas sem sincronização prévia.
- Ação tomada: ajuste operacional posterior para tornar o bootstrap explícito com `--sync-dev`, mantendo `uv run --no-sync` no fluxo padrão.
- Status: resolvido.
- Observação futura: documentar o uso de `--sync-dev` para bootstrap local.

## 2026-03-09 06:08 - `pytest` da `.venv` sem `PYTHONPATH=src`

- Contexto: execução local de testes após corrigir baseline operacional.
- Ação/comando relacionado: `./.venv/bin/pytest`
- Erro observado: `ModuleNotFoundError: No module named 'aignt_os'` em testes de config, contracts e CLI.
- Causa identificada: execução local usando `.venv` sem instalar o pacote ou sem `PYTHONPATH=src`; o caminho operacional do CI continua sendo `uv run pytest`.
- Ação tomada: validação local da suíte foi feita com `PYTHONPATH=src ./.venv/bin/pytest`.
- Status: contornado na sessão.
- Observação futura: validar se vale padronizar explicitamente o import path local fora do fluxo `uv run`.

## 2026-03-09 - Docker preflight bloqueado no sandbox

- Contexto: validação do `DOCKER_PREFLIGHT` da worktree antes de iniciar a feature.
- Ação/comando relacionado: `./scripts/docker-preflight.sh`
- Erro observado: build falhou com `Docker daemon is not accessible`.
- Causa identificada: limitação de acesso ao daemon Docker no sandbox, não erro do repositório.
- Ação tomada: reexecução fora do sandbox; `compose config` e build passaram.
- Status: resolvido.
- Observação futura: manter diferenciação explícita entre falha de sandbox e falha real do preflight.

## 2026-03-09 - Check local bloqueado por DNS no sandbox

- Contexto: execução inicial de checks operacionais locais.
- Ação/comando relacionado: `./scripts/commit-check.sh --skip-branch-validation --skip-docker`
- Erro observado: `uv` falhou ao baixar dependências com erro de DNS/resolução.
- Causa identificada: restrição de rede no sandbox.
- Ação tomada: reexecução fora do sandbox.
- Status: resolvido.
- Observação futura: manter cache local e usar elevação apenas quando necessário para distinguir ambiente de repositório.

## 2026-03-09 - Runtime stop aceitava risco de sinalizar PID arbitrário

- Contexto: implementação inicial do runtime persistente mínimo.
- Ação/comando relacionado: testes de segurança do runtime (`pytest tests/integration/test_runtime_cli.py tests/unit/test_runtime_state.py tests/unit/test_runtime_service_security.py`)
- Erro observado: `stop` confiava em PID persistido e não validava identidade adicional do processo.
- Causa identificada: hardening local ausente na primeira implementação do lifecycle.
- Ação tomada: adição de `process_identity`, validação via `/proc/<pid>/cmdline`, falha segura em mismatch, escrita atômica e permissões restritas no arquivo de estado.
- Status: resolvido.
- Observação futura: a validação continua Linux-first e o endurecimento de path ainda é básico no MVP.

## 2026-03-09 - Formatação do repositório fora do escopo da feature

- Contexto: execução do fluxo operacional completo.
- Ação/comando relacionado: `UV_CACHE_DIR=.cache/uv uv run ruff format --check .`
- Erro observado: arquivos preexistentes fora do padrão de formatação.
- Causa identificada: dívida de formatação já presente no repositório, não ligada ao runtime persistente.
- Ação tomada: nenhuma nesta feature; mantido como pendência separada.
- Status: aberto.
- Observação futura: tratar em ajuste operacional ou limpeza dedicada antes de usar o check completo como gate global.

## 2026-03-09 08:40 - `.venv` local estava quebrada para executar `pytest`

- Contexto: tentativa de validar a feature de runtime persistente após integrar a branch no merge operacional.
- Ação/comando relacionado: `PYTHONPATH=src ./.venv/bin/pytest tests/integration/test_runtime_cli.py tests/unit/test_runtime_service_security.py tests/unit/test_runtime_state.py`
- Erro observado: `bad interpreter` apontando para `/home/g0dsssp33d/work/projetcs/aignt-os/.venv/bin/python3`.
- Causa identificada: virtualenv preexistente criada com caminho antigo/incorreto.
- Ação tomada: a validação migrou para um ambiente local novo dedicado (`.venv-codex-runtime`).
- Status: contornado na sessão.
- Observação futura: recriar ou remover a `.venv` antiga para evitar falso negativo em validações locais.

## 2026-03-09 08:42 - `uv run pytest` não enxergou dependências de runtime após `uv sync`

- Contexto: validação da suíte específica do runtime persistente depois de sincronizar dependências dev.
- Ação/comando relacionado: `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run pytest tests/integration/test_runtime_cli.py tests/unit/test_runtime_service_security.py tests/unit/test_runtime_state.py`
- Erro observado: `ModuleNotFoundError: No module named 'typer'` durante a coleta.
- Causa identificada: o runner usado pelo `uv run` permaneceu desalinhado com o ambiente esperado para a sessão.
- Ação tomada: instalação do projeto e extras de desenvolvimento em uma virtualenv local dedicada (`.venv-codex-runtime`) e reexecução da suíte por esse ambiente.
- Status: contornado na sessão.
- Observação futura: validar se o fluxo preferido do projeto para testes locais deve ser `uv run` ou uma virtualenv explícita quando houver sandbox/ambiente misto.

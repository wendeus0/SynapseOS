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

- Contexto: tentativa de executar `commit-check` pelo caminho operacional padrão.
- Ação/comando relacionado: `uv sync` / `uv run ...`
- Erro observado: falha para baixar `pyyaml==6.0.3` por `dns error` e `Temporary failure in name resolution`.
- Causa identificada: ambiente sem acesso de rede para resolver/baixar dependências.
- Ação tomada: validações locais passaram a usar `.venv` já presente e testes com `PYTHONPATH=src`.
- Status: contornado na sessão; não validado pelo caminho de rede real.
- Observação futura: revalidar `uv sync --locked --extra dev` em ambiente com rede antes de concluir o ciclo operacional completo.

## 2026-03-09 06:08 - `pytest` da `.venv` sem `PYTHONPATH=src`

- Contexto: execução local de testes após corrigir baseline operacional.
- Ação/comando relacionado: `./.venv/bin/pytest`
- Erro observado: `ModuleNotFoundError: No module named 'aignt_os'` em testes de config, contracts e CLI.
- Causa identificada: execução local usando `.venv` sem instalar o pacote ou sem `PYTHONPATH=src`; o caminho operacional do CI continua sendo `uv run pytest`.
- Ação tomada: validação local da suíte foi feita com `PYTHONPATH=src ./.venv/bin/pytest`.
- Status: contornado na sessão.
- Observação futura: validar se vale padronizar explicitamente o import path local fora do fluxo `uv run`.

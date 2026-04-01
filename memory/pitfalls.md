# Pitfalls — SynapseOS

## Armadilhas recorrentes

### Branch e Git

1. **Reuso de branch mergeada** — Nunca reutilizar branch de feature já mergeada para drafts novos. Usar `draft/*` ou `archive/*`.
2. **Drift não detectado** — Rodar `./scripts/branch-sync-check.sh` cedo e manter worktree limpa antes de commit/push/PR.
3. **Delta misto em PR** — Quando inevitável, consolidar handoff durável e artefatos mínimos imediatamente após merge.

### Docker e ambiente

4. **Sandbox vs real** — Diferenciar falha de sandbox (rede, Docker daemon) de falha real do repositório.
5. **Worktree fria** — Sincronizar `uv sync --locked --extra dev` antes de rodar testes que carregam `conftest.py`.
6. **Wrappers quebrados** — Prefira `python -m pytest`/`python -m mypy` via `uv` em vez de wrappers da `.venv`.

### Testes e TDD

7. **Fixtures ANSI** — Fixtures com ANSI armazenados como escape literal requerem `unicode_escape=True` no helper.
8. **Monkeypatch legacy** — Ao ampliar helpers de CLI, preservar assinatura compatível ou atualizar doubles legados.
9. **mypy em tests** — `tests/` tem override explícito; não aplicar strict mode da `src/` na árvore de testes.

### CI e gates

10. **repo-checks local** — Rodar equivalente local do gate amplo antes de concluir PRs grandes.
11. **ruff format global** — Revalidar após mudanças amplas de documentação/baseline.
12. **PR body inline** — Usar `--body-file` em vez de `--body` quando houver Markdown com backticks.

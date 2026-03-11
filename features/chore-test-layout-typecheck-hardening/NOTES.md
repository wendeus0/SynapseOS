# Notes

- Esta chore existe para corrigir um erro operacional persistente fora do fluxo de produto.
- O alvo principal é a colisao de namespace entre `conftest.py` em subarvores de `tests/`.
- A mitigação final combinou package markers em `tests/` com override explícito do `mypy` para `tests` e `tests.*`.
- O contrato strict de `mypy` continua aplicado ao pacote `src/aignt_os`; a arvore de testes fica fora desse contrato nesta chore.

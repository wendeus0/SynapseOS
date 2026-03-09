# NOTES

- O runtime persistente permanece propositalmente restrito a processo unico local no MVP.
- O hardening da identidade do processo usa marcador + token em `/proc/<pid>/cmdline`, com dependencia Linux-first aceita no escopo atual.
- O `commit-check.sh` passou a usar `uv run --no-sync` por padrao; `--sync-dev` ficou explicito para bootstrap local.
- A divida global de formatacao do repositório ficou fora desta entrega e deve ser tratada separadamente.

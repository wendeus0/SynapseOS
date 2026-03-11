# NOTES

- A F04 foi aberta isoladamente em `feature/f04-parsing-engine-mvp` para evitar conflito com mudancas locais de docs e skills na worktree principal.
- O recorte fica intencionalmente anterior a F05: esta feature prepara cleaner/extractor/validator, mas nao define ainda o adapter async nem subprocess orchestration.
- A implementacao minima usa um contrato proprio de parsing com `stdout_raw`, `stdout_clean` e `artifacts`, mantendo a separacao entre output bruto e limpo sem ampliar `CLIExecutionResult`.
- O hardening local do parser passou a normalizar linguagem de fences para lowercase, canonizar `py` para `python` e impor limites fixos de tamanho/volume no MVP.
- A limpeza de ruido operacional ficou deliberadamente conservadora neste recorte: remove sequencias ANSI e linhas de transporte explicitamente conhecidas, preservando texto semantico generico para parsers mais especificos no futuro.

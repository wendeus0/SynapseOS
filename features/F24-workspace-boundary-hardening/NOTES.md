# F24 Notes

- A F24 fecha apenas `G-05` e o restante publico de `G-10` apos a F23; ela nao reabre masking textual, migrations, auth ou runtime.
- O root confiavel do workspace no MVP sera `AppSettings.workspace_root`, com default em `Path.cwd()` e override por ambiente para testes e execucoes controladas.
- SPEC fora dessa root deve ser tratada como indisponivel (`Not found`) para nao confirmar existencia de arquivos externos ao host.
- A listagem publica de artifacts deve filtrar entradas escapadas; bloquear apenas no preview nao e suficiente para o boundary publico.
- `raw.txt` continua privado e fora de qualquer preview publico.

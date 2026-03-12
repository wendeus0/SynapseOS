# F23 Notes

- A F23 e a primeira frente pos-`F22` do programa de guardrails e fica deliberadamente restrita a `G-01 + G-02 + G-04`.
- O objetivo e criar uma fundacao compartilhada de sanitizacao, nao resolver todo o backlog de seguranca da IDEA-001.
- `stdout_raw`, `stderr_raw`, `raw_output` e `raw.txt` permanecem intactos por contrato; o endurecimento acontece apenas em superficies limpas e publicas.
- `ParsedOutput.stdout_clean` deve ser endurecido sem quebrar a extracao atual de artifacts, para evitar regressao silenciosa no parsing.
- `AppSettings` recebe configuracao de patterns de segredo para extensibilidade; defaults seguros ficam versionados no codigo.
- AST scanning, migrations, audit trail, rate limiting, circuit breaker e auth ficam explicitamente fora de escopo desta frente.


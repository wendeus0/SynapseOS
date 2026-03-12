# F13 Notes

- A F13 e a primeira adocao de Rich em `src/`, mas o recorte fica intencionalmente restrito a `aignt runtime status`.
- O foco e melhorar a legibilidade operacional da CLI sem alterar o lifecycle do runtime nem abrir uma TUI.
- A saida deve continuar legivel em captura de teste e em ambiente sem TTY; cor e estilo sao bonus, nao dependencia funcional.
- O comando `runtime status` pode expor o PID quando houver runtime ativo, porque esse dado ja existe no estado persistido e aumenta utilidade operacional.
- Casos inconsistentes devem continuar em `stderr` com exit code de falha para nao quebrar o contrato operacional existente.
- O security review desta frente fechou sem ressalvas: o delta so reorganiza apresentacao de dados ja existentes e nao adiciona subprocesso, shell, leitura nova de path ou dependencia extra.

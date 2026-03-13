# F38 Notes

- A `F38` endurece apenas o state-dir compartilhado de runtime/auth/circuit-breaker.
- O trust-root escolhido e `workspace_root`, porque o projeto ja usa esse boundary para SPEC e artifacts.
- O recorte preserva a superficie publica existente; a mudanca visivel e apenas a rejeicao previsivel de configuracao insegura.

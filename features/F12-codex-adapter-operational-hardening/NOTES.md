# F12 Notes

- A F12 e um follow-up pequeno da F10, restrito ao hardening operacional do `CodexCLIAdapter`.
- O foco nao e expandir o produto, e sim tornar explicito o smoke real minimo do primeiro adapter real do AIgnt-Synapse-Flow.
- `DOCKER_PREFLIGHT` deve voltar ao centro desta frente porque a validacao pratica depende do launcher container-first.
- Se o problema encontrado for de ambiente e nao de codigo, o fluxo deve parar e encaminhar para `debug-failure` ou `repo-automation`.
- O hardening foi mantido isolado no adapter: `CLIExecutionResult` continua sendo o contrato de execucao, enquanto a classificacao operacional do Codex fica em `CodexExecutionAssessment`.
- O smoke local real de `./scripts/dev-codex.sh -- exec --color never "Reply with OK only."` confirmou o launcher/container-first e falhou por autenticacao ausente (`401 Unauthorized: Missing bearer or basic authentication in header`), nao por erro do adapter nem por falha do `DOCKER_PREFLIGHT`.
- Para esta frente, `DOCKER_PREFLIGHT` e obrigatorio antes de qualquer smoke pratico do Codex em container; os testes de integracao com `docker` fake nao substituem esse gate operacional.

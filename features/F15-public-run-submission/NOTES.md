# F15 Notes

- A F15 fecha a lacuna entre o dispatch interno ja existente e a CLI publica.
- O foco e expor submit por caminho de SPEC, nao por prompt cru.
- A frente deve reutilizar o `RunDispatchService` e o runtime dual sem abrir nova camada de servico.
- A SPEC precisa ser validada antes do dispatch, inclusive no modo `async`, para evitar persistencia de runs invalidas.
- O default operacional de `--stop-at` deve ser `SPEC_VALIDATION`, porque o pipeline publico ainda nao expoe executors suficientes para um happy path completo alem desse ponto.
- O contrato textual minimo e `run_id`, `status` e `mode`; qualquer taxonomia global de erro mais rica fica para a F21.
- O security review deve confirmar que a CLI so aceita SPEC explicitamente apontada, nao introduz shell novo e nao vaza traceback cru.
- A implementacao ficou localizada na CLI publica e no dispatch interno; nao houve mudanca em schema SQLite nem nova service layer.
- O security review fechou sem ressalvas no recorte atual: a frente apenas valida path/SPEC e reutiliza subprocessos e runtime ja existentes.
- A validacao local da frente fechou verde com a SPEC validada, `pytest` focado de dispatch/runs/runtime, `./scripts/commit-check.sh --no-sync --skip-branch-validation --skip-docker --skip-security` e `./scripts/security-gate.sh`.

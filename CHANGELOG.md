# Changelog

## 0.1.0

Primeira release tecnica coerente da etapa 2 do AIgnt OS.

Superficie publica consolidada:

- `aignt doctor` para diagnostico local advisory do fluxo minimo atual
- `aignt runs submit <spec_path>` com `--mode auto|sync|async` e `--stop-at`
- `aignt runs show <run_id>` para inspecao de runs persistidas
- `aignt runs show <run_id> --preview report`
- `aignt runs show <run_id> --preview <STEP_STATE>.clean`

Limites conhecidos:

- o quickstart oficial continua local e `sync-first`
- preview continua restrito a `RUN_REPORT.md` e `clean_output`
- Docker, runtime persistente pesado e credenciais externas continuam fora do fluxo minimo oficial

# F26 Notes

- A F26 cobre apenas `G-06` e `G-08`; ela nao reabre auth, rate limiting, circuit breaker ou preview de artifacts.
- A evolucao de schema fica autocontida no `RunRepository`, sem Alembic e sem nova infraestrutura de migration.
- `spec_hash` representa o SHA-256 do arquivo canonizado em disco no momento da criacao da run.
- Runs pendentes com `spec_hash` persistido agora falham ainda em `REQUEST` quando a SPEC muda antes de o worker iniciar a pipeline.
- `initiated_by` e obrigatorio para novas runs; caminhos internos usam default explicito em vez de inferencia implicita.
- O audit trail reutiliza `run_events` com novos `event_type`, sem nova tabela.

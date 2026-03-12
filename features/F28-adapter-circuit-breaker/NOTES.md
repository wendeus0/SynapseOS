# F28 Notes

- A F28 cobre apenas `G-09` e fica deliberadamente restrita ao `CodexCLIAdapter`, que e o unico adapter real integrado no baseline atual.
- O store do breaker deve usar arquivo local sob `runtime_state_dir`, reaproveitando o padrao atomico e as permissoes restritas ja usadas pelo runtime state.
- O breaker reage apenas a bloqueios operacionais ja classificados (`launcher_unavailable`, `container_unavailable`, `authentication_unavailable`).
- `timeout` e `return_code_nonzero` continuam sendo falhas nao operacionais do adapter e nao devem manter o breaker aberto.
- Merge aprovado deve seguir o fluxo normal: `branch-sync-guard` -> `test-red` -> `green-refactor` -> `quality-gate` -> `security-review` -> `report-writer` -> `branch-sync-guard` -> `git-flow-manager`.
- Branch sugerida: `feature/f28-adapter-circuit-breaker`
- Commit sugerido: `feat(security): add persisted adapter circuit breaker`

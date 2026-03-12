# F29 Notes

- A F29 cobre apenas a fundacao local de `G-11`, sem abrir socket, daemon remoto ou RBAC distribuido.
- O enforcement fica restrito a `runs submit` e `runtime start|run|stop`; comandos de leitura continuam locais e sem token.
- O registry deve persistir apenas hash SHA-256 de token, com escrita atomica e permissoes privadas.
- O rollout e opt-in: `auth_enabled=false` preserva o baseline atual.
- `initiated_by` passa a refletir o `principal_id` autenticado somente nos submits bem-sucedidos.
- Merge aprovado deve seguir o fluxo normal: `spec-editor` -> `test-red` -> `green-refactor` -> `quality-gate` -> `security-review` -> `report-writer` -> `branch-sync-guard` -> `git-flow-manager`.
- Branch sugerida: `feature/f29-auth-rbac-foundation`
- Commit sugerido: `feat(security): add opt-in cli auth rbac foundation`

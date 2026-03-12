# F27 Notes

- A F27 foi reduzida deliberadamente para cobrir apenas `G-07`.
- `G-09` fica fora desta SPEC porque o repositório ainda nao tem um contrato explicito de estado de health/cooldown entre runs no adapter layer.
- O merge aprovado deve seguir o fluxo normal: `branch-sync-guard` -> `test-red` -> `green-refactor` -> `quality-gate` -> `security-review` -> `report-writer` -> `branch-sync-guard` -> `git-flow-manager`.
- Branch sugerida: `feature/f27-adapter-concurrency-guard`
- Commit sugerido: `feat(security): limit adapter concurrency per process`

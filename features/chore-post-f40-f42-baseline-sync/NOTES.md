# Post-F40/F42 Notes

- Esta frente e propositalmente doc-only: nao altera CLI, runtime, TUI, auth nem persistencia.
- O menor recorte util agora e consolidar o baseline ja mergeado de `F40` e `F42` antes da proxima triagem de produto.
- `RUN_REPORT.md` raiz continua tratado como artefato de execucao; o artefato de fechamento desta frente e `features/chore-post-f40-f42-baseline-sync/REPORT.md`.
- A PR `#87` entrou com delta misto alem do recorte funcional da `F40`; a mitigacao escolhida aqui e registrar e sincronizar o handoff, nao reverter nem ampliar escopo.

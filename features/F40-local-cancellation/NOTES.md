# F40 Notes

- A feature ficou deliberadamente restrita a cancelamento local e gracioso de runs ja persistidas.
- A superficie publica entregue foi `aignt runs cancel <run_id>` e o atalho `k` no dashboard TUI atual.
- O baseline nao inclui cancelamento distribuido, fila remota, scheduler nem interrupcao forcada de subprocessos.
- O worker/runtime observa o sinal de cancelamento dentro do fluxo atual do AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS.

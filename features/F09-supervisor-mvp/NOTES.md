# F09 Notes

- A F09 expande o AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS, apenas ate `SECURITY`.
- O recorte escolhido mantem retry e reroute dentro da mesma execucao da pipeline para evitar resumir estado parcial entre polls do worker.
- O worker da F08 continua o hospedeiro do processamento assíncrono, mas a decisao de retry/rework fica concentrada na pipeline e no supervisor.
- Persistencia de decisao do supervisor entra como evento de run, nao como nova tabela.
- `DOCUMENT` e `RUN_REPORT.md` ficam explicitamente fora desta frente.

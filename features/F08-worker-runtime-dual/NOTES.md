# F08 Notes

## Decisoes locais

- O recorte da F08 fica backend-only: nenhuma CLI publica nova de runs entra nesta feature.
- O runtime foreground passa a poder hospedar polling de runs pendentes, mas o lifecycle publico `start/status/run/ready/stop` permanece o mesmo.
- O dispatch `auto` usa a prontidao do runtime para escolher entre execucao inline e enfileirada.
- O worker continua single-process e single-workspace no MVP.
- Retomada basica nesta feature significa apenas drenar runs ainda `pending` apos restart; nao ha replay implicito de run interrompida no meio.

## Validacao esperada

- testes unitarios do dispatch e do worker
- teste de integracao para dispatch `auto` resolvendo para `async`
- teste de integracao para worker consumindo run pendente via SQLite + filesystem
- checks locais padrao do repositorio

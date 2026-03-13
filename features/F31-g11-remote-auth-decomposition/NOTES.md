# F31 Notes

- A F31 e propositalmente doc-only: ela nao implementa transporte nem auth remota.
- O runtime atual continua local, sem socket ou IPC autenticado; isso passa a ser fato explicitado no backlog.
- `G-11` deixa de ser um bloco unico e passa a ser tratado como `local_cli_auth`, `resident_transport_auth` e `remote_multi_host_auth`.
- O bucket `resident_transport_auth` permanece apenas como proximo candidato de SPEC pequena; ele nao vira compromisso de implementacao nesta frente.
- Se o futuro bucket `resident_transport_auth` exigir ADR, isso deve ser triado numa frente propria, nao resolvido implicitamente aqui.

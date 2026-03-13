# F34 Notes

- O recorte fica restrito ao dispatch autenticado em `runs submit`; o lifecycle do runtime nao muda.
- O gate vale apenas quando o dispatch resolver para `async`; o caminho `sync` permanece inalterado.
- A ausencia de runtime residente pronto e tratada como precondicao operacional, nao como erro de uso.
- O fallback para estado legado sem `started_by` permanece obrigatorio para nao quebrar runtime ja persistido.

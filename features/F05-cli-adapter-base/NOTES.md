# NOTES

- A F05 evolui `CLIExecutionResult` para refletir o contrato real de execucao CLI assíncrona, sem mover contratos de parsing da F04 para o mesmo módulo.
- O `BaseCLIAdapter` fica restrito a montar comando, executar subprocesso async, capturar streams e aplicar sanitização leve; adapters reais continuam fora deste recorte.
- A sanitização local da F05 remove apenas ANSI e whitespace periférico para evitar conflito com o Parsing Engine MVP, que continua sendo o componente responsável por limpeza e extração mais profundas antes dos hand-offs do AIgnt-Synapse-Flow.

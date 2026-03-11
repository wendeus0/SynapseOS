# NOTES

- A F06 introduz a primeira camada de pipeline do AIgnt-Synapse-Flow em fake mode, acima da state machine, do SpecValidator e dos contratos ja implementados.
- O recorte deliberadamente executa trabalho real apenas em `SPEC_VALIDATION`, `PLAN` e `TEST_RED`; os estados anteriores permanecem como transicoes lineares da state machine.
- O hand-off da F06 fica em memoria e tipado, sem persistencia, sem CLI publica nova e sem chamar adapter real ou parser detalhado dentro da pipeline.

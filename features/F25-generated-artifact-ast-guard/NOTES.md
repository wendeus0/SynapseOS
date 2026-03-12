# F25 Notes

- A F25 cobre apenas `G-03` e nao reabre boundary de path, masking textual, migrations ou auth.
- O enforcement principal foi fechado no caminho real do produto: `PipelinePersistenceObserver` antes da promocao, com defesa adicional em `ArtifactStore`.
- A validacao de artifacts Python passou a ocorrer antes de `save_step_outputs()`, evitando residuo publico listavel quando o guardrail AST reprova o step.
- A heuristica de Python no MVP fica restrita a artifact names terminando em `.py`, `_py` ou `_python`.
- A denylist AST do MVP cobre `eval`, `exec`, `os.system` e `subprocess.*(..., shell=True)`, incluindo aliases simples.
- Falsos positivos fora dessa denylist ficam fora desta frente por decisao de escopo.

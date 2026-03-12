# F16 Notes

- A F16 aprofunda apenas `aignt runs show <run_id>`; nao abre novo comando nem preview de conteudo.
- O foco e reduzir o tempo ate o proximo passo de diagnostico usando somente dados ja persistidos.
- O resumo de diagnostico deve ser derivado de `RunRecord`, `RunStepRecord`, `RunEventRecord` e paths do `ArtifactStore`.
- `raw_output_path` e `clean_output_path` devem aparecer apenas como paths, sem leitura de arquivo.
- A feature nao deve alterar schema SQLite, `RunRepository`, `ArtifactStore` nem layout de artifacts.
- A saida precisa continuar assertavel sem TTY.
- O security review deve confirmar que a frente so expõe metadados e paths ja persistidos, sem leitura arbitraria de filesystem.
- O security review fechou sem ressalvas no recorte atual: a frente permanece restrita a rendering de metadados ja persistidos e nao adiciona shell, subprocesso ou leitura de conteudo de artifact.
- A validacao local da frente fechou verde com a SPEC validada, `pytest` focado de CLI rendering/runs, `./scripts/commit-check.sh --no-sync --skip-docker` e `./scripts/security-gate.sh`.

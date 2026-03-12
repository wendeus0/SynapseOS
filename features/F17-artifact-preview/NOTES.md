# F17 Notes

- A F17 mantem a superficie publica concentrada em `aignt runs show <run_id>` e adiciona apenas um seletor opcional: `--preview <target>`.
- O contrato inicial de preview fica deliberadamente restrito a `report` e `<STEP_STATE>.clean`; `raw_output` continua fora de escopo por seguranca e ruido operacional.
- O preview deve mostrar apenas o inicio do conteudo, com truncamento explicito apos no maximo 40 linhas, para evitar dump irrestrito de artifacts grandes.
- O preview e renderizado como painel adicional dentro de `aignt runs show <run_id>`, preservando o detalhe atual da run quando `--preview` nao e informado.
- O path exibido no preview fica relativo ao diretório de artifacts persistidos da propria run, evitando leitura arbitraria fora da arvore controlada pelo `ArtifactStore`.
- Se a leitura controlada de `clean_output` revelar necessidade real de mascaramento adicional de segredos, isso deve virar endurecimento explicito ou follow-up proprio, nao expansao silenciosa da F17.

# F17 Checklist

- [x] SPEC da F17 criada e validavel
- [x] Superficie publica mantida em `aignt runs show <run_id>` com um unico seletor `--preview`
- [x] Targets suportados restritos a `report` e `<STEP_STATE>.clean`
- [x] Preview truncado apos no maximo 40 linhas, sem dump irrestrito
- [x] REDs cobrindo rendering sem TTY, preview de report, preview de clean output, target invalido e artifact ausente
- [x] Regressao de `runs show <run_id>` sem `--preview` preservada
- [x] Quality gate local relevante executado com pytest, ruff e mypy
- [x] Security review local executado com parecer aprovado com ressalvas baixas
- [x] REPORT da feature consolidado

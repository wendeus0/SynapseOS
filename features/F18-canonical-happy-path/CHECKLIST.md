# F18 Checklist

- [x] SPEC da F18 criada e validavel
- [x] Comando inicial canonico definido como `aignt runs submit <spec_path> --mode sync --stop-at SPEC_VALIDATION`
- [x] Estado terminal de sucesso definido explicitamente para o recorte atual
- [x] Auditoria obrigatoria por `aignt runs show <run_id>` registrada na SPEC
- [x] Fora de escopo explicito para runtime persistente, doctor, onboarding e variantes pesadas
- [x] REDs cobrindo a sequencia canonica `runs submit -> runs show`
- [x] Implementacao minima ajustada para orientar `completed @ SPEC_VALIDATION` como happy path canonico
- [x] Quality gate local relevante executado com pytest, ruff e mypy
- [x] Security review local executado sem ressalvas
- [x] REPORT da feature consolidado

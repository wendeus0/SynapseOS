# F27 Checklist

- [x] SPEC da F27 criada e validavel
- [x] Recorte limitado a `G-07`
- [x] `AppSettings.max_concurrent_adapters` adicionado com default `4`
- [x] Guard compartilhado por processo introduzido no adapter layer
- [x] Limite aplicado antes da abertura do subprocesso em `BaseCLIAdapter.execute()`
- [x] REDs cobrindo espera por slot, compartilhamento entre instancias e override por ambiente
- [x] Quality gate local relevante executado com `pytest`, `ruff` e `mypy`
- [x] Security review local executado com parecer registrado
- [x] REPORT da feature consolidado

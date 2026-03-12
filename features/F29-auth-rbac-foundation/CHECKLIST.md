# F29 Checklist

- [x] SPEC da F29 criada e validavel
- [x] Recorte limitado ao baseline local de `G-11`
- [x] Registry privado de auth criado com escrita atomica e hash SHA-256
- [x] `AppSettings` exposto com `auth_enabled` e path derivado do registry
- [x] Comandos mutaveis da CLI protegidos por auth opt-in
- [x] Contrato publico de erro ampliado para authn/authz
- [x] `initiated_by` reutilizado com `principal_id` autenticado
- [x] REDs cobrindo registry, roles e comandos protegidos
- [x] Quality gate local relevante executado com `pytest`, `ruff` e `mypy`
- [x] Security review local executado com parecer registrado
- [x] REPORT da feature consolidado

---
id: F02-spec-engine-mvp
type: feature
summary: Validate the hybrid spec format.
inputs:
  - raw_request
outputs:
  - validated_spec
acceptance_criteria:
  - YAML front matter is required.
non_goals:
  - Implement the whole pipeline.
---

# Contexto

Documento de exemplo para validar o contrato minimo da SPEC.

# Objetivo

Confirmar que uma SPEC valida pode ser carregada e validada.

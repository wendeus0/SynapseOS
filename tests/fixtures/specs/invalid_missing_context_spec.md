---
id: F02-spec-engine-mvp
type: feature
summary: Invalid spec because Contexto section is missing.
inputs:
  - raw_request
outputs:
  - validated_spec
acceptance_criteria:
  - YAML front matter is required.
non_goals:
  - Implement the whole pipeline.
---

# Objetivo

Confirmar que a validacao falha quando Contexto nao existe.

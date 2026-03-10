---
id: F02-spec-engine-mvp
type: feature
summary: Validar a SPEC hibrida do AIgnt OS com parser de front matter YAML, checagem estrutural minima e bloqueio explicito quando o documento for invalido.
workspace: .
inputs:
  - docs/architecture/SPEC_FORMAT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - feature_spec_documents
outputs:
  - spec_validator_contract
  - parser_de_front_matter_yaml
  - validacao_estrutural_minima_da_spec
  - testes_red_e_fixtures_de_spec
constraints:
  - manter escopo estritamente na validacao da SPEC
  - nao implementar state machine, pipeline completa ou editor de SPEC
  - nao antecipar parsing generico de outputs fora do dominio da SPEC
  - preservar o fluxo spec-first do MVP
acceptance_criteria:
  - Existe validacao automatizada para detectar ausencia de front matter YAML obrigatorio.
  - Existe validacao automatizada para os campos minimos obrigatorios do YAML da SPEC.
  - Existe validacao automatizada para exigir ao menos um item em acceptance_criteria.
  - Existe validacao automatizada para exigir as secoes markdown Contexto e Objetivo.
  - Uma SPEC valida no formato oficial passa pela validacao e expõe dados estruturados consumiveis.
  - Uma SPEC invalida bloqueia explicitamente o avanco para a proxima etapa por erro verificavel.
non_goals:
  - gerar ou editar SPEC automaticamente
  - implementar state machine
  - implementar pipeline do AIgnt-Synapse-Flow
  - validar semantica profunda de cada secao narrativa
  - integrar adapters, worker ou persistencia
dependencies:
  - F01-bootstrap-contracts
---

# Contexto

O AIgnt OS adota desenvolvimento spec-first e depende de uma SPEC hibrida com front matter YAML obrigatorio. No estado atual do projeto, a arquitetura e o formato estao definidos em documentacao, mas ainda falta o primeiro incremento executavel que valide esse contrato antes da pipeline avancar.

Essa feature introduz apenas o menor recorte necessario para iniciar `SPEC_VALIDATION` no AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS, sem antecipar state machine, parser generico ou fluxo completo da pipeline.

# Objetivo

Entregar o primeiro validador de SPEC do projeto com:
- parser de front matter YAML;
- validacao dos campos minimos obrigatorios;
- checagem das secoes narrativas obrigatorias;
- erro explicito para bloquear o avanco quando a SPEC for invalida;
- testes automatizados com fixtures de SPEC valida e invalida.

# Escopo

## Incluido

- parser do front matter YAML no inicio de `SPEC.md`
- contrato minimo para resultado validado da SPEC
- validacao dos campos obrigatorios `id`, `type`, `summary`, `inputs`, `outputs` e `acceptance_criteria`
- exigencia de ao menos um item em `acceptance_criteria`
- exigencia das secoes markdown `Contexto` e `Objetivo`
- erro verificavel para casos de SPEC invalida
- fixtures e testes unitarios focados em SPEC valida e invalida

## Fora de escopo

- normalizacao ou reparo automatico de SPEC invalida
- editor interativo de SPEC
- validacao semantica completa de todas as secoes opcionais
- integracao com state machine, PLAN ou worker
- parsing generico de markdown fora do contrato minimo da SPEC

# Requisitos funcionais

1. O sistema deve rejeitar documento sem front matter YAML valido.
2. O sistema deve rejeitar SPEC sem qualquer um dos campos minimos obrigatorios do YAML.
3. O sistema deve rejeitar SPEC com `acceptance_criteria` vazio.
4. O sistema deve rejeitar SPEC sem a secao `Contexto`.
5. O sistema deve rejeitar SPEC sem a secao `Objetivo`.
6. O sistema deve retornar um resultado estruturado quando a SPEC estiver valida.
7. O erro de validacao deve ser verificavel por testes e adequado para bloquear o avanco da esteira.

# Requisitos nao funcionais

- A implementacao deve permanecer pequena o suficiente para 1 a 3 dias.
- O contrato deve ser simples e tipado com Pydantic v2.
- O parsing deve ser deterministico e sem dependencia de LLM.
- A feature nao deve introduzir dependencias operacionais pesadas.

# Casos de erro

- arquivo sem delimitadores de front matter
- YAML malformado
- campo obrigatorio ausente
- `acceptance_criteria` vazio
- secao `Contexto` ausente
- secao `Objetivo` ausente

# Cenarios verificaveis

## Cenario 1: SPEC valida

- Dado um documento com front matter YAML valido
- E com os campos minimos obrigatorios preenchidos
- E com as secoes `Contexto` e `Objetivo`
- Quando a SPEC for validada
- Entao o sistema retorna um resultado estruturado sem erro

## Cenario 2: ausencia de front matter

- Dado um documento sem front matter YAML
- Quando a SPEC for validada
- Entao a validacao falha de forma explicita

## Cenario 3: acceptance criteria vazio

- Dado um documento com `acceptance_criteria` vazio
- Quando a SPEC for validada
- Entao a validacao falha de forma explicita

## Cenario 4: secao obrigatoria ausente

- Dado um documento sem a secao `Contexto` ou `Objetivo`
- Quando a SPEC for validada
- Entao a validacao falha de forma explicita

# Observacoes

Esta feature nao entrega `SPEC_DISCOVERY` nem `SPEC_NORMALIZATION`. Ela entrega apenas o primeiro bloco de `SPEC_VALIDATION` necessario para permitir que o projeto passe de documentacao estavel para validacao executavel do contrato da feature.

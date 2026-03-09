# SPEC Format — AIgnt OS

## Decisão
O formato oficial da SPEC no MVP é **Markdown estruturado com front matter YAML obrigatório**.

## Por que não apenas JSON/YAML?
### Vantagens de schema formal puro
- validação forte,
- menos ambiguidade,
- contratos claros.

### Desvantagens
- pior legibilidade humana,
- menos contexto narrativo,
- maior rigidez para tarefas exploratórias.

## Por que não apenas Markdown livre?
### Vantagens
- ótima leitura humana,
- boa interpretação por IA.

### Desvantagens
- ambiguidade alta,
- parsing menos previsível,
- validação mais fraca.

## Modelo adotado
- YAML obrigatório para campos estruturais.
- Markdown obrigatório para contexto e nuances.
- Validação com Pydantic e JSON Schema.

## Campos mínimos obrigatórios no YAML
- `id`
- `type`
- `summary`
- `inputs`
- `outputs`
- `acceptance_criteria`

## Regras de validação
- sem YAML válido, não passa de `SPEC_VALIDATION`.
- `acceptance_criteria` deve conter pelo menos um item.
- `non_goals` deve existir, mesmo que vazio.
- a SPEC deve ter pelo menos seção `Contexto` e `Objetivo`.

## Relação com a esteira
- `SPEC_DISCOVERY` cria rascunho.
- `SPEC_NORMALIZATION` ajusta para formato oficial.
- `SPEC_VALIDATION` valida schema e seções obrigatórias.
- `PLAN` consome somente SPEC validada.

---
applyTo: "features/**/SPEC.md"
---

# SPEC — Instruções de contexto

## Formato obrigatório

Todo `SPEC.md` deve começar com YAML front matter válido:

```yaml
---
id: F<NN>-<slug-descritivo>
type: feature
summary: "Descrição concisa em uma linha"
inputs:
  - descrição do input 1
outputs:
  - descrição do output 1
acceptance_criteria:
  - critério verificável 1
  - critério verificável 2
non_goals:
  - o que explicitamente está fora do escopo
---
```

## Campos obrigatórios (o `SpecValidator` rejeitará sem eles)

- `id` — identificador único da feature (ex: `F03-state-machine-mvp`)
- `type` — deve ser `feature` (ou valor reconhecido pelo validator)
- `summary` — string não-vazia
- `inputs` — lista não-vazia
- `outputs` — lista não-vazia
- `acceptance_criteria` — lista não-vazia (cada item deve ser verificável por teste)
- `non_goals` — lista não-vazia (explicita o que está fora do escopo)

## Seções obrigatórias no corpo

Após o front matter, o corpo deve conter pelo menos:

```markdown
## Contexto

<por que esta feature existe, qual problema resolve>

## Objetivo

<o que será entregue, qual é o resultado esperado>
```

## Regras de conteúdo

- `acceptance_criteria`: cada item deve ser testável — evite critérios vagos como "funciona bem".
- `non_goals`: seja específico sobre o que NÃO será feito — evite "fora do escopo" genérico.
- Não invente funcionalidade já implementada se o código não existir ainda.
- Não amplie o escopo da SPEC durante a implementação — abra uma nova feature se necessário.

## Validação

Para validar uma SPEC localmente:

```bash
uv run --no-sync python -c "
from aignt_os.specs.validator import SpecValidator
v = SpecValidator()
result = v.validate_file('features/<feature>/SPEC.md')
print(result)
"
```

## Nomenclatura

- Diretório: `features/F<NN>-<slug>/`
- Arquivo: sempre `SPEC.md` (maiúsculo)
- `id` no front matter deve corresponder ao nome do diretório

## Proibições

- Não use placeholders vagos (`TBD`, `preencher depois`) sem marcar como `Premissa:`.
- Não omita `non_goals` — é obrigatório e operacionalmente importante para limitar scope creep.
- Não modifique uma SPEC após o início do `TEST_RED` sem registrar a mudança e realinhar os testes.

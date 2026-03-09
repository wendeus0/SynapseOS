# ADR-008 — Adotar Spec-Driven Development com SPEC híbrida

## Status
Aceito

## Contexto
O AIgnt OS precisa reduzir ambiguidade entre `REQUEST`, `PLAN`, `TEST_RED` e `CODE_GREEN`. Uma SPEC em texto livre dificulta validação, enquanto um schema puro prejudica legibilidade e contexto para humanos e IAs.

## Decisão
Adotar **Spec-Driven Development** com uma SPEC híbrida:
- Markdown estruturado para contexto e leitura humana/IA;
- front matter YAML obrigatório para campos estruturais;
- validação com Pydantic e JSON Schema.

A esteira passa a ser:

```text
REQUEST → SPEC_DISCOVERY → SPEC_NORMALIZATION → SPEC_VALIDATION → PLAN → TEST_RED → CODE_GREEN → REVIEW → SECURITY → DOCUMENT
```

## Consequências
### Positivas
- reduz ambiguidade antes da execução;
- melhora hand-offs entre agentes e etapas;
- facilita derivação de testes;
- aumenta previsibilidade da esteira;
- mantém o documento legível.

### Negativas
- exige normalização e validação adicionais;
- aumenta disciplina documental no pipeline;
- adiciona um novo artefato a versionar e manter.

## Alternativas consideradas
- SPEC apenas em Markdown livre;
- SPEC apenas em JSON/YAML;
- continuar com planejamento diretamente a partir do prompt cru.

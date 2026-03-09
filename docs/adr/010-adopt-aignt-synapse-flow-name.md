# ADR-010 — Adotar AIgnt-Synapse-Flow como nome formal da engine própria de pipeline

## Status
Aceito

## Contexto
O projeto já adotou o AIgnt-Synapse-Flow como conceito técnico central para coordenar estados, hand-offs, retries e integração com o supervisor, mas ainda sem nome formal padronizado nos documentos. Até aqui, os textos o descrevem apenas de forma genérica como engine própria de pipeline, o que dificulta comunicação operacional, rastreabilidade documental e padronização entre skills, ADRs e workflows.

Ao mesmo tempo, o fluxo oficial do projeto passou a exigir a sequência:

```text
DOCKER_PREFLIGHT → SPEC → TEST_RED → CODE_GREEN → REFACTOR → SECURITY_REVIEW → REPORT → COMMIT
```

Essa formalização aumenta a necessidade de um nome estável para o AIgnt-Synapse-Flow, a engine própria de pipeline do AIgnt OS.

## Decisão
Adotar **AIgnt-Synapse-Flow** como nome formal da engine própria de pipeline do AIgnt OS.

Regras derivadas:
- o termo `AIgnt-Synapse-Flow` deve ser usado nos documentos alterados quando o conceito for mencionado;
- ao menos uma vez por documento alterado, deve ficar explícito que o AIgnt-Synapse-Flow é a engine própria de pipeline do AIgnt OS;
- o fluxo oficial de trabalho por feature passa a ser documentado separadamente das subetapas internas do runtime.

## Consequências
### Positivas
- padroniza a comunicação entre arquitetura, skills e operação;
- reduz ambiguidade em discussões sobre o runtime interno;
- facilita rastreabilidade de responsabilidades entre `repo-automation`, `spec-editor` e `security-review`;
- melhora a clareza entre fluxo oficial da feature e estados internos da execução.

### Negativas
- exige atualização gradual de documentação existente;
- adiciona um novo termo de domínio que precisa ser aprendido pela equipe;
- pode gerar coexistência temporária entre nomenclaturas antigas e novas durante a transição.

## Alternativas consideradas
- continuar usando apenas a descrição genérica de engine própria de pipeline, sem formalizar o nome AIgnt-Synapse-Flow;
- adotar um nome genérico como `Pipeline Engine`;
- renomear toda a arquitetura para refletir a engine, ampliando escopo além do necessário.

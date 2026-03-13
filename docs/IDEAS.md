# IDEAS.md — Backlog de ideias futuras

## Sobre este documento

Este documento registra ideias, melhorias e candidatos de evolução do AIgnt OS que
**ainda não são SPECs** — não têm escopo fechado, critérios de aceite validados por testes
nem feature aberta na fila ativa.

### O que este documento não é

| Documento | Propósito | Diferença em relação a este |
|-----------|-----------|------------------------------|
| `SPEC.md` | Define o _quê_ e _como_ de uma feature com critérios testáveis | Uma IDEA vira SPEC só quando a fila permite e os critérios são mapeáveis |
| `ADR-*.md` | Registra uma decisão arquitetural já tomada | Uma IDEA é candidata, não decisão |
| `PHASE_2_ROADMAP.md` | Define a fila ativa e as decisões de prioridade da Fase 2 | Este documento documenta candidatos fora da fila; não muda a fila |

### Relação com PHASE_2_ROADMAP.md

O `docs/architecture/PHASE_2_ROADMAP.md` é a fonte de verdade da fila ativa.
No baseline atual, a Etapa 2 ja foi concluida e a fila passou a ser definida por novas SPECs pos-`F27`.

As ideias aqui registradas **não entram na fila automaticamente**. Elas aguardam a feature
de absorção correspondente ser alcançada. A decisão do `PHASE_2_ROADMAP.md` é explícita:

> "Não abrir guardrails como features autônomas antes da Fase 2. Absorver apenas quando
>  fizerem sentido no fluxo oficial."

Único recorte imediato permitido sem feature nova: masking de secrets em campos `_clean`
(ver G-02 em IDEA-001).

---

## Legenda e glossário

### Prioridade

| Valor | Significado |
|-------|-------------|
| `critical` | Risco de segurança ou corretude que bloqueia uso seguro do sistema |
| `high` | Risco relevante ou gap funcional com impacto direto no usuário |
| `medium` | Melhoria significativa, sem urgência imediata |
| `low` | Melhoria qualitativa ou preparatória para evolução futura |

### Esforço

| Valor | Referência de duração |
|-------|-----------------------|
| `XS` | < 1 dia — uma função ou regex |
| `S` | 1–2 dias — um módulo pequeno ou novo campo em contrato |
| `M` | 3–5 dias — novo módulo com testes ou migration SQLite |
| `L` | 1–2 semanas — subsistema ou refatoração transversal |
| `XL` | > 2 semanas — nova camada arquitetural ou serviço externo |

### Status

| Valor | Significado |
|-------|-------------|
| `open` | Ideia registrada, aguardando oportunidade de absorção |
| `in_progress` | Sendo implementada em uma feature da Fase 2 ativa |
| `absorbed` | Implementada como parte de uma feature (com link para a SPEC) |
| `rejected` | Descartada, com justificativa registrada |
| `done` | Entregue como hotfix ou commit independente (recorte mínimo ou doc-only) |

### Absorção recomendada

Indica em qual feature da fila ativa a ideia faz mais sentido entrar.

Valores válidos: `F16`, `F17`, `F18`, `F19`, `F20`, `F21`, `F22`, `F28`, `F29`, `F30`, `pós-F27`, `imediato`.

---

## Ciclo de vida de uma IDEA

```
          ┌─────────┐
          │  open   │  ← ideia registrada no IDEAS.md
          └────┬────┘
               │
     ┌─────────▼──────────┐
     │ Feature de absorção │
     │ alcançada na fila   │
     └─────────┬──────────┘
               │
       ┌───────▼────────┐
       │  in_progress   │  ← SPEC aberta dentro da feature alvo
       └───────┬────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼──────┐        ┌─────▼────┐
│ absorbed │        │ rejected │
│ (link    │        │ (motivo  │
│  SPEC)   │        │  regist.)│
└──────────┘        └──────────┘

Exceção: recorte mínimo sem feature nova → status vira `done` diretamente.
```

---

## Como contribuir

### Inserindo nova IDEA

1. Copie o bloco de **template padrão** (seção abaixo) para o lugar correto no documento
2. Preencha todos os campos obrigatórios: `Prioridade`, `Esforço`, `Status`, `Absorção recomendada`
3. **Reposicione** o bloco na ordenação correta:
   - Ordem decrescente: `critical > high > medium > low`
   - Dentro de mesma prioridade: menor esforço primeiro (`XS < S < M < L < XL`)
4. Não crie nova IDEA para algo que já cabe como subtarefa de uma IDEA existente;
   prefira adicionar como item na tabela interna da IDEA existente

### Promovendo IDEA para SPEC

Uma IDEA pode virar SPEC quando **todas** as condições forem atendidas:

- [ ] A feature de absorção sugerida está na fila ativa ou é a próxima
- [ ] Os `acceptance_criteria` podem ser escritos de forma testável
- [ ] O impacto arquitetural está mapeado e não exige outro ADR prévio não resolvido
- [ ] Não há dependência de IDEA anterior ainda em `open`
- [ ] O escopo cabe dentro de uma única feature (sem scope creep)

Ao promover:

1. Crie `features/FNN-<slug>/SPEC.md` seguindo `docs/architecture/SPEC_FORMAT.md`
2. Atualize o `Status` desta IDEA para `in_progress` com link para a SPEC
3. Ao concluir o merge da feature, mude para `absorbed` e registre o link do PR

---

## Template padrão

```markdown
## IDEA-NNN — Título da ideia

| Campo | Valor |
|-------|-------|
| **Prioridade** | critical / high / medium / low |
| **Esforço** | XS / S / M / L / XL |
| **Status** | open |
| **Absorção recomendada** | FNN ou pós-F27 |
| **Depende de** | IDEA-NNN ou — |

### Problema
<descrição do gap ou oportunidade>

### Solução proposta
<descrição técnica objetiva do que implementar>

### Impacto arquitetural
- **Mudança estrutural:** sim/não — <descrição se sim>
- **Novos agents/skills:** sim/não — <nome e responsabilidade se sim>
- **Novos contratos Pydantic:** sim/não — <modelo e campos se sim>
```

---

## IDEA-001 — Implementação de guardrails de segurança

| Campo | Valor |
|-------|-------|
| **Prioridade máxima interna** | high |
| **Status global** | open |
| **Absorção recomendada** | ver tabela interna por item |
| **Depende de** | — |

Esta IDEA consolida os gaps de proteção identificados na análise de guardrails do AIgnt OS.
Cada item tem prioridade e absorção independentes. Parte do programa já foi absorvida
em `F23 -> F27`; os itens remanescentes continuam candidatos a novas SPECs próprias.

### Itens

| Item | Descrição | Prioridade | Esforço | Status atual | Absorção recomendada |
|------|-----------|------------|---------|--------------|----------------------|
| G-01 | Prevenção de Bidi attack (`strip_bidi_controls()`) | high | XS | absorbed em `F23` | — |
| G-02 | Mascaramento de secrets em campos `_clean` | high | S | absorbed em `F23` | — |
| G-03 | Scanning AST de artefatos gerados por IA | high | M | absorbed em `F25` | — |
| G-04 | Normalização Unicode de inputs (`NFKC`) | medium | XS | absorbed em `F23` | — |
| G-05 | Isolamento de workspace por run (boundary check) | medium | XS | absorbed em `F24` | — |
| G-06 | Integridade da SPEC por hash SHA-256 | medium | M | absorbed em `F26` | — |
| G-07 | Rate limiting via `asyncio.Semaphore` no adapter layer | medium | M | absorbed em `F27` | — |
| G-08 | Audit trail com `initiated_by` e security events | medium | M | absorbed em `F26` | — |
| G-09 | Circuit breaker para adapters (estado persistido entre runs) | medium | L | absorbed em `F28` | — |
| G-10 | Log sanitization de artefatos em disco | low | S | absorbed em `F24` | — |
| G-11 | Autenticação e autorização (fundacao local absorvida; transporte autenticado residente e operacao remota ainda pendentes) | low | XL | decomposed em `F31`; fundacao local absorvida em `F29`/`F30` | pós-F27 |

### Problema

O AIgnt-Synapse-Flow — a engine própria de pipeline do AIgnt OS — expõe superfície de
ataque crescente à medida que a Fase 2 amplia a interface pública (`runs submit`,
`runs show`, `runs list`). Os gaps de maior risco imediato são:

- **Bidi characters e Unicode homógrafos** em prompts e artefatos de IA: indetectáveis
  visualmente em editores, mas executam de forma diferente no runtime (G-01, G-04)
- **Secrets persistidos sem masking** em campos `_clean` e no filesystem: tokens GitHub
  (`ghp_*`, `ghs_*`), Bearer keys e `sk-*` podem vazar em logs e outputs públicos (G-02, G-10)
- **Artefatos Python gerados por IA** com `eval`, `exec`, `os.system` ou `shell=True`
  passam pela validação de sintaxe atual sem varredura de padrões perigosos (G-03)
- **Ausência de rastreabilidade**: `RunRecord` não tem `initiated_by` nem events tipados
  como `security_failure`, dificultando auditoria e resposta a incidentes (G-08)

O unico gap remanescente desta IDEA no baseline atual e o residual de `G-11`, agora
decomposto em tres buckets: a fundacao local ja absorvida, o futuro bucket pequeno de
`resident_transport_auth` e a operacao remota/multi-host explicitamente adiada.
Circuit breaker, boundary check, integridade da SPEC, rate limiting, audit trail minimo
e sanitizacao publica ja foram absorvidos no baseline atual.

### Solução proposta

Absorver os itens remanescentes em features próprias, seguindo o fluxo oficial
`SPEC → TEST_RED → CODE_GREEN → REFACTOR → SECURITY_REVIEW → COMMIT`.

Absorções já concluídas no baseline atual:
- `F23`: `G-01`, `G-02` e `G-04`
- `F24`: `G-05` e o recorte público remanescente de `G-10`
- `F25`: `G-03`
- `F26`: `G-06` e `G-08`
- `F27`: `G-07`
- `F28`: `G-09`
- `F29`: fundacao local opt-in de auth/RBAC para comandos mutaveis
- `F30`: provisionamento local do auth registry (`init`, `issue`, `disable`)
- `F31`: decomposicao formal de `G-11` em buckets local, residente e remoto

Centralização técnica já realizada:
- `src/aignt_os/security.py` foi criado como módulo de segurança compartilhado
- a sanitização pública passou a reutilizar helpers compartilhados no baseline atual

Boundary ainda adiado:
- `resident_transport_auth`: ainda sem SPEC de codigo propria; segue apenas como bucket futuro pequeno
- `remote_multi_host_auth`: continua sem transporte em rede, operacao entre hosts ou coordenacao remota

### Impacto arquitetural

- **Mudança estrutural:** sim — G-06 e G-08 exigem migration SQLite;
  G-09 exigiu novo arquivo de estado; o residual futuro de G-11 ainda exigira camada propria de transporte/auth quando sair do bucket documental
- **Novos agents/skills:** nao obrigatorio no baseline atual; qualquer skill nova de auth/transporte so deve aparecer quando houver frente de codigo propria
- **Novos contratos Pydantic:**
  - já absorvido: `AppSettings.secret_mask_patterns: list[str]`
  - já absorvido: `RunRecord.spec_hash: str | None`
  - já absorvido: `AppSettings.max_concurrent_adapters: int = 4`
  - já absorvido: `RunRecord.initiated_by: str`
  - G-09: `CircuitBreakerState` (novo modelo)
  - G-11 local: `AuthToken`, `Principal` ja absorvidos no baseline de auth local
  - G-11 remoto: sem contrato novo definido nesta frente

---

## IDEAs futuras

> **Placeholder** — esta seção reserva espaço para ideias identificadas em sessões futuras.

Ao registrar nova ideia aqui, siga o template padrão e respeite a ordenação por prioridade.
Se a ideia pertencer a uma categoria existente (ex: segurança), avalie adicionar como item
interno de uma IDEA já existente em vez de criar entrada nova.

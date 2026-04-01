# ADR-015 — Adotar Plugin System com HookSpec e Entry Point Discovery

## Status

Aceito

## Contexto

O SynapseOS precisa ser extensível sem modificar o core. Adapters CLI (ADR-004) resolvem integração com ferramentas externas, mas o sistema precisa de mecanismos para:

- Plugins de terceiros estenderem comportamento (novos parsers, novos tipos de step);
- Hooks em pontos específicos da pipeline (pré/pós execução, transformação de artefatos);
- Discovery automático de extensões instaladas via pip/entry points.

A arquitetura state-driven do Synapse-Flow (ADR-003) possui pontos bem definidos onde hooks podem ser injetados sem comprometer o fluxo principal.

## Decisão

Adotar um **Plugin System** baseado em:

1. **HookSpec**: contratos declarativos usando `pluggy` (sistema de hooks do pytest);
2. **Entry point discovery**: plugins registrados via `pyproject.toml` `[project.entry-points."synapseos.hooks"]`;
3. **Hook points explícitos**:
    - `pre_step_execute`: antes de executar um step;
    - `post_step_execute`: após execução, antes do parsing;
    - `pre_artifact_persist`: antes de persistir artefato;
    - `post_run_complete`: ao finalizar run com sucesso;
    - `on_run_failed`: quando run falha (para cleanup ou notificação).

Regras:

- Hooks são **opcionais** — sistema funciona sem plugins;
- Hooks podem **modificar** contexto (mutável) ou apenas **observar** (readonly);
- Falha em hook não quebra pipeline (log + continua), exceto hooks críticos explicitamente marcados;
- Plugins são carregados uma vez no boot do Synapse-Flow.

## Consequências

### Positivas

- Extensibilidade sem fork do core;
- Ecossistema permitido: comunidade pode criar plugins sem PRs no repo principal;
- `pluggy` é battle-tested (usado no pytest), bem documentado;
- Entry points são padrão Python, sem magia de import dinâmico;
- Hooks bem definidos permitem instrumentação, métricas, notificações customizadas.

### Negativas

- Nova dependência (`pluggy`);
- Surface de ataque aumentada — plugins maliciosos podem executar código arbitrário;
- Debugging mais complexo quando múltiplos plugins interagem;
- Necessidade de versionamento de HookSpec (breaking changes em hooks);
- Overhead de carregamento de plugins no startup.

## Alternativas consideradas

- **Import dinâmico de módulos**: rejeitado — menos estruturado, risco de side effects no import;
- **Sistema de hooks próprio**: rejeitado — reinventar roda, `pluggy` já resolve bem;
- **Arquitetura de microserviços**: rejeitado — overkill, aumentaria complexidade operacional;
- **Config-based plugin loading**: rejeitado — entry points são mais idiomáticos em Python.

## Segurança

Plugins executam com os mesmos privilégios do Synapse-Flow. Recomendações:

- Documentar que plugins são código arbitrário — só instalar de fontes confiáveis;
- Futuro: considerar sandboxing ou assinatura de plugins.

## Relação com ADRs existentes

- ADR-004 (cli-adapter-layer): plugins podem adicionar novos adapters dinamicamente;
- ADR-003 (state-machine-pipeline-engine): hooks são invocados em transições de estado;
- ADR-014 (http-control-plane): plugins podem expor endpoints customizados na API.

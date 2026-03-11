# AGENTS.md

## Objetivo do repositório
Este repositório implementa o AIgnt OS, um meta-orquestrador de agentes de IA via CLI.
A implementação deve seguir a arquitetura e decisões já documentadas, sem reinventar o projeto a cada feature.

## Fontes de verdade
Antes de iniciar qualquer trabalho, leia nesta ordem:
1. `CONTEXT.md`
2. `docs/architecture/SDD.md`
3. `docs/architecture/TDD.md`
4. `docs/architecture/SPEC_FORMAT.md`
5. `features/<feature>/SPEC.md` da feature atual

Em caso de conflito:
- `SPEC.md` da feature governa o comportamento da feature
- `SDD.md` governa a arquitetura
- `TDD.md` governa a estratégia de implementação e testes
- `SPEC_FORMAT.md` governa o formato da SPEC

## Regras gerais
- Trabalhe **uma feature por vez**.
- Não misture escopo de duas features na mesma mudança.
- Sempre siga o fluxo oficial:
  1. `DOCKER_PREFLIGHT`
  2. `SPEC`
  3. `TEST_RED`
  4. `CODE_GREEN`
  5. `REFACTOR`
  6. `SECURITY_REVIEW`
  7. `REPORT`
  8. `COMMIT`
- Nunca invente requisitos ausentes. Se faltar informação, reduza escopo e registre a lacuna em `NOTES.md`.
- Prefira mudanças pequenas, localizadas e reversíveis.
- Nunca altere docs centrais sem necessidade real da feature.
- Use sempre o nome **AIgnt-Synapse-Flow** ao se referir ao runtime interno do AIgnt OS. Ao menos uma vez por documento, deixe claro que ele é a **engine própria de pipeline** do AIgnt OS.
- Preserve o caráter **CLI-first**, **spec-first** e **feature-by-feature** do projeto.

## Convenção de nomes para agents/skills
- Use o padrão `<domínio>-<papel>`.
- Mantenha nomes em inglês.
- Famílias preferidas: `repo-*`, `git-*`, `security-*`, `session-*`, `technical-*`, `adr-*`, `debug-*`, `spec-*`, `test-*`, `green-*`.

## Branch Sync Gate
- Em qualquer branch diferente de `main`, verifique drift com `origin/main` antes de trabalho relevante, antes de `commit`/`push`/`PR` e depois de mudanças estruturais com risco de drift.
- Use `./scripts/branch-sync-check.sh` para detectar atraso sempre.
- Use `./scripts/branch-sync-update.sh` apenas como atualização conservadora/best effort: só quando a branch não for `main`, a working tree estiver limpa e não houver conflito imediato detectável.
- Mesmo após essa checagem, `rebase` ou `merge` ainda podem exigir intervenção manual.
- Se a branch estiver atrasada e não for seguro atualizar, pare e reporte explicitamente.

## Fluxo oficial do projeto

```text
DOCKER_PREFLIGHT → SPEC → TEST_RED → CODE_GREEN → REFACTOR → SECURITY_REVIEW → REPORT → COMMIT
```

- `DOCKER_PREFLIGHT` é obrigatório antes de qualquer execução prática da feature.
- O preflight operacional de Docker/container é responsabilidade da skill `repo-automation`.
- Em CI e no fluxo local, o `DOCKER_PREFLIGHT` deve permanecer leve por padrão: validar `compose config` sem subir o container completo; build fica explícito quando necessário.
- Hooks locais podem executar checks leves de repositório, mas isso não substitui o `DOCKER_PREFLIGHT` operacional real antes da execução prática da feature.
- O container completo só sobe em workflow dedicado de runtime/integração ou quando houver pedido explícito ligado a boot, ciclo de vida, persistência ou integração.
- `spec-editor` só pode iniciar depois que o ambiente estiver verde em Docker ou explicitamente validado.
- `security-review` atua como gate de segurança antes de `REPORT` e `COMMIT`.
- `SPEC` pode conter subetapas internas como descoberta, normalização e validação, sem alterar o fluxo oficial acima.

## Escopo do MVP
No MVP:
- 1 workspace por run
- memória semântica apenas advisory/read-only
- observabilidade local
- `RUN_REPORT.md` por execução
- pipeline linear state-driven
- runtime dual simples: CLI efêmero + worker leve
- sem DAG distribuída real
- sem vector DB obrigatório
- sem roteamento automático por memória semântica

## Critérios de parada
Pare imediatamente e peça revisão quando:
- a `SPEC.md` estiver ambígua
- os testes contradisserem a SPEC
- a mudança exigir refatoração ampla fora da feature
- a mudança pedir alteração arquitetural não coberta pelos ADRs
- a saída esperada não puder ser validada de forma clara

## Política de desenvolvimento
- Faça TDD de forma explícita.
- Escreva testes antes do código de produção.
- Não refatore antes de os testes ficarem verdes.
- Não inicie execução prática da feature sem `DOCKER_PREFLIGHT` validado.
- Mantenha baixo acoplamento e contratos explícitos com Pydantic.
- Trate parsing como componente crítico.
- Separe output bruto de output limpo.
- Não use abstrações prematuras.

## Execução local do Codex
- Neste repositório, a operação do Codex deve ser **container-first** via `./scripts/dev-codex.sh`.
- O serviço `codex-dev` existe só para desenvolvimento assistido; o serviço `aignt-os` continua sendo o container de runtime da aplicação e do AIgnt-Synapse-Flow, a engine própria de pipeline do AIgnt OS.
- Não rode o Codex diretamente no host quando a tarefa exigir execução prática em container.
- O fluxo padrão do Codex deve montar apenas o repositório em `/workspace` e usar a configuração versionada em `.codex/config.toml`.
- Não monte `docker.sock`, não use `privileged` e não monte o `$HOME` do host no ambiente isolado do Codex.
- No ambiente atual do Codex com `network-access = true`, tente `git push` e `gh pr create` normalmente no sandbox como caminho padrão.
- Reexecute fora do sandbox apenas como contingência quando houver falha real de rede/sandbox ou bloqueio operacional equivalente.
- Trate autenticação, permissão no GitHub e conectividade real do host como problemas distintos; não masque esses casos com fallback automático.

## Agentes recomendados
### 1. repo-automation
Responsável por:
- executar `DOCKER_PREFLIGHT`
- validar build/rebuild do container
- validar alinhamento operacional com `main`
- preparar workflows e scripts operacionais
- distinguir checks leves de hook do `DOCKER_PREFLIGHT` operacional real
- manter o preflight leve por padrão, promovendo runtime completo apenas quando explicitamente necessário
Não inicia lógica de produto.
Não faz diagnóstico inicial de falhas; use `debug-failure` antes quando o problema ainda não estiver classificado.

### debug-failure
Responsável por:
- investigar falhas reais em CI, scripts, testes, Docker, runtime, Git e ambiente local
- reproduzir a falha quando possível
- classificar a falha por tipo e indicar o próximo agent responsável
Não implementa a correção, não decide backlog e não substitui `repo-automation`.

### memory-curator
Responsável por:
- manter `memory.md` como memória durável e reaproveitável do projeto
- consolidar decisões, trade-offs, estado da frente e próximos passos
- gerar handoff de sessão quando explicitamente invocada para encerramento
Não substitui `session-logger`, não decide backlog e não cria ADR.

### 2. spec-editor
Responsável por:
- melhorar o pedido do usuário
- transformar o pedido em `SPEC.md`
- ajustar `SPEC_FORMAT.md` apenas se necessário
- reduzir ambiguidade
Só começa após `DOCKER_PREFLIGHT` verde ou explicitamente validado.
Não implementa código de produção.

### 3. test-red
Responsável por:
- ler `SPEC.md`
- criar testes que falham
- validar critérios de aceite da feature
Não implementa código de produção.

### 4. green-refactor
Responsável por:
- implementar o mínimo para passar nos testes
- refatorar após os testes ficarem verdes
- manter compatibilidade com a arquitetura
Não altera a SPEC sem motivo explícito.

### 5. security-review
Responsável por:
- revisar riscos de Docker, scripts, workflows, skills e código alterado
- atuar como gate de segurança antes de `REPORT` e `COMMIT`
- registrar mitigação objetiva quando houver ressalvas
Não substitui `repo-automation` na execução operacional.

## Alternativas de operação
Se multi-agent não estiver disponível:
- execute `repo-automation` primeiro
- depois `spec-editor`
- depois `test-red`
- depois `green-refactor`
- depois `security-review`

Se multi-agent estiver disponível:
- `repo-automation` roda primeiro e valida `DOCKER_PREFLIGHT`
- `spec-editor` só roda após ambiente validado
- `test-red` e leituras auxiliares podem rodar em paralelo apenas quando a SPEC estiver estável
- `green-refactor` só começa após a etapa RED estar validada
- `security-review` roda depois de `REFACTOR` e antes de `REPORT`/`COMMIT`

## Entregáveis por feature
Cada feature deve terminar com:
- `DOCKER_PREFLIGHT` validado ou explicitamente aprovado
- `SPEC.md` atualizado
- testes cobrindo a feature
- implementação mínima funcional
- refatoração concluída
- revisão de segurança concluída
- `NOTES.md` com decisões locais
- checklist de aceite da feature

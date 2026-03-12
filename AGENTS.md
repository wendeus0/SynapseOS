# AGENTS.md

## Objetivo do repositório
Este repositório implementa o AIgnt OS, um meta-orquestrador de agentes de IA via CLI.
A implementação deve seguir a arquitetura e decisões já documentadas, sem reinventar o projeto a cada feature.

O runtime interno deve ser referido como **AIgnt-Synapse-Flow**, deixando claro que ele é a **engine própria de pipeline** do AIgnt OS.

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
- Sempre siga o fluxo oficial do projeto.
- Nunca invente requisitos ausentes. Se faltar informação, reduza escopo e registre a lacuna em `NOTES.md`.
- Prefira mudanças pequenas, localizadas e reversíveis.
- Nunca altere docs centrais sem necessidade real da feature.
- Preserve o caráter **CLI-first**, **spec-first** e **feature-by-feature** do projeto.
- Use sempre o nome **AIgnt-Synapse-Flow** ao se referir ao runtime interno do AIgnt OS, deixando explícito ao menos uma vez por documento que ele é a **engine própria de pipeline** do AIgnt OS.

## Convenção de nomes para agents/skills
- Use o padrão `<domínio>-<papel>`.
- Mantenha nomes em inglês.
- Famílias preferidas: `repo-*`, `git-*`, `security-*`, `session-*`, `technical-*`, `adr-*`, `debug-*`, `spec-*`, `test-*`, `green-*`.

## Fluxo oficial do projeto

SPEC → TEST_RED → CODE_GREEN → REFACTOR → QUALITY_GATE → SECURITY_REVIEW → REPORT → COMMIT
Regras do fluxo

DOCKER_PREFLIGHT é gate operacional condicional.

DOCKER_PREFLIGHT é obrigatório antes de execução prática que dependa de Docker, imagem, boot, ciclo de vida, persistência ou integração.

O preflight operacional de Docker/container deve permanecer leve por padrão: validar compose config sem subir runtime completo.

Build de imagem é explícito quando necessário.

Runtime completo é exceção e só deve ocorrer em workflow dedicado ou quando a tarefa tocar boot, ciclo de vida, persistência ou integração.

QUALITY_GATE ocorre depois de REFACTOR e antes de SECURITY_REVIEW.

SECURITY_REVIEW atua como gate de segurança antes de REPORT e COMMIT.

REPORT consolida escopo alterado, validações, riscos residuais e próximos passos.

COMMIT só deve ocorrer ao final do fluxo, com gates anteriores satisfeitos.

SPEC pode conter subetapas internas como descoberta, normalização e validação, sem alterar o fluxo oficial acima.

Mandatory skill usage

Use as skills abaixo como padrão operacional do repositório:

technical-triage

Use quando o pedido ainda estiver difuso, amplo ou mal classificado.
Não substitui spec-editor.

spec-editor

Use quando a demanda ainda não estiver convertida em SPEC.md clara, estável e validável.
Não implementa código de produção.

test-red

Use quando a SPEC.md já estiver estável e for hora de escrever testes que falham.
Não implementa código de produção.

green-refactor

Use quando já existir etapa RED validada e for hora de passar os testes com a menor mudança possível.
Refatora somente após os testes ficarem verdes.
Não altera a SPEC sem motivo explícito.

repo-preflight

Use antes de execução prática dependente de Docker/container.
É responsável por DOCKER_PREFLIGHT.
Não inicia lógica de produto.
Não substitui debug-failure quando o problema ainda não estiver classificado.

branch-sync-guard

Use:

antes de trabalho relevante em branch diferente de main

antes de commit / push / PR

depois de mudanças estruturais com risco de drift

quality-gate

Use depois de REFACTOR e antes de SECURITY_REVIEW,
para validar testes, lint, typecheck e regressão funcional.

security-review

Use depois de quality-gate e antes de REPORT / COMMIT.
Revisa riscos de Docker, scripts, workflows, skills e código alterado.
Registra mitigação objetiva quando houver ressalvas.

report-writer

Use depois de security-review,
para consolidar escopo alterado, validações, riscos residuais e próximos passos.

git-flow-manager

Use somente no final do fluxo,
depois de branch-sync-guard, quality-gate, security-review e report-writer.

ci-automation

Use quando a tarefa envolver GitHub Actions, hooks, scripts operacionais, gatilhos de rebuild ou automação de repositório.

debug-failure

Use quando houver falha real ainda não classificada.
Investiga, reproduz quando possível, classifica e indica o próximo agent responsável.
Não implementa a correção.

session-logger

Use para fechamento operacional da sessão corrente.

memory-curator

Use para memória durável, handoff e consolidação de contexto.
Mantém memory.md como memória reutilizável do projeto.
Não substitui session-logger.

adr-manager

Use apenas quando a mudança exigir decisão arquitetural nova ou ajuste real de ADR.

Agent roles

Os papéis de multi-agent deste projeto são:

explorer

mapeia arquitetura, arquivos afetados, ADRs, SPECs, execução e evidências

não propõe mudanças cedo demais

reviewer

revisa correção, regressão, segurança, cobertura e risco técnico

não implementa código

worker

implementa mudanças pequenas e focadas depois que a frente estiver entendida

monitor

acompanha comandos longos, logs, runtime, CI e evidências operacionais

não assume ownership da implementação

Branch Sync Gate

Em qualquer branch diferente de main:

use ./scripts/branch-sync-check.sh para detectar drift com origin/main

use ./scripts/branch-sync-update.sh apenas como atualização conservadora:

somente fora de main

somente com working tree limpa

somente quando não houver conflito imediato detectável

mesmo após a checagem, rebase ou merge ainda podem exigir intervenção manual

se a branch estiver atrasada e não for seguro atualizar, pare e reporte explicitamente

Escopo do MVP

No MVP:

1 workspace por run

memória semântica apenas advisory/read-only

observabilidade local

RUN_REPORT.md por execução

pipeline linear state-driven

runtime dual simples: CLI efêmero + worker leve

sem DAG distribuída real

sem vector DB obrigatório

sem roteamento automático por memória semântica

Critérios de parada

Pare e reporte quando:

a SPEC.md estiver ambígua

os testes contradisserem a SPEC

a mudança exigir refatoração ampla fora da feature

a mudança pedir alteração arquitetural não coberta pelos ADRs

a saída esperada não puder ser validada de forma clara

Política de desenvolvimento

Faça TDD de forma explícita.

Escreva testes antes do código de produção.

Não refatore antes de os testes ficarem verdes.

Não inicie execução prática dependente de Docker sem DOCKER_PREFLIGHT validado.

Mantenha baixo acoplamento e contratos explícitos com Pydantic.

Trate parsing como componente crítico.

Separe output bruto de output limpo.

Não use abstrações prematuras.

Execução local do Codex

Neste repositório, a operação do Codex deve ser container-first via ./scripts/dev-codex.sh.

O serviço codex-dev existe só para desenvolvimento assistido.

O serviço aignt-os continua sendo o container de runtime da aplicação e do AIgnt-Synapse-Flow, a engine própria de pipeline do AIgnt OS.

Não rode o Codex diretamente no host quando a tarefa exigir execução prática em container.

O fluxo padrão do Codex deve montar apenas o repositório em /workspace e usar a configuração versionada em .codex/config.toml.

Não monte docker.sock, não use privileged e não monte o $HOME do host no ambiente isolado do Codex.

No ambiente atual com network_access = true, tente git push e gh pr create normalmente no sandbox como caminho padrão.

Reexecute fora do sandbox apenas como contingência quando houver falha real de rede/sandbox ou bloqueio operacional equivalente.

Trate autenticação, permissão no GitHub e conectividade real do host como problemas distintos; não masque esses casos com fallback automático.

Alternativas de operação

Se multi-agent não estiver disponível:

execute technical-triage quando a demanda ainda estiver difusa

execute spec-editor

execute test-red

execute green-refactor

execute repo-preflight quando a feature exigir execução prática dependente de Docker

execute quality-gate

execute security-review

execute report-writer

execute git-flow-manager no encerramento

execute session-logger e memory-curator quando necessário

Se multi-agent estiver disponível:

explorer pode abrir a frente e estabilizar contexto, arquivos afetados e evidências

spec-editor estabiliza a SPEC sem depender de preflight inicial

test-red e leituras auxiliares podem rodar em paralelo apenas quando a SPEC estiver estável

worker só começa após a etapa RED estar validada

repo-preflight entra antes de validação prática que dependa de Docker, imagem ou runtime

monitor acompanha logs, runtime e evidências operacionais

reviewer atua em correção, regressão, cobertura e segurança após a implementação

quality-gate roda depois de REFACTOR

security-review roda depois de quality-gate e antes de REPORT / COMMIT

Entregáveis por feature

Cada feature deve terminar com:

SPEC.md atualizado

testes cobrindo a feature

implementação mínima funcional

refatoração concluída

revisão de qualidade concluída

revisão de segurança concluída

NOTES.md com decisões locais

checklist de aceite da feature

RUN_REPORT.md ou relatório equivalente quando aplicável

DOCKER_PREFLIGHT validado ou explicitamente aprovado quando houver execução prática dependente de Docker

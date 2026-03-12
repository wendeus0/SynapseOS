# Roadmap da Etapa 2 — Pós-F14

## Objetivo

Registrar a proxima etapa do projeto apos a conclusao do MVP inicial e dos follow-ups `F13` e `F14`, mantendo o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS e priorizando evolucao incremental da CLI publica.

## Estado de partida

- `main` sincronizada e baseline estavel
- MVP inicial concluido ate `DOCUMENT`
- `aignt runs list`, `aignt runs show <run_id>` e `aignt runs submit <spec_path>` ja expostos pela CLI publica
- nenhuma nova feature de produto aberta no momento

## Estrategia adotada

A etapa 2 segue o **cenario misto** escolhido na triagem e foi concluida no baseline atual. O repositorio ja incorpora `F15-public-run-submission`, `F16-run-detail-expansion`, `F21-cli-error-model-and-exit-codes`, `F18-canonical-happy-path`, `F19-environment-doctor`, `F20-public-onboarding`, `F17-artifact-preview` e `F22-release-readiness`.

O objetivo desta ordem foi fechado com sucesso: primeiro a leitura rica controlada dos sinais persistidos pela CLI publica, depois o empacotamento da etapa como release tecnica coerente.

## Guardrails avaliados antes da etapa 2

Uma proposta posterior sugeriu antecipar um pacote de hardening dividido em duas frentes sobre input, secrets, rate limiting e audit trail antes do inicio da etapa 2.

Decisao adotada:
- nao abrir essas propostas como features autonomas antes da etapa 2;
- nao reutilizar IDs `F14` ou `F15` para esse pacote, porque `F14` ja foi mergeada e `F15` ja esta reservada para `public-run-submission`;
- tratar esse material como **guardrails candidatos**, a serem absorvidos apenas quando fizerem sentido no fluxo oficial da etapa 2.

Recorte minimo permitido antes da etapa 2:
- mascaramento de secrets em saidas `_clean` e artifacts de leitura publica, caso seja necessario endurecer a observabilidade atual sem abrir nova superficie de produto.

Recortes explicitamente adiados:
- sanitizacao de prompt como frente isolada antes da submissao publica;
- rate limiting generico em adapters por `asyncio.Semaphore`;
- audit trail novo com `initiated_by` e eventos dedicados de seguranca;
- endurecimento amplo de `AppSettings` sem demanda concreta da superficie publica.

Alocacao recomendada quando esses itens voltarem:
- `F21-cli-error-model-and-exit-codes`: classificacao, mensagens e efeitos operacionais do contrato publico;
- follow-up curto proprio apenas se o mascaramento de secrets em observabilidade precisar entrar antes por risco real.

## Etapa 2 ja concluida

### F15 — Public Run Submission
- **Objetivo**: abrir um caminho oficial para criar runs pela CLI publica.
- **Valor para a fase**: transforma o sistema de apenas inspecionavel em executavel por interface publica.
- **Superficie publica afetada**: `aignt runs submit <spec_path>`, `--mode auto|sync|async`, `--stop-at <state>`.
- **Dependencias**: F14, runtime dual, dispatch interno ja existente.
- **Fora de escopo**: preview de artifacts, onboarding, TUI.
- **Criterio de pronto**: um operador consegue iniciar uma run e obter `run_id`, `status` e `mode`.
- **Risco principal**: expor submit antes de estabilizar o contrato de erro.

### F16 — Run Detail Expansion
- **Objetivo**: aprofundar `runs show` para explicar onde a run esta, falhou ou travou.
- **Valor para a fase**: reduz atrito operacional logo apos a submissao publica.
- **Superficie publica afetada**: extensoes de `aignt runs show` para steps, events e artifacts listados com mais contexto.
- **Dependencias**: F14 concluida; idealmente F15 concluida ou em reta final.
- **Fora de escopo**: preview bruto de conteudo e TUI.
- **Criterio de pronto**: um operador consegue localizar o proximo ponto de diagnostico apenas pela CLI.
- **Risco principal**: crescer demais e virar uma pseudo-TUI textual.

### F21 — CLI Error Model and Exit Codes
- **Objetivo**: organizar categorias de erro e exit codes previsiveis para a CLI.
- **Valor para a fase**: estabiliza automacoes e reduz ambiguidade operacional.
- **Superficie publica afetada**: comandos publicos da CLI, com foco em `runs submit` e `runs show`.
- **Dependencias**: F15 e F16 ja suficientes para revelar casos reais de falha.
- **Fora de escopo**: modo verbose rico e debug profundo.
- **Criterio de pronto**: input, ambiente e execucao falham com mensagens e codigos distinguiveis.
- **Risco principal**: fixar cedo demais um contrato ainda imaturo.

### F18 — Canonical Happy Path
- **Objetivo**: consolidar um caminho oficial de demonstracao de ponta a ponta.
- **Valor para a fase**: transforma capacidade tecnica em fluxo reproduzivel.
- **Superficie publica afetada**: sequencia oficial de comandos e SPEC de referencia.
- **Dependencias**: F15 e base minima de erro e inspecao.
- **Fora de escopo**: multiplos adapters reais ou multiplas demos paralelas.
- **Criterio de pronto**: existe uma execucao canonica reproduzivel e auditavel.
- **Risco principal**: acoplar a demo a pre-requisitos externos frageis.

### F19 — Environment Doctor
- **Objetivo**: oferecer diagnostico local para os pre-requisitos do fluxo publico.
- **Valor para a fase**: reduz troubleshooting antes da primeira run real.
- **Superficie publica afetada**: `aignt doctor`.
- **Dependencias**: happy path ja conhecido o suficiente para virar checklist.
- **Fora de escopo**: auto-correcao de ambiente.
- **Criterio de pronto**: o usuario entende o que falta para executar o fluxo oficial.
- **Risco principal**: verificar coisas demais e produzir ruido.

### F20 — Public Onboarding
- **Objetivo**: criar um quickstart curto e oficial para a primeira run.
- **Valor para a fase**: aproxima o projeto de uso por terceiros.
- **Superficie publica afetada**: README, quickstart e troubleshooting essencial.
- **Dependencias**: F15, F18 e F19 ja estaveis.
- **Fora de escopo**: documentacao enciclopedica.
- **Criterio de pronto**: alguem de fora consegue fazer a primeira run sem ajuda direta.
- **Risco principal**: documentar fluxo ainda instavel e gerar drift rapido.

## Fechamento da etapa 2

### F17 — Artifact Preview
- **Objetivo**: permitir consulta de report e outputs uteis pela CLI.
- **Valor para a fase**: melhora conforto de operacao depois do caminho principal estar estavel.
- **Superficie publica afetada**: extensoes de `aignt runs show <run_id>` para preview controlado de `RUN_REPORT.md` e de output limpo por step.
- **Dependencias**: F16 e caminho canonico ja consolidados.
- **Fora de escopo**: dump irrestrito de arquivos e leitura arbitraria do host.
- **Criterio de pronto**: o usuario le report e outputs-chave sem abrir arquivos manualmente.
- **Risco principal**: ampliar cedo demais a superficie de leitura.
- **Status no baseline atual**: concluida e mergeada em `main`.

### F22 — Release Readiness
- **Objetivo**: empacotar a etapa como primeira release tecnica coerente.
- **Valor para a fase**: fecha o ciclo de produto interno robusto para produto apresentavel.
- **Superficie publica afetada**: changelog, release notes, checklist de readiness.
- **Dependencias**: F15, F18, F19, F20 e F21 maduros o suficiente.
- **Fora de escopo**: prometer escala ou validacao com usuarios se isso ainda nao existir.
- **Criterio de pronto**: um terceiro consegue instalar, diagnosticar, submeter e inspecionar uma run.
- **Risco principal**: rotular release acima da maturidade real.
- **Status no baseline atual**: concluida e mergeada em `main`.

## Proxima decisao apos a etapa 2

- A etapa 2 nao tem mais fila ativa remanescente.
- A proxima frente deve nascer de uma nova SPEC pos-`F22`, seguindo `SPEC -> TEST_RED -> CODE_GREEN -> REFACTOR -> QUALITY_GATE -> SECURITY_REVIEW -> REPORT -> COMMIT`.
- `docs/IDEAS.md` permanece como backlog candidato; o menor recorte imediato registrado e `IDEA-001 / G-02` para mascaramento de secrets em campos `_clean` e artifacts de leitura publica, caso haja risco real.

## Arquivos a manter alinhados durante a etapa

### Fontes principais da fila
- `docs/architecture/PHASE_2_ROADMAP.md`
- `docs/architecture/WORKTREE_FEATURES.md`
- `README.md`

### Memoria e handoff
- `memory.md`
- `PENDING_LOG.md`

### Contexto operacional para agentes
- `.github/copilot-instructions.md`

## O que esta etapa nao faz

- nao reabre o cronograma historico de 10 dias como roadmap atual
- nao implica criacao imediata de SPEC detalhada para cada feature
- nao abre `F14-tui-watch-command`
- nao reabre `F17` ou `F22` como backlog ativo depois do merge

# CONTEXT.md

## O que é o AIgnt OS
AIgnt OS é um meta-orquestrador de agentes de IA via CLI.
Ele não é o agente principal de raciocínio; seu papel é coordenar múltiplas ferramentas externas de IA por meio de subprocessos, parsing estruturado, handoffs controlados e do **AIgnt-Synapse-Flow**, a **engine própria de pipeline** do AIgnt OS.

## Objetivo do projeto
Construir um runtime de desenvolvimento autônomo e controlado que:
- coordene agentes externos via CLI
- execute uma esteira de desenvolvimento state-driven
- use SPEC como contrato central da feature
- mantenha memória operacional e semântica
- gere observabilidade local e relatórios por run
- seja simples o suficiente para um MVP em 10 dias

## Filosofia do projeto
- CLI-first
- Spec-Driven Development
- Test-Driven Development
- feature por feature
- baixo acoplamento
- contratos explícitos
- parsing robusto
- observabilidade local
- evolução progressiva sem sobreengenharia

## Fluxo oficial do projeto
DOCKER_PREFLIGHT
→ SPEC
→ TEST_RED
→ CODE_GREEN
→ REFACTOR
→ SECURITY_REVIEW
→ REPORT
→ COMMIT

## Subetapas internas do AIgnt-Synapse-Flow
Dentro do fluxo oficial, o AIgnt-Synapse-Flow pode decompor a execução em estados internos como:
REQUEST
→ SPEC_DISCOVERY
→ SPEC_NORMALIZATION
→ SPEC_VALIDATION
→ PLAN
→ TEST_RED
→ CODE_GREEN
→ REVIEW
→ SECURITY
→ DOCUMENT
→ COMPLETE

No MVP, a implementação prática continua linear, mas o operador deve seguir primeiro o fluxo oficial.

## Componentes centrais
- Orchestrator Engine
- AIgnt-Synapse-Flow
- Pipeline Manager
- State Machine Manager
- CLI Adapter Layer
- Parsing Engine
- Memory Engine
- Adaptive Supervisor
- Spec Engine

## Decisões já estabelecidas
- linguagem principal: Python 3.12+
- CLI principal: Typer
- modelagem de estado: python-statemachine
- subprocessos: asyncio + create_subprocess_exec
- contratos internos: Pydantic v2
- SPEC híbrida: Markdown estruturado + bloco YAML validável
- persistência MVP: SQLite + filesystem
- observabilidade local: logs estruturados + `RUN_REPORT.md`
- memória semântica MVP: advisory/read-only
- runtime dual: CLI efêmero + worker leve
- isolamento: container da aplicação + containers dos agentes selecionados
- `DOCKER_PREFLIGHT`: obrigatório antes da execução prática de uma feature
- `DOCKER_PREFLIGHT` leve: padrão para CI e fluxo local, com compose/config + build sem `up`
- preflight completo de runtime: reservado para workflow dedicado ou pedido explícito em tarefas de boot/ciclo de vida/persistência/integração
- `repo-automation`: skill responsável pelo preflight operacional em Docker/container
- `spec-editor`: só inicia após ambiente validado
- `security-review`: gate de segurança antes de `REPORT` e `COMMIT`
- AIgnt-Synapse-Flow: engine própria de pipeline interna ao projeto, state-driven, linear no MVP

## O que NÃO fazer no MVP
- não implementar DAG distribuída completa
- não introduzir Celery/Temporal cedo
- não criar vector DB obrigatório
- não fazer roteamento automático pela memória semântica
- não abrir múltiplas features em paralelo no mesmo contexto
- não transformar o projeto em uma plataforma genérica antes do núcleo ficar estável

## Como trabalhar neste repositório
O trabalho deve acontecer por feature.
Cada feature tem sua própria pasta em `features/` e sua própria `SPEC.md`.
O ciclo ideal é:
1. validar `DOCKER_PREFLIGHT` com `repo-automation`
2. escrever/refinar a `SPEC` com `spec-editor`
3. escrever testes `TEST_RED`
4. implementar `CODE_GREEN`
5. executar `REFACTOR`
6. rodar `SECURITY_REVIEW`
7. gerar `REPORT`
8. concluir `COMMIT`

## O que significa “memória semântica” neste momento
No MVP, memória semântica não decide automaticamente qual agente usar.
Ela existe para:
- registrar aprendizados
- resumir falhas anteriores
- documentar heurísticas úteis
- enriquecer futuras execuções de forma advisory

## Parsing é crítico
As CLIs externas podem produzir saídas ruidosas.
O projeto assume parsing em camadas:
- limpeza
- extração
- validação
- recuperação corretiva quando o formato vier errado

Se o agente não respeitar YAML/JSON/Markdown esperado, deve haver tentativa de reparo local e, se necessário, uma nova chamada com prompt corretivo.

## Forma de pensar features
As features devem ser pequenas.
Se parecer grande demais para 1 a 3 dias, deve ser quebrada.
O repositório privilegia progresso incremental, commits pequenos e baixa ambiguidade.

## Estrutura do repositório
- `src/` contém o código do produto
- `tests/` contém os testes
- `docs/architecture/` contém os documentos principais
- `docs/adr/` contém as decisões arquiteturais
- `features/` contém as SPECs e notas por feature
- `scripts/` contém automações auxiliares

## Linguagem e terminologia
Sempre usar:
- `AIgnt-Synapse-Flow`, deixando explícito ao menos uma vez que ele é a engine própria de pipeline do AIgnt OS

Usar “SPEC” para o artefato formal da feature.
Usar “run” para uma execução da pipeline.
Usar “worker” para o modo residente do runtime dual.

## Meta operacional
Entregar um MVP funcional, demonstrável e coerente com a arquitetura.
A prioridade é confiabilidade do núcleo, não cobertura total de cenários futuros.

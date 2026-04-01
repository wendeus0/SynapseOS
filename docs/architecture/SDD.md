# Software Design Document (SDD) — SynapseOS v3

## 1. Visão Geral

### 1.1 Propósito

SynapseOS é um meta-orquestrador de agentes de IA via CLI. Seu papel é coordenar múltiplas ferramentas externas de IA, organizar hand-offs entre etapas de uma esteira controlada e produzir artefatos de software com rastreabilidade, resiliência e baixo custo operacional.

### 1.2 Objetivos

- Orquestrar ferramentas de IA via CLI de forma uniforme.
- Executar pipelines autônomos de desenvolvimento de software.
- Isolar contexto entre etapas e agentes.
- Tratar parsing de saídas textuais como preocupação arquitetural central.
- Incorporar Spec-Driven Development como etapa formal antes do planejamento executivo.
- Manter memória operacional e memória semântica de apoio à execução.
- Oferecer observabilidade local suficiente para auditoria posterior.
- Permitir evolução futura para paralelismo, DAG real e workers distribuídos.

### 1.3 Escopo

O sistema recebe uma tarefa, produz uma especificação estruturada, planeja sua execução, chama agentes externos por subprocess, limpa suas saídas, valida os artefatos, reage a falhas, persiste memória de execução e gera um relatório final por run.

### 1.4 Fora do escopo inicial

- Cluster distribuído completo.
- Suporte nativo a Windows/macOS como plataforma principal.
- Interface web completa.
- Decisão automática de roteamento baseada em memória semântica no MVP.
- Multi-workspace por run no MVP.

---

## 2. Premissas do MVP

- Linguagem principal: **Python 3.12+**.
- Execução principal: **CLI-first**.
- Runtime do MVP: **dual**, com CLI efêmero e worker/daemon residente leve.
- Ambiente: **container da aplicação + containers dos agentes selecionados**.
- Precondição operacional: **DOCKER_PREFLIGHT** validado antes da execução prática de uma feature.
- Workspace do MVP: **um único workspace local por run**.
- Observabilidade do MVP: **local**, com logs estruturados e `RUN_REPORT.md` por execução.
- Memória semântica no MVP: **advisory/read-only**.
- SPEC oficial: **Markdown estruturado com front matter YAML obrigatório**.
- Núcleo de orquestração: **Synapse-Flow**, a **engine própria de pipeline** do SynapseOS, state-driven e implementada em Python.

---

## 3. Princípios Arquiteturais

1. **CLI-first**: integrações externas devem passar por adapters padronizados.
2. **Spec-first**: a demanda bruta deve ser transformada em especificação verificável antes do planejamento executivo.
3. **State-driven orchestration**: o fluxo deve ser auditável por máquina de estados e evolutivo para DAG.
4. **Structured handoff**: nenhuma etapa pode consumir saída bruta sem parsing e validação.
5. **Failure-aware design**: falhas são esperadas, classificadas e tratadas.
6. **Observability by default**: logs, rastreabilidade e relatório de execução são parte da arquitetura.
7. **Extensibility**: novos agentes, parsers, políticas e modos de execução devem ser adicionáveis sem refatoração sistêmica.
8. **Container-aware isolation**: execução em ambiente isolado, com controles explícitos sobre comandos, arquivos e agentes.

---

## 4. Arquitetura de Alto Nível

### 4.1 Camadas principais

#### Camada de Orquestração

Responsável por estado, pipeline, supervisão, memória e decisão.

Componentes:

- Orchestrator Engine
- Synapse-Flow
- State Machine Manager
- Pipeline Manager (DAG execution)
- Adaptive Supervisor (per-step policies, backoff)
- Memory Engine (IndexedArtifactStore, namespacing)
- Spec Engine
- Runtime Coordinator

#### Camada de Adapters

Responsável por integração com ferramentas externas via CLI.

Componentes:

- Base CLI Adapter
- AdapterRegistry
- CapabilityRouter
- Gemini Adapter
- Codex Adapter
- Copilot Adapter
- OpenCode Adapter
- DeepSeek Adapter
- Claude Adapter
- Local LLM Adapter

#### Camada de Controle HTTP

Responsável por expor API REST para integração externa.

Componentes:

- FastAPI Application
- REST Controllers (/runs, /steps, /artifacts, /agents)
- Async Handlers
- Webhook Dispatcher

#### Camada de Extensão

Responsável por permitir extensões sem modificar o core.

Componentes:

- Plugin Loader (entry point discovery)
- Hook Manager (pluggy)
- HookSpec Definitions
- Plugin Registry

#### Camada de Execução Autônoma

Conjunto de ferramentas externas executadas sob demanda.

#### Camada de Persistência e Observabilidade

Responsável por persistir runs, steps, artefatos, eventos e relatórios.

---

## 5. Esteira de Execução

### 5.1 Fluxo oficial do projeto

```text
SPEC → TEST_RED → CODE_GREEN → REFACTOR → QUALITY_GATE → SECURITY_REVIEW → REPORT → COMMIT
```

Regras:

- `DOCKER_PREFLIGHT` é executado pela skill `repo-preflight` quando a feature exigir validação prática em Docker.
- Em CI e no fluxo local, o `DOCKER_PREFLIGHT` padrão é leve: `compose config` sem `up`; build fica explícito quando necessário.
- O runtime completo em container fica reservado para workflow dedicado ou acionamento explícito em features que toquem boot, ciclo de vida, persistência ou integração.
- `security-review` atua como gate antes de `REPORT` e `COMMIT`.
- O fluxo oficial organiza o trabalho por feature sem substituir os estados internos do runtime.

### 5.2 Subetapas internas do Synapse-Flow

```text
REQUEST → SPEC_DISCOVERY → SPEC_NORMALIZATION → SPEC_VALIDATION → PLAN → TEST_RED → CODE_GREEN → QUALITY_GATE → REVIEW → SECURITY → DOCUMENT → COMPLETE
```

O macroestágio `SPEC` do fluxo oficial engloba `SPEC_DISCOVERY`, `SPEC_NORMALIZATION` e `SPEC_VALIDATION`.

### 5.3 Mapeamento macro ↔ estados internos

| Macroestágio (fluxo oficial) | Estados internos do Synapse-Flow                            |
| ---------------------------- | ----------------------------------------------------------- |
| `SPEC`                       | `SPEC_DISCOVERY` → `SPEC_NORMALIZATION` → `SPEC_VALIDATION` |
| `TEST_RED`                   | `PLAN` → `TEST_RED`                                         |
| `CODE_GREEN`                 | `CODE_GREEN`                                                |
| `REFACTOR`                   | parte de `CODE_GREEN` (sem estado dedicado no MVP)          |
| `QUALITY_GATE`               | `QUALITY_GATE`                                              |
| `SECURITY_REVIEW`            | `SECURITY`                                                  |
| `REPORT`                     | `DOCUMENT`                                                  |
| `COMMIT`                     | pós-`COMPLETE` (fora da state machine, ação do operador)    |
| —                            | `FAILED` (acessível de qualquer estado não-terminal)        |

### 5.3 Motivação da etapa SPEC

A etapa de especificação transforma intenção em contrato operacional. Ela reduz ambiguidade entre agentes, melhora a geração de testes, aumenta a previsibilidade do parsing e permite validar aderência entre requisito, teste, código e documentação.

### 5.4 Regras da etapa SPEC

- A entrada é a tarefa bruta do usuário.
- A saída é uma SPEC híbrida validável.
- A pipeline não avança para `PLAN` sem validação mínima da SPEC.
- Mudanças relevantes de SPEC durante a run podem invalidar o plano e exigir retorno para `PLAN` ou `TEST_RED`.

---

## 6. Modelo Runtime

### 6.1 Modo CLI efêmero

Usado para:

- executar ou validar `DOCKER_PREFLIGHT` antes do trabalho prático dependente de Docker,
- iniciar runs,
- executar runs curtas inline,
- inspecionar status,
- disparar jobs para execução posterior.

### 6.2 Worker/daemon residente leve

Usado para:

- consumir runs pendentes,
- executar o Synapse-Flow,
- aplicar retries longos,
- persistir progresso,
- gerar artefatos e relatório final.

### 6.3 Motivação do runtime dual

O runtime dual permite preservar a experiência CLI e, ao mesmo tempo, suportar tarefas longas sem bloquear o operador. Também prepara o sistema para crescimento futuro sem obrigar adoção imediata de uma infraestrutura pesada de filas distribuídas.

---

## 7. Diagrama Arquitetural Descritivo

```text
[User Task / CLI Command]
          |
          v
   [Spec Engine]
   |    |    |
   |    |    +--> SPEC_VALIDATION
   |    +--------> SPEC_NORMALIZATION
   +-------------> SPEC_DISCOVERY
          |
          v
 [Orchestrator Engine]
          |
          v
 [State Machine + Pipeline Manager] <--- [DOCKER_PREFLIGHT gate]
          |                                (executado por repo-preflight
          |                                 quando a feature exige Docker)
          +-----------------------------+
          |                             |
          v                             v
 [Memory Engine]               [Adaptive Supervisor]
          |                             |
          +-------------+---------------+
                        |
                        v
                [Task Routing Policy]
                        |
                        v
                 [CLI Adapter Layer]
      +-----------+----------+----------+-----------+
      |           |          |          |           |
      v           v          v          v           v
  [Gemini]     [Codex]   [Copilot] [OpenCode] [Local LLMs]
      |           |          |          |           |
      +-----------+----------+----------+-----------+
                        |
                        v
                  [Raw CLI Outputs]
                        |
                        v
                  [Parsing Engine]
                        |
                        v
               [Structured Step Result]
                        |
                        +----------------------+
                        |                      |
                        v                      v
                [Next Pipeline Step]   [Persistence + Report]
```

---

## 8. Módulos Principais

### 8.1 Orchestrator Engine

Coordena a execução ponta a ponta, cria o contexto da run, invoca o Synapse-Flow e consolida resultados.

### 8.2 State Machine Manager

Modela e valida estados e transições.

Estados implementados no MVP:

- `REQUEST`
- `SPEC_DISCOVERY`
- `SPEC_NORMALIZATION`
- `SPEC_VALIDATION`
- `PLAN`
- `TEST_RED`
- `CODE_GREEN`
- `QUALITY_GATE`
- `REVIEW`
- `SECURITY`
- `DOCUMENT`
- `COMPLETE`
- `FAILED`

> **Pós-MVP (não implementados)**: `INIT` e `RETRYING` estão reservados para versões futuras onde o estado de inicialização precisa de rastreamento explícito e retries têm estado próprio na máquina.

### 8.3 Pipeline Manager

Executa a sequência de steps com suporte a DAG.

Funcionalidades:

- Execução linear (pipeline tradicional);
- Execução paralela de steps independentes via `asyncio.gather`;
- Fan-out/fan-in para steps com múltiplas dependências;
- Detecção de ciclos no grafo de dependências;
- Scheduling otimizado baseado em profundidade do DAG.

### 8.4 Spec Engine

Responsável por:

- converter a demanda bruta em especificação operacional;
- normalizar linguagem, escopo, critérios de aceite e restrições;
- validar schema e completude mínima;
- produzir artefatos estruturados para planejamento e testes.

Subcomponentes sugeridos:

- `spec_discovery`
- `spec_normalizer`
- `spec_validator`
- `spec_repository`

### 8.5 CLI Adapter Layer

Abstrai a execução das ferramentas externas.

Contrato mínimo (implementado em `src/synapse_os/contracts.py`):

```python
@dataclass
class CLIExecutionResult:
    tool_name: str
    command: list[str]
    return_code: int
    stdout_raw: str
    stderr_raw: str
    stdout_clean: str
    duration_ms: int
    timed_out: bool
    success: bool
    metadata: dict[str, Any]
```

### 8.6 Parsing Engine

Transforma saídas ruidosas em artefatos estruturados. Deve operar em múltiplas fases:

1. normalização textual,
2. limpeza via regex,
3. extração de blocos relevantes,
4. validação estrutural,
5. fallback heurístico.

Validações adicionais:

- `ast.parse()` para código Python,
- Pydantic para contratos internos,
- JSON Schema para SPEC.

### 8.7 Memory Engine

Armazena histórico operacional e memória semântica com indexação.

#### IndexedArtifactStore

Armazenamento estruturado com índices:

- Índice por run_id, step_id, tipo de artefato;
- Índice por timestamp para consultas temporais;
- Índice por hash de conteúdo para deduplicação;
- Consultas rápidas via índices secundários.

#### Namespacing

Isolamento de contexto:

- **Workspace**: projetos diferentes;
- **Run**: contexto de execução específica;
- **Step**: contexto de step individual;
- **Global**: padrões compartilhados.

#### Memória operacional

- runs,
- steps,
- eventos,
- falhas,
- retries,
- ferramentas usadas,
- artefatos gerados (via IndexedArtifactStore).

#### Memória semântica

Papel advisory no MVP:

- registrar padrões úteis,
- anotar heurísticas,
- resumir falhas recorrentes,
- enriquecer prompts,
- apoiar análise posterior.

### 8.8 Adaptive Supervisor

Monitora a run e decide sobre:

- retry (com backoff exponencial),
- reroute para outro agente via CapabilityRouter,
- rollback lógico,
- falha terminal,
- reexecução com prompt mais restritivo,
- retorno para etapa anterior em caso de rejeição ou inconsistência,
- per-step policies (configuração por tipo de step).

### 8.9 Runtime Coordinator

Coordena a diferença entre execução inline via CLI e execução assíncrona via worker residente.

Responsabilidades:

- criar runs pendentes,
- aplicar locking,
- retomar runs,
- decidir se a execução será inline ou assíncrona,
- consolidar estado final.

### 8.10 Synapse-Flow

O Synapse-Flow é a engine própria de pipeline do SynapseOS. Ele coordena os estados internos da run, os hand-offs entre steps, o encadeamento `SPEC → TEST_RED → CODE_GREEN → REFACTOR → SECURITY_REVIEW → REPORT` e a integração com supervisor, memória e adapters.

---

## 9. Fluxo de Dados

1. `repo-preflight` valida o `DOCKER_PREFLIGHT` quando a feature exige execução prática.
2. Usuário envia uma tarefa.
3. O CLI cria ou dispara uma run.
4. O Spec Engine produz e valida a SPEC.
5. O Synapse-Flow seleciona o step atual.
6. O Adapter executa a ferramenta externa.
7. O Parsing Engine limpa e valida a saída.
8. O Supervisor decide o próximo movimento.
9. O Memory Engine persiste evento, artefato e observações.
10. Ao final, é gerado um `RUN_REPORT.md`.

### 9.1 Artefatos principais por run

- `SPEC.md` — especificação validada
- `PLAN.md` — plano gerado pelo step PLAN
- `TESTS_RED.md` ou arquivos de teste — gerados no step TEST_RED
- código gerado — produzido no step CODE_GREEN
- `QUALITY_GATE.md` — resultado do gate de qualidade automatizado
- `REVIEW.md` — resultado da revisão de código
- `SECURITY.md` — resultado do gate de segurança
- `DOCUMENT.md` — documentação gerada
- `RUN_REPORT.md` — relatório final consolidado

> **Nota**: `REQUEST.md` foi considerado como artefato inicial da run, mas **não está implementado no MVP**. O pedido do usuário é registrado como metadado da run no banco, não como arquivo de artefato. Pode ser adicionado em versão futura junto com `RUN_REPORT.md`.

---

## 10. Persistência

### 10.1 MVP

- **SQLite** para metadados operacionais.
- Arquivos em disco para artefatos (`raw`, `clean`, `spec`, `plan`, `tests`, `code`, `review`, `docs`, `report`).

### 10.2 Evolução futura

- PostgreSQL para concorrência maior.
- pgvector ou vector DB dedicado quando a memória semântica evoluir.

---

## 11. Tratamento de Erros

- **Falhas de CLI**: detectar binário ausente, erro de autenticação, exit code != 0.
- **Timeouts**: encerrar subprocesso e marcar step como recuperável ou terminal.
- **Parsing errors**: tentar reparse ou reexecução com prompt mais restritivo.
- **Saída corrompida**: rejeitar handoff e registrar artefato bruto.
- **Erros de schema na SPEC**: bloquear avanço para `PLAN`.
- **Falhas de locking/worker**: evitar dupla execução da mesma run.

---

## 12. Observabilidade

### 12.1 Logs

Logs estruturados por run e step.

Campos mínimos:

- `run_id`
- `step`
- `tool_name`
- `return_code`
- `retry_count`
- `duration_ms`
- `timed_out`

> **Nota**: `parser_confidence` foi considerado mas **não está implementado no MVP**. O campo `ParsedOutput` não expõe score de confiança. Caso a heurística de parsing evolua, esse campo pode ser adicionado ao modelo em versão futura.

### 12.2 Relatório por execução

Cada run deve produzir:

```text
artifacts/<run_id>/RUN_REPORT.md
```

Conteúdo mínimo:

- resumo da solicitação,
- SPEC validada,
- estados percorridos,
- ferramentas utilizadas,
- falhas e retries,
- observações do supervisor,
- links para artefatos,
- resumo final.

---

## 13. Segurança e Isolamento

- O sistema roda em container da aplicação.
- Agentes selecionados podem rodar em containers específicos.
- Não usar `shell=True` por padrão.
- Aplicar allowlist de binários e comandos.
- Isolar o workspace da run.
- Registrar outputs brutos para auditoria, com cuidado para segredos.

---

## 14. Escalabilidade e Evolução

### Curto prazo (em implementação)

- paralelizar alguns steps com DAG pipeline — execução paralela implementada em `DAGExecutor`;
- permitir worker residente consumir múltiplas runs — Worker leve residente implementado;
- expandir o Synapse-Flow para DAG simples — DAG execution implementado com `DAGExecutor` e `DAGValidator`.

### Médio prazo

- workers distribuídos;
- PostgreSQL;
- vector memory;
- roteamento automático por memória semântica.

### Longo prazo

- orquestração distribuída durável;
- múltiplos workspaces/branches efêmeras por run;
- políticas adaptativas influenciadas por memória semântica;
- plugin ecosystem maduro.

---

## 15. Documentos Relacionados

- TDD do SynapseOS
- template oficial de SPEC
- documentação de stack e runtime
- ADR-001 a ADR-015

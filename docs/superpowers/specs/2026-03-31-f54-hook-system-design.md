# F54 — Hook System Design

**Data:** 2026-03-31
**Status:** aprovado
**Feature ID:** F54-hook-system

---

## Contexto

O SynapseOS pós-F53 possui foundations sólidas: `ToolSpec`/capabilities (F51), workspace isolation (F52) e observability com `run_events` (F53). O próximo passo lógico é expor pontos de extensão controlados no Synapse-Flow — hooks que permitem injetar lógica de guarda, custo, permissão e observabilidade sem modificar o núcleo da pipeline.

Inspiração arquitetural: Hook System do Claude Code (`PreToolUse`, `PostToolUse`, `SessionStart`) — adaptado para o modelo state-driven do Synapse-Flow.

---

## Decisões de design

| Decisão | Escolha | Razão |
|---|---|---|
| Modelo de execução | Híbrido: `pre_*` síncrono, `post_*` assíncrono | Guards precisam bloquear; observabilidade não deve bloquear |
| Registro | `AppSettings` (global) + frontmatter SPEC (override por run) | Alinha com padrão `SYNAPSE_OS_` existente; SPEC pode especializar |
| Failure mode | Por handler: `hard_fail` ou `supervisor_delegate` | Flexibilidade máxima sem overhead de config global |

---

## Arquitetura

```
AppSettings.hooks (global)
    +
SPEC.hooks (por feature, opcional — merge/disable)
    │
    ▼
HookDispatcher
  ├── _merge(global_hooks, spec_hooks) → lista final auditável
  ├── _load_handlers()                 → importlib na construção
  ├── dispatch_pre(point, ctx)  → HookContext   # síncrono
  └── dispatch_post(point, ctx) → None           # assíncrono fire-and-forget
    │
    ├── PipelineEngine   (pre_step / post_step)
    └── SynapseStateMachine (pre_state_transition / post_state_transition)
```

---

## Pontos de hook

| Ponto | Tipo | Quando dispara |
|---|---|---|
| `pre_step` | síncrono | antes de executar qualquer step do Synapse-Flow |
| `post_step` | assíncrono | após step completar (success ou failure) |
| `pre_state_transition` | síncrono | antes de avançar estado na state machine |
| `post_state_transition` | assíncrono | após transição de estado confirmada |

---

## Contratos novos (`runtime_contracts.py`)

```python
class HookConfig(BaseModel):
    point: Literal["pre_step", "post_step",
                   "pre_state_transition", "post_state_transition"]
    handler: StrictStr          # dotted path: "synapse_os.hooks.cost_tracker.handle"
    failure_mode: Literal["hard_fail", "supervisor_delegate"] = "supervisor_delegate"
    enabled: StrictBool = True

class HookContext(BaseModel):
    run_id: StrictStr
    step_name: StrictStr | None = None
    current_state: StrictStr | None = None
    tool_spec: ToolSpec | None = None
    workspace_path: StrictStr | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class HookResult(BaseModel):
    allowed: StrictBool
    reason: StrictStr | None = None
    context_patch: dict[str, Any] | None = None
    # context_patch: shallow-merged em HookContext.metadata quando allowed=True
    # ignorado quando allowed=False
```

---

## `HookDispatcher` (`src/synapse_os/hooks.py`)

```python
class HookRejectedError(Exception):
    def __init__(self, handler: str, reason: str | None,
                 failure_mode: Literal["hard_fail", "supervisor_delegate"]): ...

class HookDispatcher:
    def __init__(
        self,
        global_hooks: list[HookConfig],
        spec_hooks: list[HookConfig] | None = None,
    ) -> None:
        self._hooks = self._merge(global_hooks, spec_hooks or [])
        self._handlers = self._load_handlers()

    def dispatch_pre(self, point: str, ctx: HookContext) -> HookContext:
        # Retorna HookContext (possivelmente com metadata enriquecido via context_patch).
        # Levanta HookRejectedError(handler, reason, failure_mode) quando allowed=False.
        # O chamador (PipelineEngine / SynapseStateMachine) inspeciona failure_mode
        # para decidir: hard_fail → re-raise; supervisor_delegate → StepResult(failed).
        ...

    async def dispatch_post(self, point: str, ctx: HookContext) -> None: ...
```

### Regras de merge

1. Hooks globais (`AppSettings.hooks`) formam a lista base.
2. SPEC pode **adicionar** handlers extras (append).
3. SPEC pode **desabilitar** um hook global com `enabled: false` + mesmo `handler` + `point`.
4. Resultado auditado em `run_context_initialized.hooks_active`.

### Carregamento de handlers

- Importados via `importlib` na construção do dispatcher.
- `hard_fail` handler com import inválido → `RuntimeError` (fail-fast na startup).
- `supervisor_delegate` handler com import inválido → warning no log, hook desabilitado para a run.

### Assinatura dos handlers

```python
# pre_step / pre_state_transition
def handle(ctx: HookContext) -> HookResult: ...

# post_step / post_state_transition
async def handle(ctx: HookContext) -> None: ...
```

Validado via `inspect.signature` na inicialização.

---

## Integração com `PipelineEngine`

```
execute_step(step):
    ctx = HookContext(run_id, step_name, current_state, tool_spec, workspace_path)

    # 1. pre_step (síncrono)
    try:
        ctx = dispatcher.dispatch_pre("pre_step", ctx)
    except HookRejectedError as e:
        if e.failure_mode == "hard_fail":
            raise StepError(reason="hook_rejected", detail=e.reason)
        else:  # supervisor_delegate
            return StepResult(failed=True, reason=e.reason)

    # 2. execução real do step (sem mudança)

    # 3. post_step (assíncrono, não bloqueia)
    asyncio.create_task(dispatcher.dispatch_post("post_step", ctx_com_resultado))
```

---

## Integração com `SynapseStateMachine`

```
transition(from_state, to_state):
    ctx = HookContext(run_id, current_state=from_state, metadata={"to": to_state})

    # pre_state_transition (síncrono)
    ctx = dispatcher.dispatch_pre("pre_state_transition", ctx)
      → rejeição bloqueia a transição

    # transição real

    # post_state_transition (assíncrono)
    asyncio.create_task(dispatcher.dispatch_post("post_state_transition", ctx))
```

---

## Extensão do frontmatter SPEC

Campo opcional `hooks` no frontmatter:

```yaml
hooks:
  - point: pre_step
    handler: synapse_os.hooks.permission.handle
    failure_mode: hard_fail
  - point: post_step
    handler: synapse_os.hooks.cost_tracker.handle
  - point: pre_step
    handler: synapse_os.hooks.some_global.handle
    enabled: false   # desabilita hook global para esta run
```

`spec_validator` valida schema mas não importa handlers.

---

## Observabilidade

`run_context_initialized` (F53) ganha campo `hooks_active: list[str]` — lista dos handlers efetivos após merge. Auditável na CLI e no `RUN_REPORT.md`.

---

## Arquivos afetados

| Arquivo | Tipo de mudança |
|---|---|
| `src/synapse_os/hooks.py` | **novo** — `HookDispatcher`, `HookRejectedError` |
| `src/synapse_os/runtime_contracts.py` | adição — `HookConfig`, `HookContext`, `HookResult` |
| `src/synapse_os/config.py` | adição — campo `hooks: list[HookConfig]` em `AppSettings` |
| `src/synapse_os/pipeline.py` | modificação — chamadas `dispatch_pre`/`dispatch_post` |
| `src/synapse_os/state_machine.py` | modificação — chamadas de hook em transições |
| `src/synapse_os/specs/validator.py` | modificação — validação do campo `hooks` no frontmatter |
| `src/synapse_os/reporting.py` | modificação — campo `hooks_active` em `run_context_initialized` |
| `tests/unit/test_hook_dispatcher.py` | **novo** |
| `tests/unit/test_pipeline_hook_integration.py` | **novo** |
| `tests/unit/test_state_machine_hooks.py` | **novo** |
| `tests/integration/` | adição — 1 teste CLI end-to-end com hook via `AppSettings` |

---

## Critérios de aceite

- `HookDispatcher` carrega handlers válidos na construção sem erro
- `dispatch_pre` síncrono bloqueia step quando hook retorna `allowed=false`
- `failure_mode=hard_fail` levanta `HookRejectedError`; `supervisor_delegate` retorna `StepResult(failed)`
- `dispatch_post` não propaga exceções de handlers
- Merge de hooks globais + SPEC produz lista auditável em `run_context_initialized`
- `spec_validator` rejeita frontmatter com hooks malformados com `SpecValidationError`
- Cobertura unitária e de integração para todos os pontos de hook expostos

---

## Non-goals

- Hooks extensíveis por usuário final via plugin marketplace
- Hook scheduling (cron, delay)
- Hooks em modo assíncrono bloqueante
- Override de hooks por variável de ambiente por run (somente AppSettings + SPEC)

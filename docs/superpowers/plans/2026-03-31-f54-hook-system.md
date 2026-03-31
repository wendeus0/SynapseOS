# F54 — Hook System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar um sistema de hooks pre/post ao Synapse-Flow que permite injetar guards síncronos e observadores assíncronos em steps e transições de estado, configuráveis via `AppSettings` e frontmatter SPEC.

**Architecture:** `HookConfig` declara handler (dotted path), ponto (`pre_step`, `post_step`, `pre_state_transition`, `post_state_transition`) e `failure_mode`. `HookDispatcher` carrega handlers via `importlib`, faz merge global+SPEC e despacha via `dispatch_pre` (síncrono, pode lançar `HookRejectedError`) e `dispatch_post` (thread daemon, erros swallowed). `PipelineEngine` consome o dispatcher como dependência opcional injetada.

**Tech Stack:** Python 3.12, Pydantic v2, pydantic-settings, threading, importlib, pytest

---

## Mapa de arquivos

| Arquivo | Ação |
|---|---|
| `src/synapse_os/runtime_contracts.py` | Adicionar `HookConfig`, `HookContext`, `HookResult` |
| `src/synapse_os/hooks.py` | **Novo** — `HookRejectedError`, `HookDispatcher` |
| `src/synapse_os/config.py` | Adicionar `hooks: list[HookConfig]` a `AppSettings` |
| `src/synapse_os/specs/validator.py` | Adicionar `hooks: list[HookConfig]` a `SpecMetadata` |
| `src/synapse_os/pipeline.py` | Adicionar `hook_dispatcher` param + `hooks_active` em `PipelineContext` + `_advance_with_hooks` |
| `tests/unit/helpers/__init__.py` | **Novo** — pacote de helpers de teste |
| `tests/unit/helpers/hook_handlers.py` | **Novo** — handlers stub para testes |
| `tests/unit/test_hook_contracts.py` | **Novo** — testes dos contratos |
| `tests/unit/test_hook_dispatcher.py` | **Novo** — testes do dispatcher |
| `tests/unit/test_pipeline_hook_integration.py` | **Novo** — testes de integração pipeline+hooks |
| `tests/integration/test_hook_system_e2e.py` | **Novo** — teste CLI end-to-end |

---

## Task 1: Contratos de hook em `runtime_contracts.py`

**Files:**
- Modify: `src/synapse_os/runtime_contracts.py`
- Create: `tests/unit/test_hook_contracts.py`

- [ ] **Step 1: Escrever testes RED para os contratos**

Criar `tests/unit/test_hook_contracts.py`:

```python
from __future__ import annotations

import pytest


def test_hook_config_rejects_invalid_point() -> None:
    from pydantic import ValidationError
    from synapse_os.runtime_contracts import HookConfig

    with pytest.raises(ValidationError):
        HookConfig(point="invalid_point", handler="some.module.handle")


def test_hook_config_defaults() -> None:
    from synapse_os.runtime_contracts import HookConfig

    h = HookConfig(point="pre_step", handler="some.module.handle")
    assert h.failure_mode == "supervisor_delegate"
    assert h.enabled is True


def test_hook_config_hard_fail_accepted() -> None:
    from synapse_os.runtime_contracts import HookConfig

    h = HookConfig(point="post_step", handler="a.b.c", failure_mode="hard_fail")
    assert h.failure_mode == "hard_fail"


def test_hook_context_metadata_defaults_to_empty() -> None:
    from synapse_os.runtime_contracts import HookContext

    ctx = HookContext(run_id="r1")
    assert ctx.metadata == {}
    assert ctx.step_name is None
    assert ctx.current_state is None


def test_hook_context_accepts_all_optional_fields() -> None:
    from synapse_os.runtime_contracts import HookContext

    ctx = HookContext(
        run_id="r1",
        step_name="PLAN",
        current_state="SPEC_VALIDATION",
        workspace_path="/tmp/ws",
        metadata={"key": "value"},
    )
    assert ctx.step_name == "PLAN"
    assert ctx.metadata == {"key": "value"}


def test_hook_result_defaults() -> None:
    from synapse_os.runtime_contracts import HookResult

    r = HookResult(allowed=True)
    assert r.context_patch is None
    assert r.reason is None


def test_hook_result_allowed_false_with_reason() -> None:
    from synapse_os.runtime_contracts import HookResult

    r = HookResult(allowed=False, reason="permission denied")
    assert not r.allowed
    assert r.reason == "permission denied"
```

- [ ] **Step 2: Rodar testes para confirmar falha por import**

```bash
uv run --no-sync python -m pytest tests/unit/test_hook_contracts.py -v
```

Esperado: `FAILED` — `ImportError: cannot import name 'HookConfig'`

- [ ] **Step 3: Adicionar contratos em `runtime_contracts.py`**

No topo do arquivo, adicionar imports necessários:

```python
# Adicionar após a linha "from pydantic import BaseModel, ConfigDict, Field, StrictStr"
from typing import Any, Literal
from pydantic import StrictBool
```

Após a classe `RunScopedWorkspaceProvider`, adicionar:

```python
class HookConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    point: Literal["pre_step", "post_step", "pre_state_transition", "post_state_transition"]
    handler: StrictStr
    failure_mode: Literal["hard_fail", "supervisor_delegate"] = "supervisor_delegate"
    enabled: StrictBool = True


class HookContext(BaseModel):
    model_config = ConfigDict(strict=True)

    run_id: StrictStr
    step_name: StrictStr | None = None
    current_state: StrictStr | None = None
    tool_spec: "ToolSpec | None" = None
    workspace_path: StrictStr | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class HookResult(BaseModel):
    model_config = ConfigDict(strict=True)

    allowed: StrictBool
    reason: StrictStr | None = None
    context_patch: dict[str, Any] | None = None
    # context_patch: shallow-merged em HookContext.metadata quando allowed=True
    # ignorado quando allowed=False
```

- [ ] **Step 4: Rodar testes para confirmar verde**

```bash
uv run --no-sync python -m pytest tests/unit/test_hook_contracts.py -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Rodar suite completa para confirmar sem regressão**

```bash
uv run --no-sync python -m pytest tests/unit/ -v --tb=short
```

Esperado: todos PASSED (nenhum teste existente quebrado).

- [ ] **Step 6: Commit**

```bash
git add src/synapse_os/runtime_contracts.py tests/unit/test_hook_contracts.py
git commit -m "feat(hooks): add HookConfig, HookContext, HookResult contracts"
```

---

## Task 2: Helpers de teste para handlers stub

**Files:**
- Create: `tests/unit/helpers/__init__.py`
- Create: `tests/unit/helpers/hook_handlers.py`

- [ ] **Step 1: Criar pacote helpers**

Criar `tests/unit/helpers/__init__.py` vazio:

```python
```

- [ ] **Step 2: Criar handlers stub**

Criar `tests/unit/helpers/hook_handlers.py`:

```python
"""Stub hook handlers para testes unitários."""
from __future__ import annotations

from synapse_os.runtime_contracts import HookContext, HookResult

# Rastreamento de chamadas (reset manualmente nos testes que precisam)
call_log: list[tuple[str, HookContext]] = []


def noop_pre(ctx: HookContext) -> HookResult:
    call_log.append(("noop_pre", ctx))
    return HookResult(allowed=True)


def reject_pre(ctx: HookContext) -> HookResult:
    call_log.append(("reject_pre", ctx))
    return HookResult(allowed=False, reason="test rejection")


def patch_pre(ctx: HookContext) -> HookResult:
    call_log.append(("patch_pre", ctx))
    return HookResult(allowed=True, context_patch={"patched": True})


def noop_post(ctx: HookContext) -> None:
    call_log.append(("noop_post", ctx))


def failing_post(ctx: HookContext) -> None:
    call_log.append(("failing_post", ctx))
    raise RuntimeError("intentional post hook failure")
```

- [ ] **Step 3: Verificar importabilidade**

```bash
uv run --no-sync python -c "from tests.unit.helpers.hook_handlers import noop_pre; print('OK')"
```

Esperado: `OK`

- [ ] **Step 4: Commit**

```bash
git add tests/unit/helpers/
git commit -m "test(hooks): add stub hook handlers for unit tests"
```

---

## Task 3: `HookDispatcher` — estrutura base, merge e load

**Files:**
- Create: `src/synapse_os/hooks.py`
- Create: `tests/unit/test_hook_dispatcher.py`

- [ ] **Step 1: Escrever testes RED para merge e load**

Criar `tests/unit/test_hook_dispatcher.py`:

```python
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# HookRejectedError
# ---------------------------------------------------------------------------


def test_hook_rejected_error_carries_failure_mode() -> None:
    from synapse_os.hooks import HookRejectedError

    err = HookRejectedError(
        handler="some.module.handle",
        reason="blocked",
        failure_mode="hard_fail",
    )
    assert err.handler == "some.module.handle"
    assert err.reason == "blocked"
    assert err.failure_mode == "hard_fail"


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


def test_dispatcher_active_handlers_global_only() -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    hooks = [HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.noop_pre")]
    d = HookDispatcher(global_hooks=hooks)
    assert "tests.unit.helpers.hook_handlers.noop_pre" in d.active_handlers


def test_dispatcher_merge_spec_disables_global_hook() -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    global_hooks = [
        HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.noop_pre")
    ]
    spec_hooks = [
        HookConfig(
            point="pre_step",
            handler="tests.unit.helpers.hook_handlers.noop_pre",
            enabled=False,
        )
    ]
    d = HookDispatcher(global_hooks=global_hooks, spec_hooks=spec_hooks)
    assert d.active_handlers == []


def test_dispatcher_merge_spec_adds_extra_hook() -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    global_hooks = [
        HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.noop_pre")
    ]
    spec_hooks = [
        HookConfig(point="post_step", handler="tests.unit.helpers.hook_handlers.noop_post")
    ]
    d = HookDispatcher(global_hooks=global_hooks, spec_hooks=spec_hooks)
    assert "tests.unit.helpers.hook_handlers.noop_pre" in d.active_handlers
    assert "tests.unit.helpers.hook_handlers.noop_post" in d.active_handlers


def test_dispatcher_merge_spec_disable_only_removes_matching_point() -> None:
    """Disabling pre_step handler should not remove same handler registered for post_step."""
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    global_hooks = [
        HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.noop_pre"),
        HookConfig(point="post_step", handler="tests.unit.helpers.hook_handlers.noop_pre"),
    ]
    spec_hooks = [
        HookConfig(
            point="pre_step",
            handler="tests.unit.helpers.hook_handlers.noop_pre",
            enabled=False,
        )
    ]
    d = HookDispatcher(global_hooks=global_hooks, spec_hooks=spec_hooks)
    assert "tests.unit.helpers.hook_handlers.noop_pre" in d.active_handlers
    # post_step registration must survive
    assert len(d.active_handlers) == 1


# ---------------------------------------------------------------------------
# Load handlers
# ---------------------------------------------------------------------------


def test_dispatcher_hard_fail_handler_with_bad_import_raises_at_construction() -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    hooks = [
        HookConfig(
            point="pre_step",
            handler="nonexistent.module.handle",
            failure_mode="hard_fail",
        )
    ]
    with pytest.raises(RuntimeError, match="Failed to load hard_fail hook handler"):
        HookDispatcher(global_hooks=hooks)


def test_dispatcher_supervisor_delegate_handler_with_bad_import_disables_silently(
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    hooks = [
        HookConfig(
            point="pre_step",
            handler="nonexistent.module.handle",
            failure_mode="supervisor_delegate",
        )
    ]
    with caplog.at_level(logging.WARNING, logger="synapse_os.hooks"):
        d = HookDispatcher(global_hooks=hooks)
    assert d.active_handlers == []
    assert "nonexistent.module.handle" in caplog.text


def test_dispatcher_empty_hooks_constructs_without_error() -> None:
    from synapse_os.hooks import HookDispatcher

    d = HookDispatcher(global_hooks=[])
    assert d.active_handlers == []
```

- [ ] **Step 2: Rodar testes para confirmar falha por import**

```bash
uv run --no-sync python -m pytest tests/unit/test_hook_dispatcher.py -v
```

Esperado: `FAILED` — `ModuleNotFoundError: No module named 'synapse_os.hooks'`

- [ ] **Step 3: Criar `src/synapse_os/hooks.py`**

```python
from __future__ import annotations

import importlib
import inspect
import logging
import threading
from typing import TYPE_CHECKING, Any, Callable, Literal

if TYPE_CHECKING:
    from synapse_os.runtime_contracts import HookConfig, HookContext

logger = logging.getLogger(__name__)


class HookRejectedError(Exception):
    """Levantado por dispatch_pre quando um hook retorna allowed=False."""

    def __init__(
        self,
        handler: str,
        reason: str | None,
        failure_mode: Literal["hard_fail", "supervisor_delegate"],
    ) -> None:
        super().__init__(f"Hook '{handler}' rejected: {reason}")
        self.handler = handler
        self.reason = reason
        self.failure_mode = failure_mode


class HookDispatcher:
    def __init__(
        self,
        global_hooks: list[HookConfig],
        spec_hooks: list[HookConfig] | None = None,
    ) -> None:
        self._hooks = self._merge(global_hooks, spec_hooks or [])
        self._handlers: dict[str, Callable[..., Any]] = self._load_handlers()
        self._post_threads: list[threading.Thread] = []

    @property
    def active_handlers(self) -> list[str]:
        return [h.handler for h in self._hooks if h.enabled]

    def _merge(
        self,
        global_hooks: list[HookConfig],
        spec_hooks: list[HookConfig],
    ) -> list[HookConfig]:
        result = list(global_hooks)
        for spec_hook in spec_hooks:
            if not spec_hook.enabled:
                result = [
                    h
                    for h in result
                    if not (h.handler == spec_hook.handler and h.point == spec_hook.point)
                ]
            else:
                result.append(spec_hook)
        return result

    def _load_handlers(self) -> dict[str, Callable[..., Any]]:
        handlers: dict[str, Callable[..., Any]] = {}
        for hook in self._hooks:
            if hook.handler in handlers:
                continue
            try:
                module_path, fn_name = hook.handler.rsplit(".", 1)
                module = importlib.import_module(module_path)
                fn = getattr(module, fn_name)
                handlers[hook.handler] = fn
            except Exception as exc:
                if hook.failure_mode == "hard_fail":
                    raise RuntimeError(
                        f"Failed to load hard_fail hook handler '{hook.handler}': {exc}"
                    ) from exc
                logger.warning(
                    "Failed to load hook handler '%s': %s — hook disabled for this run.",
                    hook.handler,
                    exc,
                )
        return handlers

    def _join_post_handlers(self, timeout: float = 1.0) -> None:
        """Para testes: aguarda threads de post hooks concluírem."""
        for t in self._post_threads:
            t.join(timeout=timeout)
        self._post_threads.clear()
```

- [ ] **Step 4: Rodar testes de merge e load**

```bash
uv run --no-sync python -m pytest tests/unit/test_hook_dispatcher.py -v
```

Esperado: testes de merge e load PASSED, testes de `dispatch_pre`/`dispatch_post` ainda não existem.

- [ ] **Step 5: Rodar suite completa**

```bash
uv run --no-sync python -m pytest tests/unit/ -v --tb=short
```

Esperado: todos PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/synapse_os/hooks.py tests/unit/test_hook_dispatcher.py tests/unit/helpers/
git commit -m "feat(hooks): add HookDispatcher base with merge and handler loading"
```

---

## Task 4: `HookDispatcher.dispatch_pre`

**Files:**
- Modify: `src/synapse_os/hooks.py`
- Modify: `tests/unit/test_hook_dispatcher.py`

- [ ] **Step 1: Adicionar testes RED para `dispatch_pre`**

Adicionar ao final de `tests/unit/test_hook_dispatcher.py`:

```python
# ---------------------------------------------------------------------------
# dispatch_pre
# ---------------------------------------------------------------------------


def test_dispatch_pre_allowed_returns_context_unchanged() -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig, HookContext

    hooks = [HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.noop_pre")]
    d = HookDispatcher(global_hooks=hooks)
    ctx = HookContext(run_id="r1", step_name="PLAN")
    result = d.dispatch_pre("pre_step", ctx)
    assert result.run_id == "r1"
    assert result.step_name == "PLAN"


def test_dispatch_pre_rejected_hard_fail_raises_hook_rejected_error() -> None:
    from synapse_os.hooks import HookDispatcher, HookRejectedError
    from synapse_os.runtime_contracts import HookConfig, HookContext

    hooks = [
        HookConfig(
            point="pre_step",
            handler="tests.unit.helpers.hook_handlers.reject_pre",
            failure_mode="hard_fail",
        )
    ]
    d = HookDispatcher(global_hooks=hooks)
    ctx = HookContext(run_id="r1", step_name="PLAN")

    with pytest.raises(HookRejectedError) as exc_info:
        d.dispatch_pre("pre_step", ctx)

    assert exc_info.value.failure_mode == "hard_fail"
    assert exc_info.value.reason == "test rejection"
    assert exc_info.value.handler == "tests.unit.helpers.hook_handlers.reject_pre"


def test_dispatch_pre_rejected_supervisor_delegate_raises_with_delegate_mode() -> None:
    from synapse_os.hooks import HookDispatcher, HookRejectedError
    from synapse_os.runtime_contracts import HookConfig, HookContext

    hooks = [
        HookConfig(
            point="pre_step",
            handler="tests.unit.helpers.hook_handlers.reject_pre",
            failure_mode="supervisor_delegate",
        )
    ]
    d = HookDispatcher(global_hooks=hooks)
    ctx = HookContext(run_id="r1", step_name="PLAN")

    with pytest.raises(HookRejectedError) as exc_info:
        d.dispatch_pre("pre_step", ctx)

    assert exc_info.value.failure_mode == "supervisor_delegate"


def test_dispatch_pre_context_patch_merged_into_metadata() -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig, HookContext

    hooks = [HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.patch_pre")]
    d = HookDispatcher(global_hooks=hooks)
    ctx = HookContext(run_id="r1")
    result = d.dispatch_pre("pre_step", ctx)
    assert result.metadata.get("patched") is True


def test_dispatch_pre_skips_hooks_registered_for_different_point() -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig, HookContext

    # reject_pre registered for post_step — should NOT run when dispatching pre_step
    hooks = [
        HookConfig(
            point="post_step",
            handler="tests.unit.helpers.hook_handlers.reject_pre",
            failure_mode="hard_fail",
        )
    ]
    d = HookDispatcher(global_hooks=hooks)
    ctx = HookContext(run_id="r1", step_name="PLAN")
    result = d.dispatch_pre("pre_step", ctx)  # must not raise
    assert result.run_id == "r1"


def test_dispatch_pre_no_hooks_returns_context_unchanged() -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookContext

    d = HookDispatcher(global_hooks=[])
    ctx = HookContext(run_id="r1")
    result = d.dispatch_pre("pre_step", ctx)
    assert result.run_id == "r1"
```

- [ ] **Step 2: Rodar testes para confirmar falha por método ausente**

```bash
uv run --no-sync python -m pytest tests/unit/test_hook_dispatcher.py -k "dispatch_pre" -v
```

Esperado: `FAILED` — `AttributeError: 'HookDispatcher' object has no attribute 'dispatch_pre'`

- [ ] **Step 3: Implementar `dispatch_pre` em `src/synapse_os/hooks.py`**

Adicionar método ao `HookDispatcher` (após `_join_post_handlers`):

```python
    def dispatch_pre(self, point: str, ctx: HookContext) -> HookContext:
        """Despacho síncrono. Retorna ctx (possivelmente enriquecido).
        Levanta HookRejectedError quando allowed=False."""
        for hook in self._hooks:
            if hook.point != point or not hook.enabled:
                continue
            fn = self._handlers.get(hook.handler)
            if fn is None:
                continue
            result = fn(ctx)
            if result.context_patch:
                ctx = ctx.model_copy(
                    update={"metadata": {**ctx.metadata, **result.context_patch}}
                )
            if not result.allowed:
                raise HookRejectedError(
                    handler=hook.handler,
                    reason=result.reason,
                    failure_mode=hook.failure_mode,
                )
        return ctx
```

O import de `HookContext` dentro de `TYPE_CHECKING` não é suficiente para runtime. Adicionar import real no topo de `hooks.py`:

```python
# Substituir o bloco TYPE_CHECKING por imports diretos:
from synapse_os.runtime_contracts import HookConfig, HookContext, HookResult
```

E remover `if TYPE_CHECKING:` block.

- [ ] **Step 4: Rodar testes de `dispatch_pre`**

```bash
uv run --no-sync python -m pytest tests/unit/test_hook_dispatcher.py -k "dispatch_pre" -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Rodar suite completa**

```bash
uv run --no-sync python -m pytest tests/unit/ -v --tb=short
```

Esperado: todos PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/synapse_os/hooks.py tests/unit/test_hook_dispatcher.py
git commit -m "feat(hooks): implement dispatch_pre with HookRejectedError"
```

---

## Task 5: `HookDispatcher.dispatch_post`

**Files:**
- Modify: `src/synapse_os/hooks.py`
- Modify: `tests/unit/test_hook_dispatcher.py`

- [ ] **Step 1: Adicionar testes RED para `dispatch_post`**

Adicionar ao final de `tests/unit/test_hook_dispatcher.py`:

```python
# ---------------------------------------------------------------------------
# dispatch_post
# ---------------------------------------------------------------------------


def test_dispatch_post_calls_handler_in_background_thread() -> None:
    from tests.unit.helpers import hook_handlers
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig, HookContext

    hook_handlers.call_log.clear()
    hooks = [HookConfig(point="post_step", handler="tests.unit.helpers.hook_handlers.noop_post")]
    d = HookDispatcher(global_hooks=hooks)
    ctx = HookContext(run_id="r1", step_name="PLAN")

    d.dispatch_post("post_step", ctx)
    d._join_post_handlers(timeout=1.0)

    assert any(name == "noop_post" for name, _ in hook_handlers.call_log)


def test_dispatch_post_does_not_propagate_handler_exception() -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig, HookContext

    hooks = [
        HookConfig(point="post_step", handler="tests.unit.helpers.hook_handlers.failing_post")
    ]
    d = HookDispatcher(global_hooks=hooks)
    ctx = HookContext(run_id="r1", step_name="PLAN")

    d.dispatch_post("post_step", ctx)  # must not raise
    d._join_post_handlers(timeout=1.0)


def test_dispatch_post_logs_warning_on_handler_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig, HookContext

    hooks = [
        HookConfig(point="post_step", handler="tests.unit.helpers.hook_handlers.failing_post")
    ]
    d = HookDispatcher(global_hooks=hooks)
    ctx = HookContext(run_id="r1")

    with caplog.at_level(logging.WARNING, logger="synapse_os.hooks"):
        d.dispatch_post("post_step", ctx)
        d._join_post_handlers(timeout=1.0)

    assert "failing_post" in caplog.text


def test_dispatch_post_skips_hooks_for_different_point() -> None:
    from tests.unit.helpers import hook_handlers
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig, HookContext

    hook_handlers.call_log.clear()
    # handler registrado para pre_step — não deve disparar para post_step
    hooks = [HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.noop_post")]
    d = HookDispatcher(global_hooks=hooks)
    ctx = HookContext(run_id="r1")

    d.dispatch_post("post_step", ctx)
    d._join_post_handlers(timeout=1.0)

    assert hook_handlers.call_log == []
```

- [ ] **Step 2: Rodar testes para confirmar falha por método ausente**

```bash
uv run --no-sync python -m pytest tests/unit/test_hook_dispatcher.py -k "dispatch_post" -v
```

Esperado: `FAILED` — `AttributeError: 'HookDispatcher' object has no attribute 'dispatch_post'`

- [ ] **Step 3: Implementar `dispatch_post` em `src/synapse_os/hooks.py`**

Adicionar ao `HookDispatcher`:

```python
    def dispatch_post(self, point: str, ctx: HookContext) -> None:
        """Despacho assíncrono (thread daemon). Exceções swallowed com warning."""
        for hook in self._hooks:
            if hook.point != point or not hook.enabled:
                continue
            fn = self._handlers.get(hook.handler)
            if fn is None:
                continue
            t = threading.Thread(
                target=self._run_post_handler,
                args=(fn, hook.handler, ctx),
                daemon=True,
            )
            self._post_threads.append(t)
            t.start()

    def _run_post_handler(
        self, fn: Callable[..., Any], handler_name: str, ctx: HookContext
    ) -> None:
        try:
            fn(ctx)
        except Exception as exc:
            logger.warning("Post hook handler '%s' raised: %s", handler_name, exc)
```

- [ ] **Step 4: Rodar testes de `dispatch_post`**

```bash
uv run --no-sync python -m pytest tests/unit/test_hook_dispatcher.py -k "dispatch_post" -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Rodar suite completa do dispatcher**

```bash
uv run --no-sync python -m pytest tests/unit/test_hook_dispatcher.py -v
```

Esperado: todos PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/synapse_os/hooks.py tests/unit/test_hook_dispatcher.py
git commit -m "feat(hooks): implement dispatch_post with fire-and-forget thread dispatch"
```

---

## Task 6: `AppSettings.hooks`

**Files:**
- Modify: `src/synapse_os/config.py`
- Modify: `tests/unit/test_config.py` (adicionar 2 testes)

- [ ] **Step 1: Adicionar testes RED**

Abrir `tests/unit/test_config.py` e adicionar ao final:

```python
def test_app_settings_hooks_defaults_to_empty_list() -> None:
    from synapse_os.config import AppSettings

    settings = AppSettings()
    assert settings.hooks == []


def test_app_settings_hooks_accepts_hook_config_list() -> None:
    from synapse_os.config import AppSettings
    from synapse_os.runtime_contracts import HookConfig

    hook = HookConfig(point="pre_step", handler="synapse_os.hooks_noop.handle")
    settings = AppSettings(hooks=[hook])
    assert len(settings.hooks) == 1
    assert settings.hooks[0].handler == "synapse_os.hooks_noop.handle"
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
uv run --no-sync python -m pytest tests/unit/test_config.py -k "hooks" -v
```

Esperado: `FAILED` — `AppSettings` não tem campo `hooks`.

- [ ] **Step 3: Adicionar campo em `config.py`**

No topo de `config.py`, adicionar import:

```python
from synapse_os.runtime_contracts import HookConfig
```

Na classe `AppSettings`, após `secret_mask_patterns`:

```python
    hooks: list[HookConfig] = Field(default_factory=list)
```

- [ ] **Step 4: Rodar testes**

```bash
uv run --no-sync python -m pytest tests/unit/test_config.py -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/synapse_os/config.py tests/unit/test_config.py
git commit -m "feat(hooks): add hooks field to AppSettings"
```

---

## Task 7: Validação de hooks no frontmatter SPEC

**Files:**
- Modify: `src/synapse_os/specs/validator.py`
- Create: `tests/unit/test_spec_validator_hooks.py`

- [ ] **Step 1: Escrever testes RED**

Criar `tests/unit/test_spec_validator_hooks.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest


def _write_spec_with_hooks(path: Path, hooks_yaml: str) -> None:
    path.write_text(
        f"""\
---
id: F-hook-test
type: feature
summary: Spec com hooks para teste.
inputs:
  - raw_request
outputs:
  - result
acceptance_criteria:
  - Deve validar.
non_goals: []
{hooks_yaml}
---

# Contexto

Teste de hooks no frontmatter.

# Objetivo

Validar parsing e rejeição de hooks inválidos.
""",
        encoding="utf-8",
    )


def test_spec_with_valid_hooks_parses_hook_list(tmp_path: Path) -> None:
    from synapse_os.specs.validator import validate_spec_file

    spec = tmp_path / "SPEC.md"
    _write_spec_with_hooks(
        spec,
        """\
hooks:
  - point: pre_step
    handler: synapse_os.hooks_noop.handle
    failure_mode: hard_fail
  - point: post_step
    handler: synapse_os.hooks_noop.record
""",
    )
    doc = validate_spec_file(spec)
    assert len(doc.metadata.hooks) == 2
    assert doc.metadata.hooks[0].point == "pre_step"
    assert doc.metadata.hooks[0].failure_mode == "hard_fail"
    assert doc.metadata.hooks[1].point == "post_step"


def test_spec_without_hooks_field_produces_empty_list(tmp_path: Path) -> None:
    from synapse_os.specs.validator import validate_spec_file

    spec = tmp_path / "SPEC.md"
    _write_spec_with_hooks(spec, "")  # no hooks key
    doc = validate_spec_file(spec)
    assert doc.metadata.hooks == []


def test_spec_with_invalid_hook_point_raises_spec_validation_error(tmp_path: Path) -> None:
    from synapse_os.specs.validator import SpecValidationError, validate_spec_file

    spec = tmp_path / "SPEC.md"
    _write_spec_with_hooks(
        spec,
        """\
hooks:
  - point: invalid_point
    handler: synapse_os.hooks_noop.handle
""",
    )
    with pytest.raises(SpecValidationError, match="hooks"):
        validate_spec_file(spec)


def test_spec_with_hook_missing_handler_raises_spec_validation_error(tmp_path: Path) -> None:
    from synapse_os.specs.validator import SpecValidationError, validate_spec_file

    spec = tmp_path / "SPEC.md"
    _write_spec_with_hooks(
        spec,
        """\
hooks:
  - point: pre_step
""",
    )
    with pytest.raises(SpecValidationError, match="hooks"):
        validate_spec_file(spec)
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
uv run --no-sync python -m pytest tests/unit/test_spec_validator_hooks.py -v
```

Esperado: `FAILED` — `SpecMetadata` não tem campo `hooks`.

- [ ] **Step 3: Adicionar campo `hooks` a `SpecMetadata` em `validator.py`**

No topo de `validator.py`, adicionar import:

```python
from synapse_os.runtime_contracts import HookConfig
```

Na classe `SpecMetadata`, adicionar após `non_goals`:

```python
    hooks: list[HookConfig] = Field(default_factory=list)
```

No método `_load_metadata`, o bloco `except ValidationError` deve ser atualizado para incluir `hooks` na mensagem de erro. O handler atual usa `exc.errors()[0]["loc"][0]` — isso funciona para qualquer campo incluindo hooks aninhados, então nenhuma mudança adicional é necessária.

- [ ] **Step 4: Rodar testes**

```bash
uv run --no-sync python -m pytest tests/unit/test_spec_validator_hooks.py -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Rodar suite completa**

```bash
uv run --no-sync python -m pytest tests/unit/ -v --tb=short
```

Esperado: todos PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/synapse_os/specs/validator.py tests/unit/test_spec_validator_hooks.py
git commit -m "feat(hooks): add optional hooks field to SpecMetadata with validation"
```

---

## Task 8: Integração `PipelineEngine` — hooks de step

**Files:**
- Modify: `src/synapse_os/pipeline.py`
- Create: `tests/unit/test_pipeline_hook_integration.py`

- [ ] **Step 1: Escrever testes RED**

Criar `tests/unit/test_pipeline_hook_integration.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest


def _make_spec(tmp_path: Path) -> Path:
    spec = tmp_path / "SPEC.md"
    spec.write_text(
        """\
---
id: F-hook-integration
type: feature
summary: Spec para testes de integração de hooks na pipeline.
inputs:
  - raw_request
outputs:
  - result
acceptance_criteria:
  - Deve executar.
non_goals: []
---

# Contexto

Fixture.

# Objetivo

Fixture.
""",
        encoding="utf-8",
    )
    return spec


class _NullExecutor:
    def execute(self, step, context):  # type: ignore[no-untyped-def]
        from synapse_os.pipeline import StepExecutionResult

        return StepExecutionResult(artifacts={}, raw_output="ok", clean_output="ok")


def _make_engine(spec_path: Path, hook_dispatcher=None):  # type: ignore[no-untyped-def]
    from synapse_os.pipeline import PipelineEngine, PipelineState

    executors = {
        s: _NullExecutor()
        for s in [
            PipelineState.PLAN,
            PipelineState.TEST_RED,
            PipelineState.CODE_GREEN,
            PipelineState.QUALITY_GATE,
            PipelineState.REVIEW,
            PipelineState.SECURITY,
            PipelineState.DOCUMENT,
        ]
    }
    return PipelineEngine(executors=executors, hook_dispatcher=hook_dispatcher)


# ---------------------------------------------------------------------------
# pre_step hooks
# ---------------------------------------------------------------------------


def test_pipeline_runs_normally_when_no_hooks_configured(tmp_path: Path) -> None:
    spec = _make_spec(tmp_path)
    engine = _make_engine(spec)
    ctx = engine.run(spec, stop_at="PLAN")
    assert ctx.current_state == "PLAN"


def test_pipeline_pre_step_noop_hook_does_not_block_execution(tmp_path: Path) -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    hooks = [HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.noop_pre")]
    dispatcher = HookDispatcher(global_hooks=hooks)
    spec = _make_spec(tmp_path)
    engine = _make_engine(spec, hook_dispatcher=dispatcher)
    ctx = engine.run(spec, stop_at="PLAN")
    assert ctx.current_state == "PLAN"


def test_pipeline_pre_step_hard_fail_hook_raises_pipeline_execution_error(
    tmp_path: Path,
) -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.pipeline import PipelineExecutionError
    from synapse_os.runtime_contracts import HookConfig

    hooks = [
        HookConfig(
            point="pre_step",
            handler="tests.unit.helpers.hook_handlers.reject_pre",
            failure_mode="hard_fail",
        )
    ]
    dispatcher = HookDispatcher(global_hooks=hooks)
    spec = _make_spec(tmp_path)
    engine = _make_engine(spec, hook_dispatcher=dispatcher)

    with pytest.raises(PipelineExecutionError, match="Hook rejected step"):
        engine.run(spec, stop_at="PLAN")


def test_pipeline_pre_step_supervisor_delegate_hook_triggers_supervisor_path(
    tmp_path: Path,
) -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    hooks = [
        HookConfig(
            point="pre_step",
            handler="tests.unit.helpers.hook_handlers.reject_pre",
            failure_mode="supervisor_delegate",
        )
    ]
    dispatcher = HookDispatcher(global_hooks=hooks)
    spec = _make_spec(tmp_path)
    engine = _make_engine(spec, hook_dispatcher=dispatcher)

    # supervisor_delegate means the error goes to the supervisor (retry/reroute/fail)
    # with _NullExecutor not configured for retries, eventually raises
    with pytest.raises(Exception):
        engine.run(spec, stop_at="PLAN")


def test_pipeline_post_step_hook_fires_after_successful_step(tmp_path: Path) -> None:
    from tests.unit.helpers import hook_handlers
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    hook_handlers.call_log.clear()
    hooks = [
        HookConfig(point="post_step", handler="tests.unit.helpers.hook_handlers.noop_post")
    ]
    dispatcher = HookDispatcher(global_hooks=hooks)
    spec = _make_spec(tmp_path)
    engine = _make_engine(spec, hook_dispatcher=dispatcher)
    engine.run(spec, stop_at="PLAN")
    dispatcher._join_post_handlers(timeout=1.0)

    assert any(name == "noop_post" for name, _ in hook_handlers.call_log)


def test_pipeline_context_hooks_active_populated_when_dispatcher_present(
    tmp_path: Path,
) -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    hooks = [HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.noop_pre")]
    dispatcher = HookDispatcher(global_hooks=hooks)
    spec = _make_spec(tmp_path)
    engine = _make_engine(spec, hook_dispatcher=dispatcher)
    ctx = engine.run(spec, stop_at="SPEC_VALIDATION")
    assert "tests.unit.helpers.hook_handlers.noop_pre" in ctx.hooks_active


def test_pipeline_context_hooks_active_empty_when_no_dispatcher(tmp_path: Path) -> None:
    spec = _make_spec(tmp_path)
    engine = _make_engine(spec)
    ctx = engine.run(spec, stop_at="SPEC_VALIDATION")
    assert ctx.hooks_active == []
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
uv run --no-sync python -m pytest tests/unit/test_pipeline_hook_integration.py -v
```

Esperado: `FAILED` — `PipelineEngine.__init__` não aceita `hook_dispatcher`.

- [ ] **Step 3: Modificar `pipeline.py` — adicionar `hook_dispatcher` e `hooks_active`**

**3a. Adicionar `hooks_active` a `PipelineContext`:**

```python
# Em PipelineContext, adicionar após supervisor_decisions:
    hooks_active: list[StrictStr] = Field(default_factory=list)
```

**3b. Adicionar import em `pipeline.py`:**

```python
from synapse_os.hooks import HookDispatcher, HookRejectedError
```

**3c. Adicionar parâmetro `hook_dispatcher` ao `PipelineEngine.__init__`:**

```python
    def __init__(
        self,
        *,
        settings: AppSettings | None = None,
        executors: dict[str, StepExecutor | dict[str, StepExecutor]] | None = None,
        state_machine: SynapseStateMachine | None = None,
        observer: PipelineObserver | None = None,
        supervisor: Supervisor | None = None,
        cancellation_checker: CancellationChecker | None = None,
        workspace_provider: WorkspaceProvider | None = None,
        hook_dispatcher: HookDispatcher | None = None,
    ) -> None:
        # ... código existente ...
        self.hook_dispatcher = hook_dispatcher
```

**3d. Popular `hooks_active` na criação do contexto em `PipelineEngine.run()`:**

Localizar a criação de `PipelineContext` em `run()` e adicionar `hooks_active`:

```python
        context = PipelineContext(
            spec_path=workspace.spec_path,
            current_state=self.state_machine.current_state,
            run_context=RunContext(
                run_id=run_id,
                initiated_by=initiated_by,
                workspace=workspace,
            ),
            run_id=run_id,
            hooks_active=self.hook_dispatcher.active_handlers if self.hook_dispatcher else [],
        )
```

**3e. Adicionar método `_run_step_with_hooks` em `PipelineEngine`:**

```python
    def _run_step_with_hooks(
        self,
        step: PipelineStep,
        context: PipelineContext,
    ) -> StepExecutionResult | None:
        if self.hook_dispatcher is not None:
            hook_ctx = HookContext(
                run_id=context.run_id or "",
                step_name=step.state,
                current_state=context.current_state,
                workspace_path=str(context.run_context.workspace.root_path),
            )
            try:
                hook_ctx = self.hook_dispatcher.dispatch_pre("pre_step", hook_ctx)
            except HookRejectedError as exc:
                if exc.failure_mode == "hard_fail":
                    raise PipelineExecutionError(
                        f"Hook rejected step '{step.state}': {exc.reason}"
                    ) from exc
                raise RetryableStepError(
                    f"Hook rejected step '{step.state}' (supervisor_delegate): {exc.reason}"
                ) from exc
        else:
            hook_ctx = None

        try:
            return self._run_runtime_step(step, context)
        finally:
            if self.hook_dispatcher is not None and hook_ctx is not None:
                self.hook_dispatcher.dispatch_post("post_step", hook_ctx)
```

Adicionar import de `HookContext` no topo de `pipeline.py`:

```python
from synapse_os.runtime_contracts import (
    RunContext,
    RunLifecycleHooks,
    WorkspaceContext,
    WorkspaceProvider,
    HookContext,
)
```

**3f. Substituir chamadas a `self._run_runtime_step` por `self._run_step_with_hooks`** nos dois blocos que executam steps (SPEC_VALIDATION usa `_execute_spec_validation`, não precisa de hook de step por ser interno; os steps PLAN→DOCUMENT sim):

Localizar:
```python
                    result = self._run_runtime_step(current_step, context)
```

Substituir por:
```python
                    result = self._run_step_with_hooks(current_step, context)
```

- [ ] **Step 4: Rodar testes de integração de pipeline**

```bash
uv run --no-sync python -m pytest tests/unit/test_pipeline_hook_integration.py -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Rodar suite completa**

```bash
uv run --no-sync python -m pytest tests/unit/ -v --tb=short
```

Esperado: todos PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/synapse_os/pipeline.py tests/unit/test_pipeline_hook_integration.py
git commit -m "feat(hooks): integrate HookDispatcher into PipelineEngine for step hooks"
```

---

## Task 9: Hooks de transição de estado

**Files:**
- Modify: `src/synapse_os/pipeline.py`
- Modify: `tests/unit/test_pipeline_hook_integration.py`

- [ ] **Step 1: Adicionar testes RED para transições de estado**

Adicionar ao final de `tests/unit/test_pipeline_hook_integration.py`:

```python
# ---------------------------------------------------------------------------
# State transition hooks
# ---------------------------------------------------------------------------


def test_pre_state_transition_hard_fail_blocks_transition(tmp_path: Path) -> None:
    from synapse_os.hooks import HookDispatcher
    from synapse_os.pipeline import PipelineExecutionError
    from synapse_os.runtime_contracts import HookConfig

    hooks = [
        HookConfig(
            point="pre_state_transition",
            handler="tests.unit.helpers.hook_handlers.reject_pre",
            failure_mode="hard_fail",
        )
    ]
    dispatcher = HookDispatcher(global_hooks=hooks)
    spec = _make_spec(tmp_path)
    engine = _make_engine(spec, hook_dispatcher=dispatcher)

    with pytest.raises(PipelineExecutionError, match="Hook blocked transition"):
        engine.run(spec, stop_at="PLAN")


def test_post_state_transition_hook_fires_after_transition(tmp_path: Path) -> None:
    from tests.unit.helpers import hook_handlers
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    hook_handlers.call_log.clear()
    hooks = [
        HookConfig(
            point="post_state_transition",
            handler="tests.unit.helpers.hook_handlers.noop_post",
        )
    ]
    dispatcher = HookDispatcher(global_hooks=hooks)
    spec = _make_spec(tmp_path)
    engine = _make_engine(spec, hook_dispatcher=dispatcher)
    engine.run(spec, stop_at="SPEC_VALIDATION")
    dispatcher._join_post_handlers(timeout=1.0)

    assert any(name == "noop_post" for name, _ in hook_handlers.call_log)
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
uv run --no-sync python -m pytest tests/unit/test_pipeline_hook_integration.py -k "state_transition" -v
```

Esperado: `FAILED` — sem hooks de transição na pipeline.

- [ ] **Step 3: Adicionar `_advance_with_hooks` ao `PipelineEngine`**

```python
    def _advance_with_hooks(
        self,
        context: PipelineContext,
        from_state: str,
        to_state: str,
    ) -> None:
        """Executa hooks pre/post em torno de uma transição de estado."""
        if self.hook_dispatcher is not None:
            pre_ctx = HookContext(
                run_id=context.run_id or "",
                current_state=from_state,
                metadata={"to_state": to_state},
            )
            try:
                self.hook_dispatcher.dispatch_pre("pre_state_transition", pre_ctx)
            except HookRejectedError as exc:
                if exc.failure_mode == "hard_fail":
                    raise PipelineExecutionError(
                        f"Hook blocked transition {from_state}→{to_state}: {exc.reason}"
                    ) from exc
                raise RetryableStepError(
                    f"Hook blocked transition {from_state}→{to_state} (supervisor_delegate): {exc.reason}"
                ) from exc

        self.state_machine.advance_to(to_state)
        context.current_state = self.state_machine.current_state

        if self.hook_dispatcher is not None:
            post_ctx = HookContext(
                run_id=context.run_id or "",
                current_state=to_state,
                metadata={"from_state": from_state},
            )
            self.hook_dispatcher.dispatch_post("post_state_transition", post_ctx)
```

**Step 3b. Substituir chamadas diretas `self.state_machine.advance_to(...)` + `context.current_state = ...` por `_advance_with_hooks`** nas 4 ocorrências em `PipelineEngine.run()`:

Localizar cada par:
```python
self.state_machine.advance_to(next_state)
context.current_state = self.state_machine.current_state
```

Substituir por:
```python
self._advance_with_hooks(context, str(current_state), str(next_state))
```

E os pares específicos com estado fixo (ex: `PLAN`, `CODE_GREEN`):
```python
# de:
self.state_machine.advance_to(PipelineState.PLAN)
context.current_state = self.state_machine.current_state
# para:
self._advance_with_hooks(context, str(PipelineState.SPEC_VALIDATION), str(PipelineState.PLAN))
```

Repetir para a ocorrência com `PipelineState.CODE_GREEN` (supervisor return_to_code_green):
```python
self._advance_with_hooks(context, str(current_state), str(PipelineState.CODE_GREEN))
```

- [ ] **Step 4: Rodar testes de transição**

```bash
uv run --no-sync python -m pytest tests/unit/test_pipeline_hook_integration.py -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Rodar suite completa**

```bash
uv run --no-sync python -m pytest tests/unit/ -v --tb=short
```

Esperado: todos PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/synapse_os/pipeline.py tests/unit/test_pipeline_hook_integration.py
git commit -m "feat(hooks): add pre/post state transition hooks via _advance_with_hooks"
```

---

## Task 10: Teste de integração end-to-end

**Files:**
- Create: `tests/integration/test_hook_system_e2e.py`

- [ ] **Step 1: Escrever teste E2E**

Criar `tests/integration/test_hook_system_e2e.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest


def _write_minimal_spec(path: Path) -> None:
    path.write_text(
        """\
---
id: F-hook-e2e
type: feature
summary: Spec para teste E2E do hook system.
inputs:
  - raw_request
outputs:
  - result
acceptance_criteria:
  - Hooks devem ser registrados e disparados.
non_goals: []
---

# Contexto

Teste E2E.

# Objetivo

Verificar que hooks configurados via AppSettings são registrados e auditáveis em hooks_active.
""",
        encoding="utf-8",
    )


class _NullExecutor:
    def execute(self, step, context):  # type: ignore[no-untyped-def]
        from synapse_os.pipeline import StepExecutionResult

        return StepExecutionResult(artifacts={}, raw_output="ok", clean_output="ok")


def test_hook_system_hooks_active_reflects_appSettings_hooks(tmp_path: Path) -> None:
    """Hooks configurados em AppSettings devem aparecer em PipelineContext.hooks_active."""
    from synapse_os.config import AppSettings
    from synapse_os.hooks import HookDispatcher
    from synapse_os.pipeline import PipelineEngine, PipelineState
    from synapse_os.runtime_contracts import HookConfig

    spec = tmp_path / "SPEC.md"
    _write_minimal_spec(spec)

    hook_cfg = HookConfig(
        point="pre_step",
        handler="tests.unit.helpers.hook_handlers.noop_pre",
    )
    settings = AppSettings(hooks=[hook_cfg])
    dispatcher = HookDispatcher(global_hooks=settings.hooks)

    executors = {
        s: _NullExecutor()
        for s in [
            PipelineState.PLAN,
            PipelineState.TEST_RED,
        ]
    }
    engine = PipelineEngine(
        settings=settings,
        executors=executors,
        hook_dispatcher=dispatcher,
    )
    ctx = engine.run(spec, stop_at="SPEC_VALIDATION")

    assert "tests.unit.helpers.hook_handlers.noop_pre" in ctx.hooks_active


def test_hook_system_spec_hooks_merged_with_global_hooks(tmp_path: Path) -> None:
    """Hooks de SPEC são mergeados com globais: disable via SPEC funciona."""
    from synapse_os.hooks import HookDispatcher
    from synapse_os.runtime_contracts import HookConfig

    global_hooks = [
        HookConfig(point="pre_step", handler="tests.unit.helpers.hook_handlers.noop_pre")
    ]
    spec_hooks = [
        HookConfig(
            point="pre_step",
            handler="tests.unit.helpers.hook_handlers.noop_pre",
            enabled=False,
        )
    ]
    dispatcher = HookDispatcher(global_hooks=global_hooks, spec_hooks=spec_hooks)
    assert dispatcher.active_handlers == []
```

- [ ] **Step 2: Rodar teste E2E**

```bash
uv run --no-sync python -m pytest tests/integration/test_hook_system_e2e.py -v
```

Esperado: todos PASSED.

- [ ] **Step 3: Rodar suite completa**

```bash
uv run --no-sync python -m pytest -v --tb=short
```

Esperado: todos PASSED, sem regressão.

- [ ] **Step 4: Typecheck e lint**

```bash
uv run --no-sync python -m mypy src/synapse_os/hooks.py src/synapse_os/pipeline.py src/synapse_os/runtime_contracts.py src/synapse_os/config.py
uv run --no-sync ruff check src/synapse_os/hooks.py src/synapse_os/pipeline.py
uv run --no-sync ruff format --check src/synapse_os/hooks.py src/synapse_os/pipeline.py
```

Corrigir qualquer erro de type ou lint antes do próximo passo.

- [ ] **Step 5: Commit final**

```bash
git add tests/integration/test_hook_system_e2e.py
git commit -m "test(hooks): add E2E integration test for hook system with AppSettings"
```

---

## Self-review checklist

- [x] **Spec coverage:** `HookConfig/HookContext/HookResult` → Task 1. `HookDispatcher` merge/load → Task 3. `dispatch_pre` → Task 4. `dispatch_post` → Task 5. `AppSettings.hooks` → Task 6. SPEC frontmatter hooks → Task 7. PipelineEngine step hooks → Task 8. State transition hooks → Task 9. E2E → Task 10. `hooks_active` em `PipelineContext` → Task 8 Step 3.
- [x] **Sem placeholders:** todos os steps têm código completo.
- [x] **Consistência de tipos:** `HookContext` definido em Task 1, importado em Tasks 3-9. `HookRejectedError.failure_mode` definido em Task 3, inspecionado em Tasks 8-9. `PipelineContext.hooks_active` adicionado em Task 8, verificado em Tasks 8+10. `_advance_with_hooks` usa `str(state)` para compatibilidade com `PipelineState(StrEnum)`.

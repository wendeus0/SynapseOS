from __future__ import annotations

import importlib
import logging
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from synapse_os.runtime_contracts import HookConfig, HookContext, HookResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class HookRejectedError(Exception):
    pass


class HookDispatcher:
    def __init__(
        self,
        *,
        global_hooks: list[HookConfig] | None = None,
        spec_hooks: list[HookConfig] | None = None,
    ) -> None:
        self._handlers: dict[str, list[tuple[HookConfig, Callable[..., Any]]]] = {}
        self._active_hooks: list[str] = []
        self._post_threads: list[threading.Thread] = []

        merged = self._merge(global_hooks or [], spec_hooks or [])
        for config in merged:
            handler = self._load_handler(config)
            if handler is None:
                continue
            key = f"{config.point}:{config.handler}"
            self._handlers.setdefault(config.point, []).append((config, handler))
            self._active_hooks.append(key)

    @property
    def hooks_active(self) -> list[str]:
        return list(self._active_hooks)

    def _merge(
        self,
        global_hooks: list[HookConfig],
        spec_hooks: list[HookConfig],
    ) -> list[HookConfig]:
        disabled = {(h.handler, h.point) for h in spec_hooks if not h.enabled}
        enabled_spec = [h for h in spec_hooks if h.enabled]
        enabled_global = [h for h in global_hooks if h.enabled]

        result = [h for h in enabled_global if (h.handler, h.point) not in disabled]
        result.extend(enabled_spec)
        return result

    def _load_handler(self, config: HookConfig) -> Callable[..., Any] | None:
        try:
            module_path, func_name = config.handler.rsplit(".", 1)
        except ValueError:
            self._handle_invalid_handler(
                config, "Handler must be a dotted path (e.g. module.func)"
            )
            return None

        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            self._handle_invalid_handler(config, f"Module '{module_path}' not found")
            return None
        except ImportError:
            self._handle_invalid_handler(
                config, f"Cannot import module '{module_path}'"
            )
            return None

        try:
            func = getattr(module, func_name)
            return func  # type: ignore[no-any-return]
        except AttributeError:
            self._handle_invalid_handler(
                config, f"Function '{func_name}' not found in '{module_path}'"
            )
            return None

    def _handle_invalid_handler(self, config: HookConfig, reason: str) -> None:
        if config.failure_mode == "hard_fail":
            raise RuntimeError(f"Hook handler '{config.handler}' is invalid: {reason}")
        logger.warning(
            "Hook handler '%s' is invalid (%s) — disabling for this run",
            config.handler,
            reason,
        )

    def dispatch_pre(
        self,
        point: str,
        context: HookContext,
    ) -> HookContext:
        handlers = self._handlers.get(point, [])
        for config, handler in handlers:
            try:
                result: HookResult = handler(context)
            except Exception as exc:
                if config.failure_mode == "hard_fail":
                    raise HookRejectedError(
                        f"Hook rejected step '{context.step_name or point}': {exc}"
                    ) from exc
                continue

            if not result.allowed:
                if config.failure_mode == "hard_fail":
                    reason = result.reason or "no reason"
                    raise HookRejectedError(
                        f"Hook rejected step '{context.step_name or point}': {reason}"
                    )
                return context

            if result.context_patch:
                for key, value in result.context_patch.items():
                    context.metadata[key] = value

        return context

    def dispatch_post(
        self,
        point: str,
        context: HookContext,
    ) -> None:
        handlers = self._handlers.get(point, [])
        if not handlers:
            return

        thread = threading.Thread(
            target=self._run_post_handlers,
            args=(point, handlers, context),
            daemon=True,
        )
        self._post_threads.append(thread)
        thread.start()

    def _run_post_handlers(
        self,
        point: str,
        handlers: list[tuple[HookConfig, Callable[..., Any]]],
        context: HookContext,
    ) -> None:
        for config, handler in handlers:
            try:
                handler(context)
            except Exception:
                logger.warning(
                    "Post-hook handler '%s' raised an exception at point '%s'",
                    config.handler,
                    point,
                    exc_info=True,
                )

    def join_post_handlers(self, timeout: float | None = None) -> None:
        for thread in self._post_threads:
            thread.join(timeout=timeout)
        self._post_threads.clear()

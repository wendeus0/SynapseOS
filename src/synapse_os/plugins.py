from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from typing import Any

HOOK_TYPES = frozenset(["pre_step", "post_step", "on_run_start", "on_run_end"])


@dataclass
class HookSpec:
    name: str
    hook_type: str
    handler: Callable[..., Any]


@dataclass
class PluginManifest:
    name: str
    version: str
    enabled: bool = True
    hooks: list[str] = field(default_factory=list)


class PluginLoadError(Exception):
    pass


class PluginRegistry:
    _instance: PluginRegistry | None = None
    _initialized: bool = False

    def __new__(cls) -> PluginRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if PluginRegistry._initialized:
            return
        self._plugins: dict[str, PluginManifest] = {}
        self._handlers: dict[str, list[Callable[..., Any]]] = {ht: [] for ht in HOOK_TYPES}
        self._hook_map: dict[str, dict[str, Callable[..., Any]]] = {}
        PluginRegistry._initialized = True

    def register(self, manifest: PluginManifest) -> None:
        if manifest.name in self._plugins:
            raise PluginLoadError(f"Plugin '{manifest.name}' already registered")
        self._plugins[manifest.name] = manifest

    def unregister(self, name: str) -> None:
        if name not in self._plugins:
            raise PluginLoadError(f"Plugin '{name}' not found")
        del self._plugins[name]
        if name in self._hook_map:
            for hook_type, handler in list(self._hook_map[name].items()):
                if handler in self._handlers.get(hook_type, []):
                    self._handlers[hook_type].remove(handler)
            del self._hook_map[name]

    def get_plugin(self, name: str) -> PluginManifest | None:
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        return list(self._plugins.keys())

    def is_loaded(self, name: str) -> bool:
        return name in self._plugins

    def enable_plugin(self, name: str) -> None:
        if name in self._plugins:
            self._plugins[name].enabled = True

    def disable_plugin(self, name: str) -> None:
        if name in self._plugins:
            self._plugins[name].enabled = False

    def register_hook(self, plugin_name: str, hook_type: str, handler: Callable[..., Any]) -> None:
        if hook_type not in HOOK_TYPES:
            raise ValueError(f"Unknown hook type: {hook_type}")
        if plugin_name not in self._plugins:
            raise PluginLoadError(f"Plugin '{plugin_name}' not registered")
        if plugin_name not in self._hook_map:
            self._hook_map[plugin_name] = {}
        self._hook_map[plugin_name][hook_type] = handler
        if hook_type not in self._handlers:
            self._handlers[hook_type] = []
        if handler not in self._handlers[hook_type]:
            self._handlers[hook_type].append(handler)

    def get_handlers(self, hook_type: str) -> list[Callable[..., Any]]:
        return list(self._handlers.get(hook_type, []))

    def load_plugins(self) -> None:
        eps = entry_points(group="synapse_os.plugins")
        if hasattr(eps, "select"):
            eps = eps.select(group="synapse_os.plugins")
        for ep in eps:
            try:
                module = ep.load()
                manifest = getattr(module, "hook_manifest", None)
                if manifest is None:
                    continue
                manifest_obj = manifest()
                if isinstance(manifest_obj, PluginManifest):
                    self.register(manifest_obj)
            except Exception:
                pass

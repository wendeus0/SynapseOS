from __future__ import annotations

from dataclasses import dataclass, field

from synapse_os.adapters import BaseCLIAdapter


class AdapterAlreadyRegisteredError(ValueError):
    pass


class AdapterNotFoundError(KeyError):
    pass


class NoSuitableAdapterError(RuntimeError):
    pass


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, BaseCLIAdapter] = {}

    def register(self, adapter: BaseCLIAdapter) -> None:
        if adapter.tool_name in self._adapters:
            raise AdapterAlreadyRegisteredError(
                f"Adapter '{adapter.tool_name}' is already registered."
            )
        self._adapters[adapter.tool_name] = adapter

    def unregister(self, name: str) -> None:
        if name not in self._adapters:
            raise AdapterNotFoundError(f"Adapter '{name}' not found.")
        del self._adapters[name]

    def get(self, name: str) -> BaseCLIAdapter | None:
        return self._adapters.get(name)

    def list_all(self) -> list[BaseCLIAdapter]:
        return list(self._adapters.values())

    def find_by_capability(self, capability: str) -> list[BaseCLIAdapter]:
        return [
            adapter for adapter in self._adapters.values() if capability in adapter.capabilities
        ]

    def all_capabilities(self) -> set[str]:
        caps: set[str] = set()
        for adapter in self._adapters.values():
            caps.update(adapter.capabilities)
        return caps


class CapabilityRouter:
    def __init__(self, registry: AdapterRegistry) -> None:
        self.registry = registry

    def select_adapter(self, required_capabilities: set[str]) -> BaseCLIAdapter | None:
        if not required_capabilities:
            adapters = self.registry.list_all()
            return adapters[0] if adapters else None

        for capability in required_capabilities:
            matches = self.registry.find_by_capability(capability)
            if matches:
                return matches[0]

        return None

    def get_best_match(self, required_capabilities: set[str]) -> BaseCLIAdapter | None:
        if not required_capabilities:
            adapters = self.registry.list_all()
            return adapters[0] if adapters else None

        all_adapters = self.registry.list_all()
        if not all_adapters:
            return None

        scored: list[tuple[int, BaseCLIAdapter]] = []
        for adapter in all_adapters:
            overlap = len(set(adapter.capabilities) & required_capabilities)
            if overlap > 0:
                scored.append((overlap, adapter))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]

        return all_adapters[0]


@dataclass
class MultiAgentCoordinator:
    registry: AdapterRegistry
    router: CapabilityRouter
    required_steps: set[str] = field(default_factory=set)
    _handoff_log: list[dict[str, str]] = field(default_factory=list)

    def resolve_adapter_for_step(
        self,
        step_name: str,
        required_capabilities: set[str],
    ) -> BaseCLIAdapter | None:
        adapter = self.router.get_best_match(required_capabilities)

        if adapter is None and step_name in self.required_steps:
            raise NoSuitableAdapterError(
                f"No suitable adapter found for required step '{step_name}' "
                f"with capabilities {required_capabilities}."
            )

        if adapter is not None:
            self._handoff_log.append(
                {
                    "step": step_name,
                    "adapter": adapter.tool_name,
                    "capabilities": (
                        ",".join(required_capabilities) if required_capabilities else ""
                    ),
                }
            )

        return adapter

    def get_handoff_log(self) -> list[dict[str, str]]:
        return list(self._handoff_log)

    def clear_handoff_log(self) -> None:
        self._handoff_log.clear()

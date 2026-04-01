from __future__ import annotations

import pytest

from synapse_os.adapters import BaseCLIAdapter, CodexCLIAdapter, GeminiCLIAdapter
from synapse_os.contracts import CLIExecutionResult
from synapse_os.multi_agent import (
    AdapterAlreadyRegisteredError,
    AdapterNotFoundError,
    AdapterRegistry,
    CapabilityRouter,
    MultiAgentCoordinator,
    NoSuitableAdapterError,
)


class FakeAdapter(BaseCLIAdapter):
    def __init__(
        self,
        *,
        tool_name: str = "fake",
        capabilities: tuple[str, ...] = ("cli_execution",),
        command_prefix: tuple[str, ...] = (),
    ) -> None:
        self._capabilities = capabilities
        self._command_prefix = command_prefix
        super().__init__(tool_name=tool_name)

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self._capabilities

    @property
    def command_prefix(self) -> tuple[str, ...]:
        return self._command_prefix

    def build_command(self, prompt: str) -> list[str]:
        return ["echo", prompt]


# --- AdapterRegistry tests ---


class TestAdapterRegistry:
    def test_registrar_adapter_por_nome(self) -> None:
        registry = AdapterRegistry()
        adapter = FakeAdapter(tool_name="test_adapter")
        registry.register(adapter)

        assert registry.get("test_adapter") is adapter

    def test_rejeitar_registro_duplicado(self) -> None:
        registry = AdapterRegistry()
        adapter = FakeAdapter(tool_name="dup")
        registry.register(adapter)

        with pytest.raises(AdapterAlreadyRegisteredError):
            registry.register(adapter)

    def test_retornar_none_para_adapter_inexistente(self) -> None:
        registry = AdapterRegistry()
        assert registry.get("nonexistent") is None

    def test_listar_todos_os_adapters(self) -> None:
        registry = AdapterRegistry()
        a1 = FakeAdapter(tool_name="a1")
        a2 = FakeAdapter(tool_name="a2")
        registry.register(a1)
        registry.register(a2)

        all_adapters = registry.list_all()
        assert len(all_adapters) == 2
        assert {a.tool_name for a in all_adapters} == {"a1", "a2"}

    def test_encontrar_adapters_por_capability(self) -> None:
        registry = AdapterRegistry()
        a1 = FakeAdapter(
            tool_name="coder", capabilities=("cli_execution", "code_generation")
        )
        a2 = FakeAdapter(
            tool_name="planner", capabilities=("cli_execution", "planning")
        )
        registry.register(a1)
        registry.register(a2)

        coders = registry.find_by_capability("code_generation")
        assert len(coders) == 1
        assert coders[0].tool_name == "coder"

        planners = registry.find_by_capability("planning")
        assert len(planners) == 1
        assert planners[0].tool_name == "planner"

    def test_retornar_lista_vazia_se_nenhuma_capability_match(self) -> None:
        registry = AdapterRegistry()
        registry.register(FakeAdapter(tool_name="basic"))

        result = registry.find_by_capability("nonexistent_capability")
        assert result == []

    def test_encontrar_multiplos_adapters_com_mesma_capability(self) -> None:
        registry = AdapterRegistry()
        a1 = FakeAdapter(tool_name="coder1", capabilities=("code_generation",))
        a2 = FakeAdapter(tool_name="coder2", capabilities=("code_generation",))
        registry.register(a1)
        registry.register(a2)

        result = registry.find_by_capability("code_generation")
        assert len(result) == 2

    def test_remover_adapter(self) -> None:
        registry = AdapterRegistry()
        adapter = FakeAdapter(tool_name="removable")
        registry.register(adapter)
        registry.unregister("removable")

        assert registry.get("removable") is None
        assert "removable" not in [a.tool_name for a in registry.list_all()]

    def test_retornar_todas_as_capabilities_registradas(self) -> None:
        registry = AdapterRegistry()
        registry.register(FakeAdapter(tool_name="a1", capabilities=("cap1", "cap2")))
        registry.register(FakeAdapter(tool_name="a2", capabilities=("cap2", "cap3")))

        all_caps = registry.all_capabilities()
        assert all_caps == {"cap1", "cap2", "cap3"}


# --- CapabilityRouter tests ---


class TestCapabilityRouter:
    def test_selecionar_adapter_com_capability_requerida(self) -> None:
        registry = AdapterRegistry()
        registry.register(
            FakeAdapter(tool_name="coder", capabilities=("code_generation",))
        )
        registry.register(
            FakeAdapter(tool_name="basic", capabilities=("cli_execution",))
        )

        router = CapabilityRouter(registry)
        selected = router.select_adapter({"code_generation"})

        assert selected is not None
        assert selected.tool_name == "coder"

    def test_retornar_none_se_nenhum_adapter_tiver_capability(self) -> None:
        registry = AdapterRegistry()
        registry.register(FakeAdapter(tool_name="basic"))

        router = CapabilityRouter(registry)
        selected = router.select_adapter({"nonexistent"})

        assert selected is None

    def test_selecionar_adapter_com_melhor_match(self) -> None:
        registry = AdapterRegistry()
        registry.register(
            FakeAdapter(
                tool_name="specialist", capabilities=("code_generation", "code_review")
            )
        )
        registry.register(
            FakeAdapter(tool_name="generalist", capabilities=("code_generation",))
        )

        router = CapabilityRouter(registry)
        selected = router.get_best_match({"code_generation", "code_review"})

        assert selected is not None
        assert selected.tool_name == "specialist"

    def test_usar_primeiro_adapter_como_fallback(self) -> None:
        registry = AdapterRegistry()
        registry.register(FakeAdapter(tool_name="first"))
        registry.register(FakeAdapter(tool_name="second"))

        router = CapabilityRouter(registry)
        selected = router.get_best_match({"nonexistent"})

        assert selected is not None
        assert selected.tool_name == "first"

    def test_retornar_none_se_registry_vazio(self) -> None:
        registry = AdapterRegistry()
        router = CapabilityRouter(registry)

        assert router.select_adapter({"anything"}) is None
        assert router.get_best_match({"anything"}) is None

    def test_priorizar_adapter_com_mais_capabilities_sobrepostas(self) -> None:
        registry = AdapterRegistry()
        registry.register(
            FakeAdapter(tool_name="partial", capabilities=("cap1", "cap2"))
        )
        registry.register(
            FakeAdapter(tool_name="full", capabilities=("cap1", "cap2", "cap3"))
        )

        router = CapabilityRouter(registry)
        selected = router.get_best_match({"cap1", "cap2", "cap3"})

        assert selected is not None
        assert selected.tool_name == "full"


# --- MultiAgentCoordinator tests ---


class TestMultiAgentCoordinator:
    def test_executar_step_com_adapter_selecionado(self) -> None:
        registry = AdapterRegistry()
        registry.register(
            FakeAdapter(tool_name="coder", capabilities=("code_generation",))
        )

        router = CapabilityRouter(registry)
        coordinator = MultiAgentCoordinator(registry, router)

        adapter = coordinator.resolve_adapter_for_step(
            "CODE_GREEN", {"code_generation"}
        )
        assert adapter is not None
        assert adapter.tool_name == "coder"

    def test_retornar_none_se_nenhum_adapter_disponivel(self) -> None:
        registry = AdapterRegistry()
        router = CapabilityRouter(registry)
        coordinator = MultiAgentCoordinator(registry, router)

        adapter = coordinator.resolve_adapter_for_step("CODE_GREEN", {"nonexistent"})
        assert adapter is None

    def test_registrar_handoff_no_contexto(self) -> None:
        registry = AdapterRegistry()
        registry.register(
            FakeAdapter(tool_name="coder", capabilities=("code_generation",))
        )

        router = CapabilityRouter(registry)
        coordinator = MultiAgentCoordinator(registry, router)

        handoffs = coordinator.get_handoff_log()
        assert len(handoffs) == 0

        coordinator.resolve_adapter_for_step("CODE_GREEN", {"code_generation"})

        handoffs = coordinator.get_handoff_log()
        assert len(handoffs) == 1
        assert handoffs[0]["step"] == "CODE_GREEN"
        assert handoffs[0]["adapter"] == "coder"

    def test_usar_fallback_adapter_quando_nenhuma_capability_especificada(self) -> None:
        registry = AdapterRegistry()
        registry.register(FakeAdapter(tool_name="generic"))

        router = CapabilityRouter(registry)
        coordinator = MultiAgentCoordinator(registry, router)

        adapter = coordinator.resolve_adapter_for_step("PLAN", set())
        assert adapter is not None
        assert adapter.tool_name == "generic"

    def test_lancar_erro_se_adapter_nao_encontrado_para_step_obrigatorio(self) -> None:
        registry = AdapterRegistry()
        router = CapabilityRouter(registry)
        coordinator = MultiAgentCoordinator(
            registry, router, required_steps={"CODE_GREEN"}
        )

        with pytest.raises(NoSuitableAdapterError):
            coordinator.resolve_adapter_for_step("CODE_GREEN", {"code_generation"})

    def test_executar_com_adapters_reais(self) -> None:
        registry = AdapterRegistry()
        registry.register(CodexCLIAdapter())
        registry.register(GeminiCLIAdapter())

        router = CapabilityRouter(registry)
        coordinator = MultiAgentCoordinator(registry, router)

        codex_adapter = coordinator.resolve_adapter_for_step(
            "CODE_GREEN", {"code_generation"}
        )
        assert codex_adapter is not None
        assert codex_adapter.tool_name == "codex"

        gemini_adapter = coordinator.resolve_adapter_for_step("PLAN", {"planning"})
        assert gemini_adapter is not None
        assert gemini_adapter.tool_name == "gemini"

    def test_registrar_todas_as_execucoes(self) -> None:
        registry = AdapterRegistry()
        registry.register(FakeAdapter(tool_name="a1", capabilities=("cap1",)))
        registry.register(FakeAdapter(tool_name="a2", capabilities=("cap2",)))

        router = CapabilityRouter(registry)
        coordinator = MultiAgentCoordinator(registry, router)

        coordinator.resolve_adapter_for_step("STEP1", {"cap1"})
        coordinator.resolve_adapter_for_step("STEP2", {"cap2"})
        coordinator.resolve_adapter_for_step("STEP3", {"cap1"})

        handoffs = coordinator.get_handoff_log()
        assert len(handoffs) == 3
        assert handoffs[0]["step"] == "STEP1"
        assert handoffs[1]["step"] == "STEP2"
        assert handoffs[2]["step"] == "STEP3"

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest


class TestRuntimeCoordinatorHardening:
    def test_health_status_returns_healthy_when_all_circuit_breakers_closed(
        self,
    ) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        coordinator.circuit_breaker_store = MagicMock()
        coordinator.circuit_breaker_store.is_open.return_value = False
        status = coordinator.health_status()
        assert status == "HEALTHY"

    def test_health_status_returns_degraded_when_any_circuit_breaker_open(self) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        coordinator.circuit_breaker_store = MagicMock()
        coordinator.circuit_breaker_store.is_open.side_effect = (
            lambda tool: tool == "codex"
        )
        status = coordinator.health_status()
        assert status == "DEGRADED"

    def test_health_status_returns_unhealthy_when_multiple_circuit_breakers_open(
        self,
    ) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        coordinator.circuit_breaker_store = MagicMock()
        coordinator.circuit_breaker_store.is_open.return_value = True
        status = coordinator.health_status()
        assert status == "UNHEALTHY"

    def test_lifecycle_event_appends_to_event_log(self) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        coordinator.lifecycle_event("runtime.starting")
        coordinator.lifecycle_event("runtime.started")
        assert len(coordinator.lifecycle_events) == 2
        assert coordinator.lifecycle_events[0].event == "runtime.starting"
        assert coordinator.lifecycle_events[1].event == "runtime.started"

    def test_lifecycle_event_contains_timestamp(self) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        coordinator.lifecycle_event("runtime.starting")
        event = coordinator.lifecycle_events[0]
        assert event.timestamp > 0

    def test_register_cleanup_handler(self) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        handler = MagicMock()
        coordinator.register_cleanup_handler(handler)
        assert handler in coordinator._cleanup_handlers

    def test_run_cleanup_handlers_calls_registered_handlers(self) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        handler1 = MagicMock()
        handler2 = MagicMock()
        coordinator.register_cleanup_handler(handler1)
        coordinator.register_cleanup_handler(handler2)
        coordinator.run_cleanup_handlers()
        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_run_cleanup_handlers_continues_after_handler_error(self) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        good_handler = MagicMock()
        bad_handler = MagicMock(side_effect=RuntimeError("cleanup error"))
        coordinator.register_cleanup_handler(bad_handler)
        coordinator.register_cleanup_handler(good_handler)
        coordinator.run_cleanup_handlers()
        good_handler.assert_called_once()

    def test_graceful_shutdown_calls_cleanup_then_stop(self) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        cleanup_mock = MagicMock()
        coordinator.register_cleanup_handler(cleanup_mock)
        stop_mock = MagicMock()
        coordinator._stop = stop_mock
        coordinator.graceful_shutdown(timeout_seconds=5)
        cleanup_mock.assert_called_once()
        stop_mock.assert_called_once()

    def test_shutdown_respects_timeout(self) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        slow_handler = MagicMock(side_effect=lambda: time.sleep(10))
        coordinator.register_cleanup_handler(slow_handler)
        stop_mock = MagicMock()
        coordinator._stop = stop_mock
        start = time.monotonic()
        coordinator.graceful_shutdown(timeout_seconds=0.1)
        elapsed = time.monotonic() - start
        assert elapsed < 1.0

    def test_degraded_adapters_reflects_open_circuit_breakers(self) -> None:
        from synapse_os.runtime.service import RuntimeCoordinator

        coordinator = RuntimeCoordinator()
        coordinator.circuit_breaker_store = MagicMock()
        coordinator.circuit_breaker_store.is_open.side_effect = lambda tool: (
            tool in ("codex", "gemini")
        )
        coordinator.circuit_breaker_store.read.side_effect = lambda tool: (
            MagicMock(
                tool_name=tool,
                consecutive_operational_failures=3,
                opened_at=time.time(),
                cooldown_until=time.time() + 300,
            )
            if tool in ("codex", "gemini")
            else None
        )
        degraded = coordinator.degraded_adapters
        assert "codex" in degraded
        assert "gemini" in degraded


class TestRuntimeLifecycleEvent:
    def test_lifecycle_event_model_has_required_fields(self) -> None:
        from synapse_os.runtime.service import RuntimeLifecycleEvent

        event = RuntimeLifecycleEvent(event="runtime.started", data={"pid": 12345})
        assert event.event == "runtime.started"
        assert event.data == {"pid": 12345}
        assert event.timestamp > 0

    def test_lifecycle_event_default_data_is_empty_dict(self) -> None:
        from synapse_os.runtime.service import RuntimeLifecycleEvent

        event = RuntimeLifecycleEvent(event="runtime.stopping")
        assert event.data == {}

from __future__ import annotations

import asyncio
from importlib import import_module

import pytest


class _BlockingProcess:
    def __init__(self, release_event: asyncio.Event, content: bytes) -> None:
        self.release_event = release_event
        self.content = content
        self.returncode = 0
        self.killed = False

    async def communicate(self) -> tuple[bytes, bytes]:
        await self.release_event.wait()
        return self.content, b""

    def kill(self) -> None:
        self.killed = True


def test_adapter_concurrency_flow_uses_env_limit_to_serialize_subprocess_spawns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = import_module("aignt_os.adapters")
    adapters._ADAPTER_EXECUTION_GUARDS.clear()
    monkeypatch.setenv("AIGNT_OS_MAX_CONCURRENT_ADAPTERS", "1")

    class FakeAdapter(adapters.BaseCLIAdapter):
        def build_command(self, prompt: str) -> list[str]:
            return ["fake-tool", prompt]

    first_release = asyncio.Event()
    second_release = asyncio.Event()
    spawn_order: list[str] = []

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _BlockingProcess:
        del kwargs
        prompt = command[-1]
        spawn_order.append(prompt)
        return _BlockingProcess(
            first_release if prompt == "first" else second_release,
            prompt.encode("utf-8") + b"\n",
        )

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    async def scenario() -> None:
        first = FakeAdapter(tool_name="fake-tool")
        second = FakeAdapter(tool_name="fake-tool")

        first_task = asyncio.create_task(first.execute("first"))
        await asyncio.sleep(0)
        second_task = asyncio.create_task(second.execute("second"))
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert spawn_order == ["first"]

        first_release.set()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert spawn_order == ["first", "second"]

        second_release.set()
        first_result, second_result = await asyncio.gather(first_task, second_task)
        assert first_result.stdout_clean == "first"
        assert second_result.stdout_clean == "second"

    asyncio.run(scenario())

from __future__ import annotations

import asyncio
from importlib import import_module

import pytest


def _adapters_module():
    return import_module("aignt_os.adapters")


class _FakeAdapterMixin:
    def build_command(self, prompt: str) -> list[str]:
        return ["fake-tool", "--prompt", prompt]


class _FakeProcess:
    def __init__(
        self,
        *,
        stdout: bytes,
        stderr: bytes,
        returncode: int,
    ) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode
        self.killed = False

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr

    def kill(self) -> None:
        self.killed = True


class _BlockingProcess(_FakeProcess):
    def __init__(
        self,
        *,
        stdout: bytes,
        stderr: bytes,
        returncode: int,
        release_event: asyncio.Event,
    ) -> None:
        super().__init__(stdout=stdout, stderr=stderr, returncode=returncode)
        self.release_event = release_event

    async def communicate(self) -> tuple[bytes, bytes]:
        await self.release_event.wait()
        return await super().communicate()


def test_base_cli_adapter_executes_subprocess_and_sanitizes_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = _adapters_module()

    class FakeAdapter(_FakeAdapterMixin, adapters.BaseCLIAdapter):
        pass

    fake_process = _FakeProcess(
        stdout=b"\x1b[32mhello\x1b[0m\n",
        stderr=b"\x1b[31mwarn\x1b[0m\n",
        returncode=0,
    )

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        assert list(command) == ["fake-tool", "--prompt", "plan feature"]
        assert kwargs["stdin"] is asyncio.subprocess.DEVNULL
        assert kwargs["stdout"] is asyncio.subprocess.PIPE
        assert kwargs["stderr"] is asyncio.subprocess.PIPE
        return fake_process

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    result = asyncio.run(FakeAdapter(tool_name="fake-tool").execute("plan feature"))

    assert result.tool_name == "fake-tool"
    assert result.command == ["fake-tool", "--prompt", "plan feature"]
    assert result.stdout_raw == "\x1b[32mhello\x1b[0m\n"
    assert result.stderr_raw == "\x1b[31mwarn\x1b[0m\n"
    assert result.stdout_clean == "hello"
    assert result.stderr_clean == "warn"
    assert result.duration_ms >= 0
    assert result.timed_out is False
    assert result.success is True


def test_base_cli_adapter_masks_secrets_and_normalizes_unicode_in_clean_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = _adapters_module()

    class FakeAdapter(_FakeAdapterMixin, adapters.BaseCLIAdapter):
        pass

    fake_process = _FakeProcess(
        stdout=b"\x1b[32mBearer secret-token\x1b[0m e\xcc\x81 \xe2\x80\xae\xef\xbc\xa6\n",
        stderr=b"sk-secret123\n",
        returncode=0,
    )

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        del command, kwargs
        return fake_process

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    result = asyncio.run(FakeAdapter(tool_name="fake-tool").execute("plan feature"))

    assert "\x1b[" not in result.stdout_clean
    assert "Bearer secret-token" not in result.stdout_clean
    assert "sk-secret123" not in result.stderr_clean
    assert "é" in result.stdout_clean
    assert "\u202E" not in result.stdout_clean
    assert "F" in result.stdout_clean
    assert "[REDACTED]" in result.stdout_clean
    assert "[REDACTED]" in result.stderr_clean


def test_base_cli_adapter_marks_nonzero_exit_as_unsuccessful(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = _adapters_module()

    class FakeAdapter(_FakeAdapterMixin, adapters.BaseCLIAdapter):
        pass

    fake_process = _FakeProcess(stdout=b"ok\n", stderr=b"boom\n", returncode=2)

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        del command, kwargs
        return fake_process

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    result = asyncio.run(FakeAdapter(tool_name="fake-tool").execute("plan feature"))

    assert result.return_code == 2
    assert result.timed_out is False
    assert result.success is False
    assert result.stderr_clean == "boom"


def test_base_cli_adapter_handles_timeout_and_kills_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = _adapters_module()

    class FakeAdapter(_FakeAdapterMixin, adapters.BaseCLIAdapter):
        pass

    fake_process = _FakeProcess(stdout=b"", stderr=b"timed out\n", returncode=-9)

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        del command, kwargs
        return fake_process

    async def fake_wait_for(awaitable: object, timeout: float) -> tuple[bytes, bytes]:
        del timeout
        awaitable.close()
        raise TimeoutError

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(adapters.asyncio, "wait_for", fake_wait_for)

    result = asyncio.run(
        FakeAdapter(tool_name="fake-tool", timeout_seconds=0.01).execute("plan feature")
    )

    assert fake_process.killed is True
    assert result.return_code == -9
    assert result.timed_out is True
    assert result.success is False
    assert result.stderr_clean == "timed out"


def test_base_cli_adapter_waits_for_available_slot_when_limit_is_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = _adapters_module()
    adapters._ADAPTER_EXECUTION_GUARDS.clear()

    class FakeAdapter(_FakeAdapterMixin, adapters.BaseCLIAdapter):
        pass

    first_release = asyncio.Event()
    second_release = asyncio.Event()
    second_started = asyncio.Event()
    spawn_order: list[str] = []

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        del kwargs
        prompt = command[-1]
        spawn_order.append(prompt)
        if prompt == "first":
            return _BlockingProcess(
                stdout=b"first\n",
                stderr=b"",
                returncode=0,
                release_event=first_release,
            )
        second_started.set()
        return _BlockingProcess(
            stdout=b"second\n",
            stderr=b"",
            returncode=0,
            release_event=second_release,
        )

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    async def scenario() -> None:
        first_adapter = FakeAdapter(tool_name="fake-tool", max_concurrent_adapters=1)
        second_adapter = FakeAdapter(tool_name="fake-tool", max_concurrent_adapters=1)

        first_task = asyncio.create_task(first_adapter.execute("first"))
        await asyncio.sleep(0)
        second_task = asyncio.create_task(second_adapter.execute("second"))
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert spawn_order == ["first"]
        assert second_started.is_set() is False

        first_release.set()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert spawn_order == ["first", "second"]

        second_release.set()
        first_result, second_result = await asyncio.gather(first_task, second_task)
        assert first_result.stdout_clean == "first"
        assert second_result.stdout_clean == "second"

    asyncio.run(scenario())


def test_base_cli_adapter_releases_slot_after_timeout_under_contention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = _adapters_module()
    adapters._ADAPTER_EXECUTION_GUARDS.clear()

    class FakeAdapter(_FakeAdapterMixin, adapters.BaseCLIAdapter):
        pass

    spawn_order: list[str] = []
    second_started = asyncio.Event()
    release_timeout = asyncio.Event()
    wait_for_calls = 0

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        del kwargs
        prompt = command[-1]
        spawn_order.append(prompt)
        if prompt == "second":
            second_started.set()
            return _FakeProcess(stdout=b"second\n", stderr=b"", returncode=0)
        return _FakeProcess(stdout=b"", stderr=b"timed out\n", returncode=-9)

    async def fake_wait_for(awaitable: object, timeout: float) -> tuple[bytes, bytes]:
        nonlocal wait_for_calls
        del timeout
        wait_for_calls += 1
        if wait_for_calls == 1:
            await release_timeout.wait()
            awaitable.close()
            raise TimeoutError
        return await awaitable

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(adapters.asyncio, "wait_for", fake_wait_for)

    async def scenario() -> None:
        first_adapter = FakeAdapter(
            tool_name="fake-tool",
            timeout_seconds=0.01,
            max_concurrent_adapters=1,
        )
        second_adapter = FakeAdapter(tool_name="fake-tool", max_concurrent_adapters=1)

        first_task = asyncio.create_task(first_adapter.execute("first"))
        await asyncio.sleep(0)
        second_task = asyncio.create_task(second_adapter.execute("second"))
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert spawn_order == ["first"]
        assert second_started.is_set() is False

        release_timeout.set()
        first_result = await first_task
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert first_result.timed_out is True
        assert spawn_order == ["first", "second"]
        assert second_started.is_set() is True

        second_result = await second_task
        assert second_result.stdout_clean == "second"

    asyncio.run(scenario())


def test_base_cli_adapter_shares_guard_across_instances_in_same_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = _adapters_module()
    adapters._ADAPTER_EXECUTION_GUARDS.clear()

    class FakeAdapter(_FakeAdapterMixin, adapters.BaseCLIAdapter):
        pass

    release_event = asyncio.Event()
    max_active = 0
    active = 0

    class _TrackedProcess(_BlockingProcess):
        async def communicate(self) -> tuple[bytes, bytes]:
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            try:
                return await super().communicate()
            finally:
                active -= 1

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        del command, kwargs
        return _TrackedProcess(
            stdout=b"ok\n",
            stderr=b"",
            returncode=0,
            release_event=release_event,
        )

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    async def scenario() -> None:
        first_adapter = FakeAdapter(tool_name="fake-tool", max_concurrent_adapters=1)
        second_adapter = FakeAdapter(tool_name="fake-tool", max_concurrent_adapters=1)

        first_task = asyncio.create_task(first_adapter.execute("first"))
        await asyncio.sleep(0)
        second_task = asyncio.create_task(second_adapter.execute("second"))
        await asyncio.sleep(0)
        release_event.set()
        await asyncio.gather(first_task, second_task)

    asyncio.run(scenario())

    assert max_active == 1


def test_codex_cli_adapter_builds_container_first_exec_command() -> None:
    adapters = _adapters_module()

    adapter = adapters.CodexCLIAdapter()

    command = adapter.build_command("Implement the plan.")

    assert command == [
        "./scripts/dev-codex.sh",
        "--",
        "exec",
        "--color",
        "never",
        "Implement the plan.",
    ]


def test_base_cli_adapter_raises_operational_error_when_launcher_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = _adapters_module()

    class FakeAdapter(_FakeAdapterMixin, adapters.BaseCLIAdapter):
        pass

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        del command, kwargs
        raise FileNotFoundError("missing launcher")

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    with pytest.raises(adapters.AdapterOperationalError, match="launcher") as excinfo:
        asyncio.run(FakeAdapter(tool_name="fake-tool").execute("plan feature"))

    error = excinfo.value
    assert error.tool_name == "fake-tool"
    assert error.reason == "launcher_unavailable"
    assert error.command == ["fake-tool", "--prompt", "plan feature"]


@pytest.mark.parametrize(
    ("result_kwargs", "expected_category", "expected_blocked"),
    [
        (
            {
                "return_code": -9,
                "stderr_clean": "process timed out",
                "timed_out": True,
                "success": False,
            },
            "timeout",
            False,
        ),
        (
            {
                "return_code": 1,
                "stderr_clean": "docker: command not found",
                "timed_out": False,
                "success": False,
            },
            "launcher_unavailable",
            True,
        ),
        (
            {
                "return_code": 1,
                "stderr_clean": "no such service: codex-dev",
                "timed_out": False,
                "success": False,
            },
            "container_unavailable",
            True,
        ),
        (
            {
                "return_code": 23,
                "stderr_clean": (
                    "401 Unauthorized: Missing bearer or basic authentication in header"
                ),
                "timed_out": False,
                "success": False,
            },
            "authentication_unavailable",
            True,
        ),
        (
            {
                "return_code": 2,
                "stderr_clean": "unexpected codex failure",
                "timed_out": False,
                "success": False,
            },
            "return_code_nonzero",
            False,
        ),
    ],
)
def test_classify_codex_execution_result(
    result_kwargs: dict[str, object],
    expected_category: str,
    expected_blocked: bool,
) -> None:
    adapters = _adapters_module()
    contracts = import_module("aignt_os.contracts")

    result = contracts.CLIExecutionResult(
        tool_name="codex",
        command=["./scripts/dev-codex.sh", "--", "exec", "prompt"],
        stdout_raw="",
        stderr_raw=str(result_kwargs["stderr_clean"]),
        stdout_clean="",
        duration_ms=10,
        **result_kwargs,
    )

    assessment = adapters.classify_codex_execution(result)

    assert assessment.category == expected_category
    assert assessment.is_operational_block == expected_blocked


def test_codex_cli_adapter_opens_circuit_breaker_after_two_operational_failures(
    tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    adapters = _adapters_module()
    circuit_breaker_module = import_module("aignt_os.runtime.circuit_breaker")

    monkeypatch.setenv("AIGNT_OS_RUNTIME_STATE_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("AIGNT_OS_ADAPTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "2")
    monkeypatch.setenv("AIGNT_OS_ADAPTER_CIRCUIT_BREAKER_COOLDOWN_SECONDS", "60")

    fake_process = _FakeProcess(
        stdout=b"",
        stderr=b"Cannot connect to the Docker daemon\n",
        returncode=1,
    )

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        del command, kwargs
        return fake_process

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    first_result = asyncio.run(adapters.CodexCLIAdapter().execute("Implement the plan."))
    second_result = asyncio.run(adapters.CodexCLIAdapter().execute("Implement the plan."))
    store = circuit_breaker_module.AdapterCircuitBreakerStore(
        tmp_path / "runtime" / "adapter-circuit-breakers.json"
    )
    state = store.read("codex")

    assert adapters.classify_codex_execution(first_result).category == "launcher_unavailable"
    assert adapters.classify_codex_execution(second_result).category == "launcher_unavailable"
    assert state is not None
    assert state.consecutive_operational_failures == 2
    assert state.cooldown_until is not None
    assert store.is_open("codex") is True


def test_codex_cli_adapter_blocks_without_spawn_when_circuit_is_open(
    tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    adapters = _adapters_module()
    circuit_breaker_module = import_module("aignt_os.runtime.circuit_breaker")

    monkeypatch.setenv("AIGNT_OS_RUNTIME_STATE_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("AIGNT_OS_ADAPTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "2")
    monkeypatch.setenv("AIGNT_OS_ADAPTER_CIRCUIT_BREAKER_COOLDOWN_SECONDS", "60")

    store = circuit_breaker_module.AdapterCircuitBreakerStore(
        tmp_path / "runtime" / "adapter-circuit-breakers.json"
    )
    store.record_operational_failure("codex", threshold=2, cooldown_seconds=60.0, now=10.0)
    store.record_operational_failure("codex", threshold=2, cooldown_seconds=60.0, now=11.0)

    async def fail_if_called(*command: str, **kwargs: object) -> _FakeProcess:
        del command, kwargs
        raise AssertionError("subprocess should not be spawned while circuit is open")

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fail_if_called)
    monkeypatch.setattr(adapters.time, "time", lambda: 12.0)

    result = asyncio.run(adapters.CodexCLIAdapter().execute("Implement the plan."))
    assessment = adapters.classify_codex_execution(result)

    assert result.success is False
    assert assessment.category == "circuit_open"
    assert assessment.is_operational_block is True


def test_codex_cli_adapter_resets_breaker_after_non_operational_probe(
    tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    adapters = _adapters_module()
    circuit_breaker_module = import_module("aignt_os.runtime.circuit_breaker")

    monkeypatch.setenv("AIGNT_OS_RUNTIME_STATE_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("AIGNT_OS_ADAPTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "2")
    monkeypatch.setenv("AIGNT_OS_ADAPTER_CIRCUIT_BREAKER_COOLDOWN_SECONDS", "60")

    store = circuit_breaker_module.AdapterCircuitBreakerStore(
        tmp_path / "runtime" / "adapter-circuit-breakers.json"
    )
    store.record_operational_failure("codex", threshold=2, cooldown_seconds=60.0, now=10.0)
    store.record_operational_failure("codex", threshold=2, cooldown_seconds=60.0, now=11.0)

    fake_process = _FakeProcess(
        stdout=b"",
        stderr=b"unexpected codex failure\n",
        returncode=2,
    )

    async def fake_create_subprocess_exec(*command: str, **kwargs: object) -> _FakeProcess:
        del command, kwargs
        return fake_process

    monkeypatch.setattr(adapters.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(adapters.time, "time", lambda: 72.0)

    result = asyncio.run(adapters.CodexCLIAdapter().execute("Implement the plan."))
    assessment = adapters.classify_codex_execution(result)

    assert assessment.category == "return_code_nonzero"
    assert store.read("codex") is None

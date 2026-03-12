from __future__ import annotations

import json
import os
from importlib import import_module
from pathlib import Path


def test_circuit_breaker_store_reports_closed_when_file_is_missing(tmp_path: Path) -> None:
    module = import_module("aignt_os.runtime.circuit_breaker")

    store = module.AdapterCircuitBreakerStore(tmp_path / "adapter-circuit-breakers.json")

    assert store.read("codex") is None
    assert store.is_open("codex", now=10.0) is False


def test_circuit_breaker_store_persists_atomically_with_restricted_permissions(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    module = import_module("aignt_os.runtime.circuit_breaker")

    state_file = tmp_path / "adapter-circuit-breakers.json"
    store = module.AdapterCircuitBreakerStore(state_file)
    replace_calls: list[tuple[Path, Path]] = []
    original_replace = module.os.replace

    def track_replace(source: Path, destination: Path) -> None:
        replace_calls.append((source, destination))
        original_replace(source, destination)

    monkeypatch.setattr(module.os, "replace", track_replace)

    store.record_operational_failure(
        "codex",
        threshold=2,
        cooldown_seconds=60.0,
        now=10.0,
    )
    store.record_operational_failure(
        "codex",
        threshold=2,
        cooldown_seconds=60.0,
        now=11.0,
    )

    assert replace_calls
    assert replace_calls[-1][1] == state_file
    assert stat_mode(state_file) == 0o600
    assert stat_mode(state_file.parent) == 0o700


def test_circuit_breaker_store_opens_after_threshold_and_resets_on_success(tmp_path: Path) -> None:
    module = import_module("aignt_os.runtime.circuit_breaker")

    store = module.AdapterCircuitBreakerStore(tmp_path / "adapter-circuit-breakers.json")

    first = store.record_operational_failure(
        "codex",
        threshold=2,
        cooldown_seconds=60.0,
        now=10.0,
    )
    second = store.record_operational_failure(
        "codex",
        threshold=2,
        cooldown_seconds=60.0,
        now=11.0,
    )

    assert first.cooldown_until is None
    assert second.cooldown_until == 71.0
    assert store.is_open("codex", now=12.0) is True

    store.reset("codex")

    assert store.read("codex") is None
    assert store.is_open("codex", now=12.0) is False


def test_circuit_breaker_store_treats_expired_cooldown_as_closed(tmp_path: Path) -> None:
    module = import_module("aignt_os.runtime.circuit_breaker")

    state_file = tmp_path / "adapter-circuit-breakers.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(
            {
                "codex": {
                    "tool_name": "codex",
                    "consecutive_operational_failures": 2,
                    "opened_at": 11.0,
                    "cooldown_until": 20.0,
                }
            }
        ),
        encoding="utf-8",
    )

    store = module.AdapterCircuitBreakerStore(state_file)

    assert store.is_open("codex", now=21.0) is False


def stat_mode(path: Path) -> int:
    return os.stat(path).st_mode & 0o777

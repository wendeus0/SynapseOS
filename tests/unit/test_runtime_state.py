from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path

import pytest


def test_runtime_state_store_persists_minimum_runtime_metadata(tmp_path: Path) -> None:
    state_module = import_module("aignt_os.runtime.state")

    store = state_module.RuntimeStateStore(tmp_path / "runtime-state.json")
    store.write_running(pid=12345)

    persisted = store.read()

    assert persisted.status == "running"
    assert persisted.pid == 12345
    assert persisted.started_at


def test_runtime_state_store_reports_stopped_when_state_file_is_missing(tmp_path: Path) -> None:
    state_module = import_module("aignt_os.runtime.state")

    store = state_module.RuntimeStateStore(tmp_path / "runtime-state.json")

    persisted = store.read()

    assert persisted.status == "stopped"
    assert persisted.pid is None


def test_runtime_state_store_reports_inconsistent_for_corrupted_state_file(
    tmp_path: Path,
) -> None:
    state_module = import_module("aignt_os.runtime.state")

    state_file = tmp_path / "runtime-state.json"
    state_file.write_text("{invalid json", encoding="utf-8")

    store = state_module.RuntimeStateStore(state_file)
    persisted = store.read()

    assert persisted.status == "inconsistent"
    assert persisted.pid is None


def test_runtime_state_store_reports_inconsistent_for_nonexistent_pid(tmp_path: Path) -> None:
    state_module = import_module("aignt_os.runtime.state")

    store = state_module.RuntimeStateStore(tmp_path / "runtime-state.json")
    store.write_running(pid=999_999_999)

    persisted = store.read()

    assert persisted.status == "inconsistent"


def test_runtime_state_store_writes_state_file_with_restricted_permissions(
    tmp_path: Path,
) -> None:
    state_module = import_module("aignt_os.runtime.state")

    state_file = tmp_path / "runtime-state.json"
    store = state_module.RuntimeStateStore(state_file)
    store.write_running(pid=12345)

    assert stat_mode(state_file) == 0o600
    assert stat_mode(state_file.parent) == 0o700


def test_runtime_state_store_persists_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_module = import_module("aignt_os.runtime.state")

    state_file = tmp_path / "runtime-state.json"
    store = state_module.RuntimeStateStore(state_file)
    replace_calls: list[tuple[Path, Path]] = []
    original_replace = state_module.os.replace

    def track_replace(source: Path, destination: Path) -> None:
        replace_calls.append((source, destination))
        original_replace(source, destination)

    monkeypatch.setattr(state_module.os, "replace", track_replace)

    store.write_running(pid=12345)

    assert replace_calls
    assert replace_calls[-1][1] == state_file


def test_runtime_state_store_rejects_untrusted_state_directory(tmp_path: Path) -> None:
    state_module = import_module("aignt_os.runtime.state")

    untrusted_dir = tmp_path / ".." / "outside-runtime"

    with pytest.raises(ValueError):
        state_module.RuntimeStateStore(untrusted_dir / "runtime-state.json")


def stat_mode(path: Path) -> int:
    return os.stat(path).st_mode & 0o777

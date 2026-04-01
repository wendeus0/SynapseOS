from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from synapse_os.workspace import (
    WorkspaceState,
    TrackedWorkspace,
    WorkspacePool,
    WorkspaceManager,
    PoolExhaustedError,
)


class TestWorkspaceState:
    def test_all_states_documented(self):
        assert WorkspaceState.CREATING.value == "creating"
        assert WorkspaceState.READY.value == "ready"
        assert WorkspaceState.BUSY.value == "busy"
        assert WorkspaceState.CLEANUP.value == "cleanup"
        assert WorkspaceState.DESTROYED.value == "destroyed"


class TestTrackedWorkspace:
    def test_create_with_defaults(self, tmp_path: Path):
        ws = TrackedWorkspace(root=tmp_path)
        assert ws.root == tmp_path
        assert ws.state == WorkspaceState.CREATING
        assert ws.run_id is None
        assert ws.metadata == {}

    def test_mark_ready(self, tmp_path: Path):
        ws = TrackedWorkspace(root=tmp_path)
        ws.mark_ready(run_id="run-1")
        assert ws.state == WorkspaceState.READY
        assert ws.run_id == "run-1"

    def test_mark_busy(self, tmp_path: Path):
        ws = TrackedWorkspace(root=tmp_path, state=WorkspaceState.READY)
        ws.mark_busy()
        assert ws.state == WorkspaceState.BUSY

    def test_mark_cleanup(self, tmp_path: Path):
        ws = TrackedWorkspace(root=tmp_path)
        ws.mark_cleanup()
        assert ws.state == WorkspaceState.CLEANUP

    def test_mark_destroyed(self, tmp_path: Path):
        ws = TrackedWorkspace(root=tmp_path)
        ws.mark_destroyed()
        assert ws.state == WorkspaceState.DESTROYED

    def test_reset_for_reuse(self, tmp_path: Path):
        ws = TrackedWorkspace(root=tmp_path, run_id="run-1", state=WorkspaceState.BUSY)
        ws.reset_for_reuse()
        assert ws.state == WorkspaceState.CREATING
        assert ws.run_id is None
        assert ws.metadata == {}

    def test_metadata_get_set(self, tmp_path: Path):
        ws = TrackedWorkspace(root=tmp_path)
        ws.set_metadata("key", "value")
        assert ws.get_metadata("key") == "value"
        assert ws.get_metadata("missing") is None


class TestWorkspacePool:
    def test_create_pool(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=3)
        assert pool.max_size == 3
        assert pool.acquired_count == 0

    def test_acquire_returns_tracked_workspace(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=2)
        ws = pool.acquire("run-1")
        assert isinstance(ws, TrackedWorkspace)
        assert ws.run_id == "run-1"
        assert ws.state == WorkspaceState.READY
        assert pool.acquired_count == 1

    def test_acquire_creates_directory(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=1)
        ws = pool.acquire("run-1")
        assert ws.root.exists()

    def test_acquire_exhausted_raises(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=1)
        pool.acquire("run-1")
        with pytest.raises(PoolExhaustedError):
            pool.acquire("run-2")

    def test_release_returns_to_pool(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=1)
        ws = pool.acquire("run-1")
        pool.release(ws)
        assert pool.acquired_count == 0
        assert pool.idle_count == 1

    def test_release_resets_workspace(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=1)
        ws = pool.acquire("run-1")
        ws.set_metadata("key", "value")
        pool.release(ws)
        assert ws.run_id is None
        assert ws.state == WorkspaceState.READY

    def test_idle_workspaces_tracked(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=2)
        ws1 = pool.acquire("run-1")
        ws2 = pool.acquire("run-2")
        pool.release(ws1)
        assert pool.idle_count == 1
        assert ws1 in pool.idle_workspaces

    def test_discard_removes_from_pool(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=1)
        ws = pool.acquire("run-1")
        pool.discard(ws)
        assert pool.acquired_count == 0
        assert pool.idle_count == 0

    def test_discard_cleans_directory(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=1)
        ws = pool.acquire("run-1")
        (ws.root / "file.txt").write_text("data")
        pool.discard(ws)
        assert not ws.root.exists()

    def test_stats(self, tmp_path: Path):
        pool = WorkspacePool(base_dir=tmp_path, max_size=3)
        ws1 = pool.acquire("run-1")
        ws2 = pool.acquire("run-2")
        pool.release(ws1)
        stats = pool.stats()
        assert stats["total"] == 3
        assert stats["acquired"] == 1
        assert stats["idle"] == 1
        assert stats["discarded"] == 1


class TestWorkspaceManager:
    def test_create_workspace(self, tmp_path: Path):
        mgr = WorkspaceManager(base_dir=tmp_path, pool_size=2)
        ws = mgr.create_workspace("run-1")
        assert isinstance(ws, TrackedWorkspace)
        assert ws.run_id == "run-1"
        assert ws.state == WorkspaceState.READY

    def test_cleanup_workspace_calls_hook(self, tmp_path: Path):
        mgr = WorkspaceManager(base_dir=tmp_path, pool_size=1)
        hook_called = []
        mgr.register_cleanup_hook(lambda path: hook_called.append(path))
        ws = mgr.create_workspace("run-1")
        mgr.cleanup_workspace(ws)
        assert len(hook_called) == 1
        assert hook_called[0] == ws.root

    def test_cleanup_sets_state_to_cleanup(self, tmp_path: Path):
        mgr = WorkspaceManager(base_dir=tmp_path, pool_size=1)
        ws = mgr.create_workspace("run-1")
        mgr.cleanup_workspace(ws)
        assert ws.state == WorkspaceState.CLEANUP

    def test_get_workspace_returns_cached(self, tmp_path: Path):
        mgr = WorkspaceManager(base_dir=tmp_path, pool_size=1)
        ws1 = mgr.create_workspace("run-1")
        ws2 = mgr.get_workspace("run-1")
        assert ws1 is ws2

    def test_get_workspace_unknown_returns_none(self, tmp_path: Path):
        mgr = WorkspaceManager(base_dir=tmp_path, pool_size=1)
        assert mgr.get_workspace("unknown") is None

    def test_list_workspaces(self, tmp_path: Path):
        mgr = WorkspaceManager(base_dir=tmp_path, pool_size=2)
        mgr.create_workspace("run-1")
        mgr.create_workspace("run-2")
        workspaces = mgr.list_workspaces()
        assert len(workspaces) == 2

    def test_pool_size_respected(self, tmp_path: Path):
        mgr = WorkspaceManager(base_dir=tmp_path, pool_size=2)
        for i in range(1, 4):
            try:
                mgr.create_workspace(f"run-{i}")
            except PoolExhaustedError:
                pass
        assert len(mgr.list_workspaces()) == 2

    def test_cleanup_all(self, tmp_path: Path):
        mgr = WorkspaceManager(base_dir=tmp_path, pool_size=2)
        mgr.create_workspace("run-1")
        mgr.create_workspace("run-2")
        called = []
        mgr.register_cleanup_hook(lambda p: called.append(p))
        mgr.cleanup_all()
        assert len(called) == 2

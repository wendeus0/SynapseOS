from __future__ import annotations

import shutil
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class WorkspaceState(StrEnum):
    CREATING = "creating"
    READY = "ready"
    BUSY = "busy"
    CLEANUP = "cleanup"
    DESTROYED = "destroyed"


class TrackedWorkspace(BaseModel):
    root: Path
    state: WorkspaceState = WorkspaceState.CREATING
    run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def mark_ready(self, run_id: str) -> None:
        self.state = WorkspaceState.READY
        self.run_id = run_id

    def mark_busy(self) -> None:
        self.state = WorkspaceState.BUSY

    def mark_cleanup(self) -> None:
        self.state = WorkspaceState.CLEANUP

    def mark_destroyed(self) -> None:
        self.state = WorkspaceState.DESTROYED

    def reset_for_reuse(self) -> None:
        self.state = WorkspaceState.CREATING
        self.run_id = None
        self.metadata = {}
        for item in self.root.iterdir():
            if item.name != self.root.name:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)


class PoolExhaustedError(Exception):
    pass


class WorkspacePool(BaseModel):
    base_dir: Path
    max_size: int
    acquired_count: int = 0
    idle_workspaces: list[TrackedWorkspace] = Field(default_factory=list)
    workspace_counter: int = Field(default=0)

    def acquire(self, run_id: str) -> TrackedWorkspace:
        if self.acquired_count >= self.max_size and not self.idle_workspaces:
            raise PoolExhaustedError(f"Pool exhausted: {self.max_size}/{self.max_size}")
        self.workspace_counter += 1
        ws_root = self.base_dir / f"ws-{self.workspace_counter}"
        ws_root.mkdir(parents=True, exist_ok=True)
        ws = TrackedWorkspace(root=ws_root)
        ws.mark_ready(run_id)
        self.acquired_count += 1
        return ws

    def release(self, ws: TrackedWorkspace) -> None:
        ws.reset_for_reuse()
        ws.state = WorkspaceState.READY
        self.idle_workspaces.append(ws)
        self.acquired_count -= 1

    def discard(self, ws: TrackedWorkspace) -> None:
        if ws in self.idle_workspaces:
            self.idle_workspaces.remove(ws)
        if ws.root.exists():
            shutil.rmtree(ws.root)
        ws.mark_destroyed()
        self.acquired_count -= 1

    @property
    def idle_count(self) -> int:
        return len(self.idle_workspaces)

    def stats(self) -> dict[str, int]:
        return {
            "total": self.max_size,
            "acquired": self.acquired_count,
            "idle": self.idle_count,
            "discarded": self.max_size - self.acquired_count - self.idle_count,
        }


class WorkspaceManager:
    def __init__(self, base_dir: Path, pool_size: int) -> None:
        self.base_dir = base_dir
        self.pool = WorkspacePool(base_dir=base_dir / ".workspace_pool", max_size=pool_size)
        self._cache: dict[str, TrackedWorkspace] = {}
        self._cleanup_hooks: list[Callable[[Path], None]] = []

    def create_workspace(self, run_id: str) -> TrackedWorkspace:
        ws = self.pool.acquire(run_id)
        self._cache[run_id] = ws
        return ws

    def register_cleanup_hook(self, hook: Callable[[Path], None]) -> None:
        self._cleanup_hooks.append(hook)

    def cleanup_workspace(self, ws: TrackedWorkspace) -> None:
        ws.mark_cleanup()
        for hook in self._cleanup_hooks:
            hook(ws.root)

    def get_workspace(self, run_id: str) -> TrackedWorkspace | None:
        return self._cache.get(run_id)

    def list_workspaces(self) -> list[TrackedWorkspace]:
        return list(self._cache.values())

    def cleanup_all(self) -> None:
        for ws in list(self._cache.values()):
            self.cleanup_workspace(ws)

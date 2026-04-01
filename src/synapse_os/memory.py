from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field, StrictStr


class ArtifactMetadata(BaseModel):
    model_config = ConfigDict(strict=True)

    type: StrictStr = Field(default="unknown")
    tags: list[StrictStr] = Field(default_factory=list)
    source_step: StrictStr | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ArtifactIndexEntry(BaseModel):
    name: StrictStr
    run_id: StrictStr
    metadata: ArtifactMetadata


class IndexedArtifactStore:
    def __init__(self, *, base_path: Path) -> None:
        self.base_path = base_path
        self._lock = Lock()
        self._index: dict[str, list[ArtifactIndexEntry]] = defaultdict(list)

    def register(
        self,
        *,
        run_id: str,
        name: str,
        metadata: ArtifactMetadata | None = None,
    ) -> None:
        with self._lock:
            entry = ArtifactIndexEntry(
                name=name,
                run_id=run_id,
                metadata=metadata or ArtifactMetadata(type="unknown"),
            )
            self._index[run_id].append(entry)

    def find_by_tag(self, tag: str) -> list[ArtifactIndexEntry]:
        with self._lock:
            return [
                entry
                for entries in self._index.values()
                for entry in entries
                if tag in entry.metadata.tags
            ]

    def find_by_type(self, artifact_type: str) -> list[ArtifactIndexEntry]:
        with self._lock:
            return [
                entry
                for entries in self._index.values()
                for entry in entries
                if entry.metadata.type == artifact_type
            ]

    def list_for_run(self, run_id: str) -> list[ArtifactIndexEntry]:
        with self._lock:
            return list(self._index.get(run_id, []))


class MemoryStore:
    def __init__(self, *, state_dir: Path) -> None:
        self.state_dir = state_dir
        self._lock = Lock()
        self._memory_path = state_dir / "memory-store.json"
        self._memory: dict[str, dict[str, str]] = self._load()

    def _load(self) -> dict[str, dict[str, str]]:
        if not self._memory_path.exists():
            return defaultdict(dict)
        try:
            data = json.loads(self._memory_path.read_text(encoding="utf-8"))
            return defaultdict(dict, data)
        except Exception:
            return defaultdict(dict)

    def _persist(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._memory_path.write_text(
            json.dumps(dict(self._memory), ensure_ascii=False),
            encoding="utf-8",
        )

    def get(self, namespace: str, key: str) -> str | None:
        with self._lock:
            return self._memory.get(namespace, {}).get(key)

    def set(self, namespace: str, key: str, value: str) -> None:
        with self._lock:
            self._memory[namespace][key] = value
            self._persist()

    def delete(self, namespace: str, key: str) -> None:
        with self._lock:
            if namespace in self._memory and key in self._memory[namespace]:
                del self._memory[namespace][key]
                self._persist()

    def list_namespaces(self) -> list[str]:
        with self._lock:
            return list(self._memory.keys())

    def feature_memory(self, feature_id: str) -> FeatureMemoryView:
        return FeatureMemoryView(store=self, namespace=feature_id)


class FeatureMemoryView:
    def __init__(self, store: MemoryStore, namespace: str) -> None:
        self._store = store
        self._namespace = namespace

    def get(self, key: str) -> str | None:
        return self._store.get(self._namespace, key)

    def set(self, key: str, value: str) -> None:
        self._store.set(self._namespace, key, value)

    def delete(self, key: str) -> None:
        self._store.delete(self._namespace, key)

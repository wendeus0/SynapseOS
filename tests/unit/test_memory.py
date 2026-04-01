from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from synapse_os.memory import (
    ArtifactMetadata,
    FeatureMemoryView,
    IndexedArtifactStore,
    MemoryStore,
)


class TestArtifactMetadata:
    def test_defaults(self) -> None:
        meta = ArtifactMetadata(type="test_report", source_step="TEST_RED")
        assert meta.type == "test_report"
        assert meta.tags == []
        assert meta.source_step == "TEST_RED"
        assert meta.created_at is not None

    def test_full(self) -> None:
        now = datetime.now(timezone.utc)
        meta = ArtifactMetadata(
            type="log",
            tags=["error", "crash"],
            source_step="CODE_GREEN",
            created_at=now,
        )
        assert meta.type == "log"
        assert meta.tags == ["error", "crash"]
        assert meta.created_at == now


class TestIndexedArtifactStore:
    def test_register_and_find_by_tag(self, tmp_path: Path) -> None:
        store = IndexedArtifactStore(base_path=tmp_path)
        store.register(
            run_id="run-1",
            name="error.log",
            metadata=ArtifactMetadata(type="log", tags=["error"], source_step="RUN"),
        )
        results = store.find_by_tag("error")
        assert len(results) == 1
        assert results[0].name == "error.log"

    def test_find_by_tag_no_match(self, tmp_path: Path) -> None:
        store = IndexedArtifactStore(base_path=tmp_path)
        store.register(
            run_id="run-1",
            name="output.txt",
            metadata=ArtifactMetadata(type="text", tags=["output"], source_step="RUN"),
        )
        assert store.find_by_tag("error") == []

    def test_find_by_type(self, tmp_path: Path) -> None:
        store = IndexedArtifactStore(base_path=tmp_path)
        store.register(
            run_id="run-1",
            name="report.txt",
            metadata=ArtifactMetadata(type="test_report", source_step="RUN"),
        )
        results = store.find_by_type("test_report")
        assert len(results) == 1
        assert results[0].name == "report.txt"

    def test_list_for_run(self, tmp_path: Path) -> None:
        store = IndexedArtifactStore(base_path=tmp_path)
        store.register(
            run_id="run-1",
            name="a.txt",
            metadata=ArtifactMetadata(type="text", source_step="RUN"),
        )
        store.register(
            run_id="run-1",
            name="b.txt",
            metadata=ArtifactMetadata(type="text", source_step="RUN"),
        )
        store.register(
            run_id="run-2",
            name="c.txt",
            metadata=ArtifactMetadata(type="text", source_step="RUN"),
        )
        run1_artifacts = store.list_for_run("run-1")
        assert len(run1_artifacts) == 2

    def test_multiple_tags(self, tmp_path: Path) -> None:
        store = IndexedArtifactStore(base_path=tmp_path)
        store.register(
            run_id="run-1",
            name="log.txt",
            metadata=ArtifactMetadata(
                type="log", tags=["error", "crash"], source_step="RUN"
            ),
        )
        assert len(store.find_by_tag("error")) == 1
        assert len(store.find_by_tag("crash")) == 1


class TestMemoryStore:
    def test_set_and_get(self, tmp_path: Path) -> None:
        store = MemoryStore(state_dir=tmp_path)
        store.set("ns", "key", "value")
        assert store.get("ns", "key") == "value"

    def test_get_missing(self, tmp_path: Path) -> None:
        store = MemoryStore(state_dir=tmp_path)
        assert store.get("ns", "missing") is None

    def test_delete(self, tmp_path: Path) -> None:
        store = MemoryStore(state_dir=tmp_path)
        store.set("ns", "key", "value")
        store.delete("ns", "key")
        assert store.get("ns", "key") is None

    def test_list_namespaces(self, tmp_path: Path) -> None:
        store = MemoryStore(state_dir=tmp_path)
        store.set("ns1", "k", "v")
        store.set("ns2", "k", "v")
        namespaces = store.list_namespaces()
        assert set(namespaces) == {"ns1", "ns2"}

    def test_persistence(self, tmp_path: Path) -> None:
        store = MemoryStore(state_dir=tmp_path)
        store.set("ns", "key", "value")
        store2 = MemoryStore(state_dir=tmp_path)
        assert store2.get("ns", "key") == "value"

    def test_feature_memory_view(self, tmp_path: Path) -> None:
        store = MemoryStore(state_dir=tmp_path)
        fm = store.feature_memory("F59")
        fm.set("decision", "use-dag")
        assert store.get("F59", "decision") == "use-dag"
        assert fm.get("decision") == "use-dag"

    def test_feature_memory_isolation(self, tmp_path: Path) -> None:
        store = MemoryStore(state_dir=tmp_path)
        store.set("F59", "key", "f59-value")
        store.set("F60", "key", "f60-value")
        fm59 = store.feature_memory("F59")
        fm60 = store.feature_memory("F60")
        assert fm59.get("key") == "f59-value"
        assert fm60.get("key") == "f60-value"

    def test_feature_memory_delete(self, tmp_path: Path) -> None:
        store = MemoryStore(state_dir=tmp_path)
        store.set("F59", "key", "value")
        fm = store.feature_memory("F59")
        fm.delete("key")
        assert store.get("F59", "key") is None

from __future__ import annotations

import sqlite3
from importlib import import_module
from pathlib import Path

import pytest


def test_run_repository_persists_run_lifecycle(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    run_id = repository.create_run(
        spec_path=tmp_path / "SPEC.md",
        workspace_path=tmp_path / "workspaces" / "run-123",
        initial_state="REQUEST",
        stop_at="PLAN",
        spec_hash="abc123",
        initiated_by="local_cli",
    )

    assert repository.acquire_lock(run_id) is True

    repository.mark_run_running(run_id, current_state="SPEC_VALIDATION")
    repository.mark_run_completed(run_id, current_state="PLAN")

    run_record = repository.get_run(run_id)

    assert run_record.run_id == run_id
    assert run_record.status == "completed"
    assert run_record.current_state == "PLAN"
    assert run_record.locked is False
    assert run_record.spec_hash == "abc123"
    assert run_record.initiated_by == "local_cli"
    assert run_record.workspace_path == str(tmp_path / "workspaces" / "run-123")
    assert run_record.completed_at is not None


def test_run_repository_prevents_double_lock_for_same_run(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    run_id = repository.create_run(
        spec_path=tmp_path / "SPEC.md",
        workspace_path=tmp_path / "workspaces" / "run-123",
        initial_state="REQUEST",
        stop_at="PLAN",
        spec_hash="hash-1",
        initiated_by="system",
    )

    assert repository.acquire_lock(run_id) is True
    assert repository.acquire_lock(run_id) is False


def test_artifact_store_saves_raw_clean_and_named_artifacts(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")

    store = persistence.ArtifactStore(tmp_path / "artifacts")

    saved_outputs = store.save_step_outputs(
        run_id="run-123",
        step_state="PLAN",
        raw_output="RAW Bearer secret-token \u202eＦ\n",
        clean_output="clean Bearer secret-token e\u0301 \u202eＦ",
    )
    artifact_path = store.save_named_artifact(
        run_id="run-123",
        step_state="PLAN",
        artifact_name="../plan_md",
        content="# Plan\nsk-secret123\n",
    )
    report_path = store.save_run_report(
        run_id="run-123",
        content="# RUN_REPORT\nBearer secret-token\n",
    )

    assert saved_outputs.raw_path is not None
    assert saved_outputs.clean_path is not None
    assert (
        saved_outputs.raw_path.read_text(encoding="utf-8") == "RAW Bearer secret-token \u202eＦ\n"
    )
    clean_content = saved_outputs.clean_path.read_text(encoding="utf-8")
    assert "Bearer secret-token" not in clean_content
    assert "[REDACTED]" in clean_content
    assert "é" in clean_content
    assert "\u202e" not in clean_content
    assert "F" in clean_content
    artifact_content = artifact_path.read_text(encoding="utf-8")
    assert "sk-secret123" not in artifact_content
    assert "[REDACTED]" in artifact_content
    assert "Bearer secret-token" not in report_path.read_text(encoding="utf-8")
    assert artifact_path.name == "plan_md.txt"


def test_run_repository_records_step_execution_metadata(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    run_id = repository.create_run(
        spec_path=tmp_path / "SPEC.md",
        workspace_path=tmp_path / "workspaces" / "run-123",
        initial_state="REQUEST",
        stop_at="DOCUMENT",
        spec_hash="hash-2",
        initiated_by="system",
    )

    repository.record_step(
        run_id,
        state="PLAN",
        status="completed",
        tool_name="codex",
        return_code=0,
        duration_ms=45,
        timed_out=False,
    )

    steps = repository.list_steps(run_id)

    assert len(steps) == 1
    assert steps[0].tool_name == "codex"
    assert steps[0].return_code == 0
    assert steps[0].duration_ms == 45
    assert steps[0].timed_out is False


def test_run_repository_upgrades_legacy_schema_with_provenance_columns(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")

    database_path = tmp_path / "runs.sqlite3"
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE runs (
                run_id TEXT PRIMARY KEY,
                spec_path TEXT NOT NULL,
                stop_at TEXT NOT NULL,
                status TEXT NOT NULL,
                current_state TEXT NOT NULL,
                locked BOOLEAN NOT NULL,
                failure_message TEXT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO runs (
                run_id,
                spec_path,
                stop_at,
                status,
                current_state,
                locked,
                failure_message,
                created_at,
                updated_at,
                completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-run",
                str(tmp_path / "SPEC.md"),
                "SPEC_VALIDATION",
                "completed",
                "SPEC_VALIDATION",
                0,
                None,
                "2026-03-12T00:00:00+00:00",
                "2026-03-12T00:01:00+00:00",
                "2026-03-12T00:02:00+00:00",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    repository = persistence.RunRepository(database_path)
    run_record = repository.get_run("legacy-run")

    schema_columns = {
        row[1]: row[4]
        for row in sqlite3.connect(database_path).execute("PRAGMA table_info(runs)").fetchall()
    }

    assert "spec_hash" in schema_columns
    assert "initiated_by" in schema_columns
    assert "workspace_path" in schema_columns
    assert run_record.spec_hash is None
    assert run_record.initiated_by == "unknown"
    assert run_record.workspace_path == str(tmp_path)


def test_artifact_store_blocks_unsafe_python_named_artifact(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    parsing = import_module("synapse_os.parsing")

    store = persistence.ArtifactStore(tmp_path / "artifacts")

    with pytest.raises(parsing.ParsingArtifactError, match="unsafe"):
        store.save_named_artifact(
            run_id="run-123",
            step_state="CODE_GREEN",
            artifact_name="code_py",
            content='eval("danger")\n',
        )

    assert not (tmp_path / "artifacts" / "run-123" / "CODE_GREEN" / "code_py.txt").exists()

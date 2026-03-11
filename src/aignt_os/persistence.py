from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    insert,
    select,
)
from sqlalchemy.engine import RowMapping
from sqlalchemy.sql import update

from aignt_os.pipeline import (
    PipelineContext,
    PipelineEngine,
    PipelineObserver,
    PipelineStep,
    StepExecutionResult,
    StepExecutor,
)

ARTIFACT_DIR_MODE = 0o700
ARTIFACT_FILE_MODE = 0o600
_SAFE_SEGMENT_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True, slots=True)
class RunRecord:
    run_id: str
    spec_path: str
    stop_at: str
    status: str
    current_state: str
    locked: bool
    failure_message: str | None
    created_at: str
    updated_at: str
    completed_at: str | None


@dataclass(frozen=True, slots=True)
class RunStepRecord:
    step_id: int
    run_id: str
    state: str
    status: str
    raw_output_path: str | None
    clean_output_path: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class RunEventRecord:
    event_id: int
    run_id: str
    state: str
    event_type: str
    message: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SavedStepOutputs:
    raw_path: Path | None
    clean_path: Path | None


class RunRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite+pysqlite:///{self.database_path}")
        self.metadata = MetaData()
        self.runs = Table(
            "runs",
            self.metadata,
            Column("run_id", String, primary_key=True),
            Column("spec_path", Text, nullable=False),
            Column("stop_at", String, nullable=False),
            Column("status", String, nullable=False),
            Column("current_state", String, nullable=False),
            Column("locked", Boolean, nullable=False),
            Column("failure_message", Text, nullable=True),
            Column("created_at", String, nullable=False),
            Column("updated_at", String, nullable=False),
            Column("completed_at", String, nullable=True),
        )
        self.run_steps = Table(
            "run_steps",
            self.metadata,
            Column("step_id", Integer, primary_key=True, autoincrement=True),
            Column("run_id", String, nullable=False),
            Column("state", String, nullable=False),
            Column("status", String, nullable=False),
            Column("raw_output_path", Text, nullable=True),
            Column("clean_output_path", Text, nullable=True),
            Column("created_at", String, nullable=False),
        )
        self.run_events = Table(
            "run_events",
            self.metadata,
            Column("event_id", Integer, primary_key=True, autoincrement=True),
            Column("run_id", String, nullable=False),
            Column("state", String, nullable=False),
            Column("event_type", String, nullable=False),
            Column("message", Text, nullable=False),
            Column("created_at", String, nullable=False),
        )
        self.metadata.create_all(self.engine)

    def create_run(self, *, spec_path: Path, initial_state: str, stop_at: str) -> str:
        run_id = uuid4().hex
        timestamp = _timestamp()
        with self.engine.begin() as connection:
            connection.execute(
                insert(self.runs).values(
                    run_id=run_id,
                    spec_path=str(spec_path),
                    stop_at=stop_at,
                    status="pending",
                    current_state=initial_state,
                    locked=False,
                    failure_message=None,
                    created_at=timestamp,
                    updated_at=timestamp,
                    completed_at=None,
                )
            )
        return run_id

    def acquire_lock(self, run_id: str) -> bool:
        timestamp = _timestamp()
        with self.engine.begin() as connection:
            result = connection.execute(
                update(self.runs)
                .where(self.runs.c.run_id == run_id, self.runs.c.locked.is_(False))
                .values(locked=True, updated_at=timestamp)
            )
        return result.rowcount == 1

    def mark_run_running(self, run_id: str, *, current_state: str) -> None:
        self._update_run(
            run_id,
            status="running",
            current_state=current_state,
            updated_at=_timestamp(),
        )

    def mark_run_completed(self, run_id: str, *, current_state: str) -> None:
        timestamp = _timestamp()
        self._update_run(
            run_id,
            status="completed",
            current_state=current_state,
            locked=False,
            updated_at=timestamp,
            completed_at=timestamp,
        )

    def mark_run_failed(self, run_id: str, *, current_state: str, failure_message: str) -> None:
        timestamp = _timestamp()
        self._update_run(
            run_id,
            status="failed",
            current_state=current_state,
            locked=False,
            failure_message=failure_message,
            updated_at=timestamp,
            completed_at=timestamp,
        )

    def record_step(
        self,
        run_id: str,
        *,
        state: str,
        status: str,
        raw_output_path: Path | None = None,
        clean_output_path: Path | None = None,
    ) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                insert(self.run_steps).values(
                    run_id=run_id,
                    state=state,
                    status=status,
                    raw_output_path=str(raw_output_path) if raw_output_path is not None else None,
                    clean_output_path=(
                        str(clean_output_path) if clean_output_path is not None else None
                    ),
                    created_at=_timestamp(),
                )
            )

    def record_event(self, run_id: str, *, state: str, event_type: str, message: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                insert(self.run_events).values(
                    run_id=run_id,
                    state=state,
                    event_type=event_type,
                    message=message,
                    created_at=_timestamp(),
                )
            )

    def get_run(self, run_id: str) -> RunRecord:
        with self.engine.begin() as connection:
            row = (
                connection.execute(select(self.runs).where(self.runs.c.run_id == run_id))
                .mappings()
                .one()
            )
        return _run_record_from_row(row)

    def list_runs(self) -> list[RunRecord]:
        with self.engine.begin() as connection:
            rows = connection.execute(select(self.runs).order_by(self.runs.c.created_at)).mappings()
            return [_run_record_from_row(row) for row in rows]

    def find_next_pending_run(self) -> RunRecord | None:
        with self.engine.begin() as connection:
            row = (
                connection.execute(
                    select(self.runs)
                    .where(
                        self.runs.c.status == "pending",
                        self.runs.c.locked.is_(False),
                    )
                    .order_by(self.runs.c.created_at)
                    .limit(1)
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return _run_record_from_row(row)

    def list_steps(self, run_id: str) -> list[RunStepRecord]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                select(self.run_steps)
                .where(self.run_steps.c.run_id == run_id)
                .order_by(self.run_steps.c.step_id)
            ).mappings()
            return [_step_record_from_row(row) for row in rows]

    def list_events(self, run_id: str) -> list[RunEventRecord]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                select(self.run_events)
                .where(self.run_events.c.run_id == run_id)
                .order_by(self.run_events.c.event_id)
            ).mappings()
            return [_event_record_from_row(row) for row in rows]

    def _update_run(self, run_id: str, **values: object) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                update(self.runs).where(self.runs.c.run_id == run_id).values(**values)
            )


class ArtifactStore:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        _ensure_private_directory(self.base_path)

    def save_step_outputs(
        self,
        *,
        run_id: str,
        step_state: str,
        raw_output: str | None,
        clean_output: str | None,
    ) -> SavedStepOutputs:
        step_directory = self._step_directory(run_id, step_state)
        raw_path = None
        clean_path = None

        if raw_output is not None:
            raw_path = step_directory / "raw.txt"
            _write_private_text(raw_path, raw_output)

        if clean_output is not None:
            clean_path = step_directory / "clean.txt"
            _write_private_text(clean_path, clean_output)

        return SavedStepOutputs(raw_path=raw_path, clean_path=clean_path)

    def save_named_artifact(
        self,
        *,
        run_id: str,
        step_state: str,
        artifact_name: str,
        content: str,
    ) -> Path:
        step_directory = self._step_directory(run_id, step_state)
        safe_name = _safe_segment(artifact_name, fallback="artifact")
        artifact_path = step_directory / f"{safe_name}.txt"
        _write_private_text(artifact_path, content)
        return artifact_path

    def _step_directory(self, run_id: str, step_state: str) -> Path:
        run_directory = self.base_path / _safe_segment(run_id, fallback="run")
        step_directory = run_directory / _safe_segment(step_state, fallback="step")
        _ensure_private_directory(step_directory)
        return step_directory


class PipelinePersistenceObserver(PipelineObserver):
    def __init__(self, repository: RunRepository, artifact_store: ArtifactStore) -> None:
        self.repository = repository
        self.artifact_store = artifact_store

    def on_run_started(self, context: PipelineContext) -> None:
        run_id = self._run_id(context)
        self.repository.mark_run_running(run_id, current_state=context.current_state)
        self.repository.record_event(
            run_id,
            state=context.current_state,
            event_type="run_started",
            message=f"Run started at {context.current_state}.",
        )

    def on_step_completed(
        self,
        step: PipelineStep,
        context: PipelineContext,
        result: StepExecutionResult | None,
    ) -> None:
        run_id = self._run_id(context)
        saved_outputs = self.artifact_store.save_step_outputs(
            run_id=run_id,
            step_state=step.state,
            raw_output=None if result is None else result.raw_output,
            clean_output=None if result is None else result.clean_output,
        )
        self.repository.record_step(
            run_id,
            state=step.state,
            status="completed",
            raw_output_path=saved_outputs.raw_path,
            clean_output_path=saved_outputs.clean_path,
        )

        artifacts = self._artifacts_for_step(step, context, result)
        for artifact_name, artifact_content in artifacts.items():
            self.artifact_store.save_named_artifact(
                run_id=run_id,
                step_state=step.state,
                artifact_name=artifact_name,
                content=artifact_content,
            )

        self.repository.record_event(
            run_id,
            state=step.state,
            event_type="step_completed",
            message=f"Step {step.state} completed.",
        )

    def on_run_completed(self, context: PipelineContext) -> None:
        run_id = self._run_id(context)
        self.repository.mark_run_completed(run_id, current_state=context.current_state)
        self.repository.record_event(
            run_id,
            state=context.current_state,
            event_type="run_completed",
            message=f"Run completed at {context.current_state}.",
        )

    def on_run_failed(
        self,
        context: PipelineContext,
        step: PipelineStep | None,
        error: Exception,
    ) -> None:
        run_id = self._run_id(context)
        state = context.current_state if step is None else step.state
        self.repository.mark_run_failed(run_id, current_state=state, failure_message=str(error))
        self.repository.record_event(
            run_id,
            state=state,
            event_type="run_failed",
            message=str(error),
        )

    def _run_id(self, context: PipelineContext) -> str:
        if context.run_id is None:
            raise ValueError("Pipeline context is missing run_id for persistence.")
        return context.run_id

    def _artifacts_for_step(
        self,
        step: PipelineStep,
        context: PipelineContext,
        result: StepExecutionResult | None,
    ) -> dict[str, str]:
        if result is not None:
            return dict(result.artifacts)

        if step.state == "SPEC_VALIDATION":
            return {
                key: value
                for key, value in context.artifacts.items()
                if key in {"spec_id", "spec_summary"}
            }

        return {}


class PersistedPipelineRunner:
    def __init__(
        self,
        *,
        repository: RunRepository,
        artifact_store: ArtifactStore,
        executors: dict[str, StepExecutor] | None = None,
    ) -> None:
        self.repository = repository
        self.artifact_store = artifact_store
        self.executors = dict(executors or {})

    def create_pending_run(self, spec_path: Path, *, stop_at: str = "TEST_RED") -> str:
        return self.repository.create_run(
            spec_path=spec_path,
            initial_state="REQUEST",
            stop_at=stop_at,
        )

    def run(self, spec_path: Path, *, stop_at: str = "TEST_RED") -> PipelineContext:
        run_id = self.create_pending_run(spec_path, stop_at=stop_at)
        return self.run_existing(run_id)

    def run_existing(self, run_id: str, *, assume_locked: bool = False) -> PipelineContext:
        run_record = self.repository.get_run(run_id)
        if not assume_locked and not self.repository.acquire_lock(run_id):
            raise RuntimeError(f"Could not acquire lock for run '{run_id}'.")

        engine = PipelineEngine(
            executors=self.executors,
            observer=PipelinePersistenceObserver(self.repository, self.artifact_store),
        )
        return engine.run(
            Path(run_record.spec_path),
            stop_at=run_record.stop_at,
            run_id=run_id,
        )


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=ARTIFACT_DIR_MODE)
    os.chmod(path, ARTIFACT_DIR_MODE)


def _write_private_text(path: Path, content: str) -> None:
    _ensure_private_directory(path.parent)
    path.write_text(content, encoding="utf-8")
    os.chmod(path, ARTIFACT_FILE_MODE)


def _safe_segment(value: str, *, fallback: str) -> str:
    sanitized = _SAFE_SEGMENT_PATTERN.sub("_", value).strip("._-")
    if not sanitized:
        return fallback
    return sanitized


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _run_record_from_row(row: RowMapping) -> RunRecord:
    return RunRecord(
        run_id=_string_value(row, "run_id"),
        spec_path=_string_value(row, "spec_path"),
        stop_at=_string_value(row, "stop_at"),
        status=_string_value(row, "status"),
        current_state=_string_value(row, "current_state"),
        locked=_bool_value(row, "locked"),
        failure_message=_optional_string_value(row, "failure_message"),
        created_at=_string_value(row, "created_at"),
        updated_at=_string_value(row, "updated_at"),
        completed_at=_optional_string_value(row, "completed_at"),
    )


def _step_record_from_row(row: RowMapping) -> RunStepRecord:
    return RunStepRecord(
        step_id=_int_value(row, "step_id"),
        run_id=_string_value(row, "run_id"),
        state=_string_value(row, "state"),
        status=_string_value(row, "status"),
        raw_output_path=_optional_string_value(row, "raw_output_path"),
        clean_output_path=_optional_string_value(row, "clean_output_path"),
        created_at=_string_value(row, "created_at"),
    )


def _event_record_from_row(row: RowMapping) -> RunEventRecord:
    return RunEventRecord(
        event_id=_int_value(row, "event_id"),
        run_id=_string_value(row, "run_id"),
        state=_string_value(row, "state"),
        event_type=_string_value(row, "event_type"),
        message=_string_value(row, "message"),
        created_at=_string_value(row, "created_at"),
    )


def _string_value(row: RowMapping, key: str) -> str:
    value = row[key]
    if not isinstance(value, str):
        raise TypeError(f"Expected '{key}' to be a string.")
    return value


def _optional_string_value(row: RowMapping, key: str) -> str | None:
    value = row[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"Expected '{key}' to be a string or None.")
    return value


def _int_value(row: RowMapping, key: str) -> int:
    value = row[key]
    if not isinstance(value, int):
        raise TypeError(f"Expected '{key}' to be an integer.")
    return value


def _bool_value(row: RowMapping, key: str) -> bool:
    value = row[key]
    if not isinstance(value, bool):
        raise TypeError(f"Expected '{key}' to be a boolean.")
    return value

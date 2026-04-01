from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import StrEnum
from threading import Lock
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictStr


class DAGSpecificationError(ValueError):
    pass


class DAGStepStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class DAGStep(BaseModel):
    model_config = ConfigDict(strict=True)

    id: StrictStr = Field(min_length=1)
    executor: StrictStr = Field(min_length=1)
    depends_on: list[StrictStr] = Field(default_factory=list)
    if_cond: StrictStr | None = None


class DAGConditional(BaseModel):
    model_config = ConfigDict(strict=True)

    id: StrictStr = Field(min_length=1)
    step: StrictStr
    if_cond: StrictStr


class DAGSpec(BaseModel):
    model_config = ConfigDict(strict=True)

    mode: StrictStr = Field(default="linear")
    steps: list[DAGStep] = Field(default_factory=list)
    conditionals: list[DAGConditional] = Field(default_factory=list)


class DAGValidator:
    @staticmethod
    def validate(spec: DAGSpec) -> None:
        if spec.mode == "linear":
            return
        if spec.mode == "dag":
            DAGValidator._validate_dag(spec)
        else:
            raise DAGSpecificationError(f"Unknown DAG mode: {spec.mode!r}. Use 'linear' or 'dag'.")

    @staticmethod
    def _validate_dag(spec: DAGSpec) -> None:
        if not spec.steps:
            raise DAGSpecificationError("DAG mode requires at least one step.")

        step_ids = {step.id for step in spec.steps}
        for step in spec.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise DAGSpecificationError(
                        f"Step '{step.id}' depends on non-existent step '{dep}'."
                    )
        DAGValidator._check_no_cycle(spec)

    @staticmethod
    def _check_no_cycle(spec: DAGSpec) -> None:
        in_degree: dict[str, int] = {step.id: 0 for step in spec.steps}
        adj: dict[str, list[str]] = {step.id: [] for step in spec.steps}

        for step in spec.steps:
            for dep in step.depends_on:
                in_degree[step.id] += 1
                adj[dep].append(step.id)

        queue: list[str] = [sid for sid, deg in in_degree.items() if deg == 0]
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited != len(spec.steps):
            raise DAGSpecificationError("Cycle detected in DAG graph.")


@dataclass
class DAGContext:
    spec: DAGSpec
    _states: dict[str, DAGStepStatus] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def __post_init__(self) -> None:
        for step in self.spec.steps:
            self._states[step.id] = DAGStepStatus.PENDING

    def get_state(self, step_id: str) -> DAGStepStatus:
        return self._states[step_id]

    def mark_running(self, step_id: str) -> None:
        with self._lock:
            self._states[step_id] = DAGStepStatus.RUNNING

    def mark_done(self, step_id: str) -> None:
        with self._lock:
            self._states[step_id] = DAGStepStatus.DONE

    def mark_failed(self, step_id: str) -> None:
        with self._lock:
            self._states[step_id] = DAGStepStatus.FAILED

    def ready_steps(self) -> list[str]:
        ready: list[str] = []
        for step in self.spec.steps:
            if self._states[step.id] != DAGStepStatus.PENDING:
                continue
            deps_done = all(self._states[dep] == DAGStepStatus.DONE for dep in step.depends_on)
            if deps_done:
                ready.append(step.id)
        return ready

    def is_complete(self) -> bool:
        return all(
            self._states[sid] in (DAGStepStatus.DONE, DAGStepStatus.FAILED) for sid in self._states
        )

    @property
    def has_failed(self) -> bool:
        return any(self._states[sid] == DAGStepStatus.FAILED for sid in self._states)


class DAGExecutor:
    def __init__(
        self,
        spec: DAGSpec,
        *,
        max_workers: int = 4,
        step_runner: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.spec = spec
        self.max_workers = max_workers
        self.step_runner = step_runner or (lambda _sid, _ctx: None)
        if spec.mode == "dag":
            DAGValidator.validate(spec)
        self.context = DAGContext(spec)

    def execute(self) -> None:
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures: dict[str, Any] = {}
            while not self.context.is_complete():
                if self.context.has_failed:
                    break

                completed = [fid for fid, f in futures.items() if f.done()]
                for fid in completed:
                    f = futures.pop(fid)
                    try:
                        f.result()
                    except Exception:
                        pass

                ready = self.context.ready_steps()
                if not ready:
                    if not futures:
                        break
                    import time as _time

                    _time.sleep(0.01)
                    continue

                for step_id in ready:
                    if step_id in futures and not futures[step_id].done():
                        continue
                    self.context.mark_running(step_id)
                    future = pool.submit(self._run_step, step_id)
                    futures[step_id] = future

    def _run_step(self, step_id: str) -> None:
        try:
            self.step_runner(step_id, {})
            self.context.mark_done(step_id)
        except Exception:
            self.context.mark_failed(step_id)
            raise


class LinearPipelineAdapter:
    def __init__(
        self,
        steps: list[str],
        step_runner: Callable[[str, dict[str, Any]], None],
    ) -> None:
        self.steps = steps
        self.step_runner = step_runner

    def execute(self) -> None:
        if not self.steps:
            raise DAGSpecificationError("Linear pipeline requires at least one step.")
        for step_id in self.steps:
            self.step_runner(step_id, {})

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest

from synapse_os.pipeline_dag import (
    DAGConditional,
    DAGContext,
    DAGExecutor,
    DAGSpecificationError,
    DAGSpec,
    DAGStep,
    DAGValidator,
    LinearPipelineAdapter,
)


class TestDAGSpec:
    def test_valid_linear_mode(self) -> None:
        spec = DAGSpec(mode="linear")
        assert spec.mode == "linear"
        assert spec.steps == []
        assert spec.conditionals == []

    def test_valid_dag_mode_empty_steps(self) -> None:
        spec = DAGSpec(mode="dag", steps=[])
        assert spec.mode == "dag"
        assert spec.steps == []

    def test_valid_dag_step_full(self) -> None:
        step = DAGStep(id="build", executor="codex", depends_on=[], if_cond=None)
        spec = DAGSpec(mode="dag", steps=[step])
        assert spec.steps[0].id == "build"

    def test_dag_step_minimal(self) -> None:
        step = DAGStep(id="build", executor="codex")
        assert step.depends_on == []
        assert step.if_cond is None


class TestDAGValidator:
    def test_valid_linear_no_error(self) -> None:
        spec = DAGSpec(mode="linear")
        DAGValidator.validate(spec)

    def test_valid_dag_single_step(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[DAGStep(id="build", executor="codex", depends_on=[])],
        )
        DAGValidator.validate(spec)

    def test_valid_dag_linear_chain(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=["a"]),
                DAGStep(id="c", executor="codex", depends_on=["b"]),
            ],
        )
        DAGValidator.validate(spec)

    def test_valid_dag_fan_out(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="root", executor="codex", depends_on=[]),
                DAGStep(id="a", executor="codex", depends_on=["root"]),
                DAGStep(id="b", executor="codex", depends_on=["root"]),
                DAGStep(id="c", executor="codex", depends_on=["root"]),
            ],
        )
        DAGValidator.validate(spec)

    def test_valid_dag_fan_in(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=[]),
                DAGStep(id="c", executor="codex", depends_on=["a", "b"]),
            ],
        )
        DAGValidator.validate(spec)

    def test_valid_dag_complex(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="root", executor="codex", depends_on=[]),
                DAGStep(id="a", executor="codex", depends_on=["root"]),
                DAGStep(id="b", executor="codex", depends_on=["root"]),
                DAGStep(id="c", executor="codex", depends_on=["a", "b"]),
            ],
        )
        DAGValidator.validate(spec)

    def test_cycle_detection_self_loop(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[DAGStep(id="a", executor="codex", depends_on=["a"])],
        )
        with pytest.raises(DAGSpecificationError, match="(?i)cycle"):
            DAGValidator.validate(spec)

    def test_cycle_detection_two_node(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=["b"]),
                DAGStep(id="b", executor="codex", depends_on=["a"]),
            ],
        )
        with pytest.raises(DAGSpecificationError, match="(?i)cycle"):
            DAGValidator.validate(spec)

    def test_cycle_detection_three_node(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=["b"]),
                DAGStep(id="b", executor="codex", depends_on=["c"]),
                DAGStep(id="c", executor="codex", depends_on=["a"]),
            ],
        )
        with pytest.raises(DAGSpecificationError, match="(?i)cycle"):
            DAGValidator.validate(spec)

    def test_missing_dependency_raises(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[DAGStep(id="a", executor="codex", depends_on=["nonexistent"])],
        )
        with pytest.raises(DAGSpecificationError, match="nonexistent"):
            DAGValidator.validate(spec)

    def test_empty_steps_raises(self) -> None:
        spec = DAGSpec(mode="dag", steps=[])
        with pytest.raises(DAGSpecificationError, match="at least one step"):
            DAGValidator.validate(spec)


class TestDAGContext:
    def test_initial_state_all_pending(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=["a"]),
            ],
        )
        ctx = DAGContext(spec)
        assert ctx.get_state("a") == "PENDING"
        assert ctx.get_state("b") == "PENDING"

    def test_mark_running(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[DAGStep(id="a", executor="codex", depends_on=[])],
        )
        ctx = DAGContext(spec)
        ctx.mark_running("a")
        assert ctx.get_state("a") == "RUNNING"

    def test_mark_done(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[DAGStep(id="a", executor="codex", depends_on=[])],
        )
        ctx = DAGContext(spec)
        ctx.mark_done("a")
        assert ctx.get_state("a") == "DONE"

    def test_mark_failed(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[DAGStep(id="a", executor="codex", depends_on=[])],
        )
        ctx = DAGContext(spec)
        ctx.mark_failed("a")
        assert ctx.get_state("a") == "FAILED"

    def test_ready_steps_root(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=["a"]),
            ],
        )
        ctx = DAGContext(spec)
        ready = ctx.ready_steps()
        assert ready == ["a"]

    def test_ready_steps_after_root_done(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=["a"]),
            ],
        )
        ctx = DAGContext(spec)
        ctx.mark_done("a")
        ready = ctx.ready_steps()
        assert ready == ["b"]

    def test_ready_steps_fan_in_both_deps_done(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=[]),
                DAGStep(id="c", executor="codex", depends_on=["a", "b"]),
            ],
        )
        ctx = DAGContext(spec)
        assert set(ctx.ready_steps()) == {"a", "b"}
        ctx.mark_done("a")
        assert ctx.ready_steps() == ["b"]
        ctx.mark_done("b")
        assert ctx.ready_steps() == ["c"]

    def test_is_complete_all_done(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=["a"]),
            ],
        )
        ctx = DAGContext(spec)
        assert not ctx.is_complete()
        ctx.mark_done("a")
        assert not ctx.is_complete()
        ctx.mark_done("b")
        assert ctx.is_complete()

    def test_is_complete_has_failed(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[DAGStep(id="a", executor="codex", depends_on=[])],
        )
        ctx = DAGContext(spec)
        ctx.mark_failed("a")
        assert ctx.is_complete()

    def test_dependency_deduplication(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=["a", "a"]),
            ],
        )
        ctx = DAGContext(spec)
        ctx.mark_done("a")
        assert ctx.ready_steps() == ["b"]


class TestDAGExecutor:
    def test_execute_single_step(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[DAGStep(id="a", executor="codex", depends_on=[])],
        )
        executed: list[str] = []

        def run_step(step_id: str) -> None:
            executed.append(step_id)

        executor = DAGExecutor(
            spec=spec,
            max_workers=4,
            step_runner=lambda sid, _: run_step(sid),
        )
        executor.execute()

        assert executed == ["a"]
        assert executor.context.is_complete()

    def test_execute_linear_chain(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=["a"]),
                DAGStep(id="c", executor="codex", depends_on=["b"]),
            ],
        )
        executed: list[str] = []

        def run_step(step_id: str) -> None:
            executed.append(step_id)

        executor = DAGExecutor(
            spec=spec,
            max_workers=4,
            step_runner=lambda sid, _: run_step(sid),
        )
        executor.execute()

        assert executed == ["a", "b", "c"]
        assert executor.context.is_complete()

    def test_execute_fan_out_parallel(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="froot", executor="codex", depends_on=[]),
                DAGStep(id="fa", executor="codex", depends_on=["froot"]),
                DAGStep(id="fb", executor="codex", depends_on=["froot"]),
                DAGStep(id="fc", executor="codex", depends_on=["froot"]),
            ],
        )
        order: list[str] = []

        def run_step(step_id: str) -> None:
            order.append(step_id)

        executor = DAGExecutor(
            spec=spec,
            max_workers=4,
            step_runner=lambda sid, _: run_step(sid),
        )
        executor.execute()

        assert order[0] == "froot"
        assert set(order[1:]) == {"fa", "fb", "fc"}
        assert executor.context.is_complete()

    def test_execute_fan_in(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="fa", executor="codex", depends_on=[]),
                DAGStep(id="fb", executor="codex", depends_on=[]),
                DAGStep(id="fc", executor="codex", depends_on=["fa", "fb"]),
            ],
        )
        done: dict[str, bool] = {}

        def run_step(step_id: str) -> None:
            done[step_id] = True

        executor = DAGExecutor(
            spec=spec,
            max_workers=4,
            step_runner=lambda sid, _: run_step(sid),
        )
        executor.execute()

        assert done.get("fa") and done.get("fb") and done.get("fc")
        assert executor.context.is_complete()

    def test_execute_stops_on_failure(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id="a", executor="codex", depends_on=[]),
                DAGStep(id="b", executor="codex", depends_on=["a"]),
            ],
        )

        def run_step(step_id: str) -> None:
            if step_id == "a":
                raise RuntimeError("simulated failure")

        executor = DAGExecutor(
            spec=spec,
            max_workers=4,
            step_runner=lambda sid, _: run_step(sid),
        )
        executor.execute()

        assert executor.context.get_state("a") == "FAILED"
        assert executor.context.has_failed

    def test_max_workers_limits_concurrency(self) -> None:
        spec = DAGSpec(
            mode="dag",
            steps=[
                DAGStep(id=str(i), executor="codex", depends_on=[]) for i in range(8)
            ],
        )
        concurrent = []

        def run_step(step_id: str) -> None:
            concurrent.append(1)
            import time

            time.sleep(0.05)

        executor = DAGExecutor(
            spec=spec,
            max_workers=2,
            step_runner=lambda sid, _: run_step(sid),
        )
        executor.execute()

        assert (
            max(sum(concurrent[i : i + 2]) for i in range(0, len(concurrent), 2)) <= 2
        )


class TestLinearPipelineAdapter:
    def test_runs_linear_sequence(self) -> None:
        executed: list[str] = []
        adapter = LinearPipelineAdapter(
            steps=["a", "b", "c"],
            step_runner=lambda sid, _: executed.append(sid),
        )
        adapter.execute()
        assert executed == ["a", "b", "c"]

    def test_raises_on_empty_steps(self) -> None:
        adapter = LinearPipelineAdapter(
            steps=[],
            step_runner=lambda _, __: None,
        )
        with pytest.raises(DAGSpecificationError, match="at least one step"):
            adapter.execute()

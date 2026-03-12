from __future__ import annotations

from importlib import import_module
from pathlib import Path


def _runs_env(tmp_path: Path) -> dict[str, str]:
    return {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNS_DB_PATH": str(tmp_path / "runs.sqlite3"),
        "AIGNT_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
    }


def _seed_run(tmp_path: Path, *, status: str, current_state: str) -> str:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / f"{status}-{current_state}.md"
    spec_path.write_text("# Fixture\n", encoding="utf-8")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="DOCUMENT",
    )

    if status == "running":
        repository.acquire_lock(run_id)
        repository.mark_run_running(run_id, current_state=current_state)
    elif status == "completed":
        repository.acquire_lock(run_id)
        repository.mark_run_running(run_id, current_state="PLAN")
        repository.mark_run_completed(run_id, current_state=current_state)
    elif status == "failed":
        repository.acquire_lock(run_id)
        repository.mark_run_running(run_id, current_state="PLAN")
        repository.mark_run_failed(
            run_id,
            current_state=current_state,
            failure_message="fixture failure",
        )

    return run_id


def test_runs_list_reports_persisted_runs(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    first_run_id = _seed_run(tmp_path, status="completed", current_state="DOCUMENT")
    second_run_id = _seed_run(tmp_path, status="running", current_state="CODE_GREEN")

    result = cli_runner.invoke(cli_app, ["runs", "list"], env=_runs_env(tmp_path))

    assert result.exit_code == 0
    assert "run id" in result.stdout.lower()
    assert first_run_id in result.stdout
    assert second_run_id in result.stdout
    assert "completed" in result.stdout.lower()
    assert "running" in result.stdout.lower()
    assert "document" in result.stdout.lower()
    assert "code_green" in result.stdout.lower()


def test_runs_show_reports_run_metadata_steps_events_and_artifacts(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    env = _runs_env(tmp_path)
    repository = persistence.RunRepository(Path(env["AIGNT_OS_RUNS_DB_PATH"]))
    artifact_store = persistence.ArtifactStore(Path(env["AIGNT_OS_ARTIFACTS_DIR"]))
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("# Fixture\n", encoding="utf-8")

    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="DOCUMENT",
    )
    repository.acquire_lock(run_id)
    repository.mark_run_running(run_id, current_state="CODE_GREEN")
    saved_outputs = artifact_store.save_step_outputs(
        run_id=run_id,
        step_state="PLAN",
        raw_output="RAW PLAN\n",
        clean_output="# Plan\n",
    )
    artifact_store.save_named_artifact(
        run_id=run_id,
        step_state="PLAN",
        artifact_name="plan_md",
        content="# Plan\n",
    )
    artifact_store.save_run_report(run_id=run_id, content="# RUN_REPORT\n")
    repository.record_step(
        run_id,
        state="PLAN",
        status="completed",
        raw_output_path=saved_outputs.raw_path,
        clean_output_path=saved_outputs.clean_path,
        tool_name="codex",
        return_code=0,
        duration_ms=45,
        timed_out=False,
    )
    repository.record_event(
        run_id,
        state="PLAN",
        event_type="step_completed",
        message="Step PLAN completed.",
    )
    repository.mark_run_completed(run_id, current_state="DOCUMENT")

    result = cli_runner.invoke(cli_app, ["runs", "show", run_id], env=env)

    assert result.exit_code == 0
    assert run_id in result.stdout
    assert "diagnostic summary" in result.stdout.lower()
    assert "latest signal" in result.stdout.lower()
    assert "step_completed @ PLAN" in result.stdout
    assert "latest timestamp" in result.stdout.lower()
    assert "spec path" in result.stdout.lower()
    assert str(spec_path) in result.stdout
    assert "completed" in result.stdout.lower()
    assert "document" in result.stdout.lower()
    assert "next action" in result.stdout.lower()
    assert "inspect generated artifacts or report" in result.stdout.lower()
    assert "steps" in result.stdout.lower()
    assert "plan" in result.stdout.lower()
    assert "codex" in result.stdout.lower()
    assert f"{run_id}/PLAN/raw.txt" in result.stdout
    assert f"{run_id}/PLAN/clean.txt" in result.stdout
    assert "events" in result.stdout.lower()
    assert "step_completed" in result.stdout
    assert "created at" in result.stdout.lower()
    assert "artifacts" in result.stdout.lower()
    assert f"{run_id}/PLAN/plan_md.txt" in result.stdout
    assert f"{run_id}/RUN_REPORT.md" in result.stdout


def test_runs_show_reports_failure_diagnostic_summary(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    env = _runs_env(tmp_path)
    repository = persistence.RunRepository(Path(env["AIGNT_OS_RUNS_DB_PATH"]))
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("# Fixture\n", encoding="utf-8")

    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="DOCUMENT",
    )
    repository.acquire_lock(run_id)
    repository.mark_run_running(run_id, current_state="CODE_GREEN")
    repository.record_event(
        run_id,
        state="CODE_GREEN",
        event_type="supervisor_decision",
        message="Supervisor requested fail after review rejection.",
    )
    repository.mark_run_failed(
        run_id,
        current_state="CODE_GREEN",
        failure_message="review rejection persisted",
    )

    result = cli_runner.invoke(cli_app, ["runs", "show", run_id], env=env)

    assert result.exit_code == 0
    assert "diagnostic summary" in result.stdout.lower()
    assert "failed" in result.stdout.lower()
    assert "supervisor_decision @ CODE_GREEN" in result.stdout
    assert "review rejection persisted" in result.stdout
    assert "inspect failure details and latest step outputs" in result.stdout.lower()
    assert "no persisted steps" in result.stdout.lower()
    assert "supervisor_decision" in result.stdout
    assert "created at" in result.stdout.lower()


def test_runs_show_fails_predictably_when_run_is_missing(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    result = cli_runner.invoke(cli_app, ["runs", "show", "missing-run"], env=_runs_env(tmp_path))

    assert result.exit_code == 3
    assert "missing-run" in result.stdout or "missing-run" in result.stderr
    assert "not found:" in result.stdout.lower() or "not found:" in result.stderr.lower()


def test_runs_show_preview_report_renders_truncated_content_and_source_path(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    env = _runs_env(tmp_path)
    repository = persistence.RunRepository(Path(env["AIGNT_OS_RUNS_DB_PATH"]))
    artifact_store = persistence.ArtifactStore(Path(env["AIGNT_OS_ARTIFACTS_DIR"]))
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("# Fixture\n", encoding="utf-8")

    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="DOCUMENT",
    )
    repository.acquire_lock(run_id)
    repository.mark_run_running(run_id, current_state="DOCUMENT")
    report_content = "\n".join(f"line {index}" for index in range(1, 46)) + "\n"
    artifact_store.save_run_report(run_id=run_id, content=report_content)
    repository.mark_run_completed(run_id, current_state="DOCUMENT")

    result = cli_runner.invoke(cli_app, ["runs", "show", run_id, "--preview", "report"], env=env)

    assert result.exit_code == 0
    assert "artifact preview" in result.stdout.lower()
    assert "report" in result.stdout.lower()
    assert f"{run_id}/RUN_REPORT.md" in result.stdout
    assert "line 1" in result.stdout
    assert "line 40" in result.stdout
    assert "line 41" not in result.stdout
    assert "preview truncated after 40 lines." in result.stdout.lower()


def test_runs_show_preview_clean_output_uses_requested_step_without_raw_content(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    env = _runs_env(tmp_path)
    repository = persistence.RunRepository(Path(env["AIGNT_OS_RUNS_DB_PATH"]))
    artifact_store = persistence.ArtifactStore(Path(env["AIGNT_OS_ARTIFACTS_DIR"]))
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("# Fixture\n", encoding="utf-8")

    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="DOCUMENT",
    )
    repository.acquire_lock(run_id)
    repository.mark_run_running(run_id, current_state="PLAN")
    saved_outputs = artifact_store.save_step_outputs(
        run_id=run_id,
        step_state="PLAN",
        raw_output="RAW SECRET\n",
        clean_output="clean line 1\nclean line 2\n",
    )
    repository.record_step(
        run_id,
        state="PLAN",
        status="completed",
        raw_output_path=saved_outputs.raw_path,
        clean_output_path=saved_outputs.clean_path,
        tool_name="codex",
        return_code=0,
        duration_ms=45,
        timed_out=False,
    )
    repository.mark_run_completed(run_id, current_state="DOCUMENT")

    result = cli_runner.invoke(
        cli_app,
        ["runs", "show", run_id, "--preview", "PLAN.clean"],
        env=env,
    )

    assert result.exit_code == 0
    assert "artifact preview" in result.stdout.lower()
    assert "plan.clean" in result.stdout.lower()
    assert f"{run_id}/PLAN/clean.txt" in result.stdout
    assert "clean line 1" in result.stdout
    assert "clean line 2" in result.stdout
    assert "RAW SECRET" not in result.stdout


def test_runs_show_preview_rejects_invalid_target_with_usage_error(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    env = _runs_env(tmp_path)
    repository = persistence.RunRepository(Path(env["AIGNT_OS_RUNS_DB_PATH"]))
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("# Fixture\n", encoding="utf-8")

    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="DOCUMENT",
    )

    result = cli_runner.invoke(
        cli_app,
        ["runs", "show", run_id, "--preview", "PLAN.raw"],
        env=env,
    )

    assert result.exit_code == 2
    assert "usage error:" in result.stdout.lower() or "usage error:" in result.stderr.lower()


def test_runs_show_preview_returns_not_found_when_requested_artifact_is_missing(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    env = _runs_env(tmp_path)
    repository = persistence.RunRepository(Path(env["AIGNT_OS_RUNS_DB_PATH"]))
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("# Fixture\n", encoding="utf-8")

    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="DOCUMENT",
    )
    repository.acquire_lock(run_id)
    repository.mark_run_running(run_id, current_state="DOCUMENT")
    repository.mark_run_completed(run_id, current_state="DOCUMENT")

    result = cli_runner.invoke(cli_app, ["runs", "show", run_id, "--preview", "report"], env=env)

    assert result.exit_code == 3
    assert "not found:" in result.stdout.lower() or "not found:" in result.stderr.lower()

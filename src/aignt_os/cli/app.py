import os
import secrets
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from sqlalchemy.exc import NoResultFound

from aignt_os import __version__
from aignt_os.cli.rendering import (
    render_run_detail,
    render_run_submission,
    render_runs_list,
    render_runtime_status,
)
from aignt_os.config import AppSettings
from aignt_os.persistence import ArtifactStore, PersistedPipelineRunner, RunRepository
from aignt_os.pipeline import PIPELINE_STOP_STATES
from aignt_os.runtime.dispatch import RunDispatchService
from aignt_os.runtime.service import RuntimeLifecycleError, RuntimeService
from aignt_os.runtime.worker import build_runtime_worker
from aignt_os.specs import SpecValidationError

app = typer.Typer(help="AIgnt OS CLI")
runtime_app = typer.Typer(help="Manage the minimal persistent runtime.")
runs_app = typer.Typer(help="Inspect persisted runs and artifacts.")
app.add_typer(runtime_app, name="runtime")
app.add_typer(runs_app, name="runs")


@app.callback()
def main() -> None:
    return None


@app.command()
def version() -> None:
    typer.echo(__version__)


def _runtime_service() -> RuntimeService:
    settings = AppSettings()
    try:
        return RuntimeService(
            settings.runtime_state_file,
            worker=build_runtime_worker(settings),
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


def _run_repository() -> RunRepository:
    settings = AppSettings()
    return RunRepository(settings.runs_db_path)


def _artifact_store() -> ArtifactStore:
    settings = AppSettings()
    return ArtifactStore(settings.artifacts_dir)


def _dispatch_service() -> RunDispatchService:
    settings = AppSettings()
    repository = RunRepository(settings.runs_db_path)
    artifact_store = ArtifactStore(settings.artifacts_dir)
    runner = PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    runtime_service = RuntimeService(settings.runtime_state_file)
    return RunDispatchService(
        repository=repository,
        runner=runner,
        is_runtime_ready=runtime_service.ready,
    )


@runtime_app.command("start")
def runtime_start() -> None:
    service = _runtime_service()
    try:
        state = service.start()
    except RuntimeLifecycleError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Runtime status: {state.status} (pid={state.pid})")


@runtime_app.command("status")
def runtime_status() -> None:
    service = _runtime_service()
    state = service.status()

    if state.status == "inconsistent":
        render_runtime_status(state, console=Console(stderr=True))
        raise typer.Exit(code=1)

    render_runtime_status(state)


@runtime_app.command("run")
def runtime_run(
    process_identity: Annotated[
        str | None,
        typer.Option("--process-identity", hidden=True),
    ] = None,
) -> None:
    if process_identity is None:
        os.execvpe(
            sys.executable,
            [
                sys.executable,
                "-c",
                "from aignt_os.cli.app import app; app()",
                "runtime",
                "run",
                "--process-identity",
                secrets.token_hex(16),
            ],
            os.environ.copy(),
        )

    service = _runtime_service()
    try:
        service.run_foreground(process_identity)
    except RuntimeLifecycleError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@runtime_app.command("ready")
def runtime_ready() -> None:
    service = _runtime_service()
    if service.ready():
        typer.echo("Runtime ready")
        return

    typer.echo("Runtime not ready", err=True)
    raise typer.Exit(code=1)


@runtime_app.command("stop")
def runtime_stop() -> None:
    service = _runtime_service()
    try:
        state = service.stop()
    except RuntimeLifecycleError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Runtime status: {state.status}")


@runs_app.command("list")
def runs_list() -> None:
    repository = _run_repository()
    runs = repository.list_runs()
    render_runs_list(runs)


def _validate_mode(mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in {"auto", "sync", "async"}:
        raise typer.BadParameter("mode must be one of: auto, sync, async.")
    return normalized


def _validate_stop_at(stop_at: str) -> str:
    normalized = stop_at.strip().upper()
    if normalized not in PIPELINE_STOP_STATES:
        raise typer.BadParameter("stop-at must be one of: " + ", ".join(PIPELINE_STOP_STATES) + ".")
    return normalized


@runs_app.command("submit")
def runs_submit(
    spec_path: Path,
    mode: Annotated[str, typer.Option("--mode")] = "auto",
    stop_at: Annotated[str, typer.Option("--stop-at")] = "SPEC_VALIDATION",
) -> None:
    dispatch_service = _dispatch_service()

    try:
        result = dispatch_service.dispatch(
            spec_path,
            mode=_validate_mode(mode),  # type: ignore[arg-type]
            stop_at=_validate_stop_at(stop_at),
        )
    except (FileNotFoundError, SpecValidationError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    render_run_submission(result)


@runs_app.command("show")
def runs_show(run_id: str) -> None:
    repository = _run_repository()
    artifact_store = _artifact_store()

    try:
        run = repository.get_run(run_id)
    except NoResultFound as exc:
        typer.echo(f"Run '{run_id}' not found.", err=True)
        raise typer.Exit(code=1) from exc

    render_run_detail(
        run,
        steps=repository.list_steps(run_id),
        events=repository.list_events(run_id),
        artifact_paths=artifact_store.list_artifact_paths(run_id),
    )

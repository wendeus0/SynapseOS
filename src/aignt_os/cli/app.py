import os
import secrets
import sys
from typing import Annotated

import typer
from rich.console import Console

from aignt_os import __version__
from aignt_os.cli.rendering import render_runtime_status
from aignt_os.config import AppSettings
from aignt_os.runtime.service import RuntimeLifecycleError, RuntimeService
from aignt_os.runtime.worker import build_runtime_worker

app = typer.Typer(help="AIgnt OS CLI")
runtime_app = typer.Typer(help="Manage the minimal persistent runtime.")
app.add_typer(runtime_app, name="runtime")


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

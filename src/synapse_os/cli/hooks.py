from __future__ import annotations

import importlib
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from synapse_os.config import AppSettings
from synapse_os.hooks import HookDispatcher
from synapse_os.runtime_contracts import HookConfig
from synapse_os.specs import validate_spec_file

hooks_app = typer.Typer(help="Manage and validate pipeline hooks.")

console = Console()


def _render_hooks_table(hooks: list[HookConfig], title: str) -> None:
    if not hooks:
        console.print(f"[dim]{title}: no hooks configured[/dim]")
        return

    table = Table(title=title)
    table.add_column("Point", style="cyan")
    table.add_column("Handler", style="green")
    table.add_column("Failure Mode", style="yellow")
    table.add_column("Enabled", style="magenta")

    for hook in hooks:
        table.add_row(
            hook.point,
            hook.handler,
            hook.failure_mode,
            str(hook.enabled),
        )

    console.print(table)


@hooks_app.command("list")
def hooks_list(
    spec: Annotated[
        Path | None,
        typer.Option("--spec", help="Path to SPEC.md to show per-run hooks"),
    ] = None,
) -> None:
    settings = AppSettings()
    global_hooks = settings.hooks

    if spec is not None:
        try:
            doc = validate_spec_file(spec)
            spec_hooks = doc.metadata.hooks
            spec_name = spec.name
        except Exception as exc:
            console.print(f"[red]Error validating SPEC: {exc}[/red]")
            raise typer.Exit(code=1) from exc
    else:
        spec_hooks = []
        spec_name = None

    if not global_hooks and not spec_hooks:
        console.print("[dim]No hooks configured.[/dim]")
        return

    if global_hooks:
        _render_hooks_table(global_hooks, "Global Hooks (AppSettings)")

    if spec_hooks:
        _render_hooks_table(spec_hooks, f"SPEC Hooks ({spec_name})")


@hooks_app.command("validate")
def hooks_validate(handler: str) -> None:
    if "." not in handler:
        console.print(
            f"[red]Error: '{handler}' is not a valid dotted path (e.g. module.func).[/red]"
        )
        raise typer.Exit(code=1)

    try:
        module_path, func_name = handler.rsplit(".", 1)
    except ValueError:
        console.print(f"[red]Error: '{handler}' is not a valid dotted path.[/red]")
        raise typer.Exit(code=1)

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        console.print(f"[red]Error: Module '{module_path}' not found.[/red]")
        raise typer.Exit(code=1) from None
    except ImportError as exc:
        console.print(f"[red]Error: Cannot import module '{module_path}': {exc}[/red]")
        raise typer.Exit(code=1) from exc

    try:
        func = getattr(module, func_name)
    except AttributeError:
        console.print(
            f"[red]Error: Function '{func_name}' not found in module '{module_path}'.[/red]"
        )
        raise typer.Exit(code=1) from None

    console.print(f"[green]OK: {handler} -> {func.__name__}[/green]")


@hooks_app.command("status")
def hooks_status() -> None:
    console.print("[dim]No active hooks from recent runs.[/dim]")
    console.print(
        "[dim]Run a pipeline with hooks configured to see active hooks.[/dim]"
    )

import typer

from aignt_os import __version__


app = typer.Typer(help="AIgnt OS CLI")


@app.callback()
def main() -> None:
    return None


@app.command()
def version() -> None:
    typer.echo(__version__)

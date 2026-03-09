from importlib import import_module

from typer.testing import CliRunner


runner = CliRunner()


def test_cli_help_returns_success() -> None:
    cli_module = import_module("aignt_os.cli.app")

    result = runner.invoke(cli_module.app, ["--help"])

    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_cli_version_returns_success() -> None:
    cli_module = import_module("aignt_os.cli.app")

    result = runner.invoke(cli_module.app, ["version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


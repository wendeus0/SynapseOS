import sys
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from aignt_os.cli.app import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_runs_watch_command_exists(runner: CliRunner) -> None:
    """O comando 'runs watch' deve existir na CLI."""
    result = runner.invoke(app, ["runs", "watch", "--help"])
    assert result.exit_code == 0
    assert "Monitor a run in real-time" in result.stdout or "watch" in result.stdout


def test_runs_watch_requires_run_id(runner: CliRunner) -> None:
    """O comando 'runs watch' deve falhar se não fornecer o ID da run."""
    result = runner.invoke(app, ["runs", "watch"])
    assert result.exit_code != 0
    # Typer geralmente coloca "Missing argument" no stdout misturado ou em stderr
    # dependendo da versão
    # Garantimos checando ambos
    assert (
        "Missing argument" in result.stdout or "Missing argument" in result.stderr
    )


@patch.dict("sys.modules", {"aignt_os.cli.dashboard": MagicMock()})
def test_runs_watch_invokes_tui(runner: CliRunner) -> None:
    """O comando deve instanciar e rodar o Dashboard TUI."""
    # Recupera o módulo mockado
    mock_dashboard_module = sys.modules["aignt_os.cli.dashboard"]
    mock_dashboard_cls = mock_dashboard_module.RunDashboard
    mock_app_instance = MagicMock()
    mock_dashboard_cls.return_value = mock_app_instance
    
    # Precisamos mockar _run_repository que é chamado dentro de watch
    # Como _run_repository está no mesmo módulo (app), mockamos ele lá.
    with patch("aignt_os.cli.app._run_repository") as mock_repo_factory:
        mock_repo = MagicMock()
        mock_repo_factory.return_value = mock_repo
        # Simula run existente (retorna algo truthy)
        mock_repo.get_run.return_value = {"id": "test-run-id"}
        
        result = runner.invoke(app, ["runs", "watch", "test-run-id"])
    
    # Debug output se falhar
    if result.exit_code != 0:
        print(result.stdout)
        print(result.exception)
        
    assert result.exit_code == 0
    mock_dashboard_cls.assert_called_once_with(run_id="test-run-id", refresh_interval=1.0)
    mock_app_instance.run.assert_called_once()


def test_runs_watch_handles_missing_run(runner: CliRunner) -> None:
    """O comando deve falhar se a run não existir."""
    # Como o import de dashboard acontece antes da validação da run no código (agora),
    # precisamos mockar o dashboard também para evitar efeitos colaterais ou erros de import
    # se o ambiente de teste não tiver dependências de TUI instaladas (embora tenhamos adicionado).
    # Mas o erro de run not found acontece depois do import.
    
    # Vamos mockar o repository para lançar NoResultFound
    with patch("aignt_os.cli.app._run_repository") as mock_repo_factory:
        mock_repo = MagicMock()
        mock_repo_factory.return_value = mock_repo
        
        # Import necessário para side_effect
        from sqlalchemy.exc import NoResultFound
        mock_repo.get_run.side_effect = NoResultFound()
        
        # Mock dashboard para evitar erro de import/instanciação se o código chegar lá (não deveria)
        with patch.dict("sys.modules", {"aignt_os.cli.dashboard": MagicMock()}):
             result = runner.invoke(app, ["runs", "watch", "non-existent-id"])
    
    assert result.exit_code != 0
    # Verifica em stdout ou stderr
    error_msg = "Error: Run non-existent-id not found."
    assert error_msg in result.stdout or error_msg in result.stderr

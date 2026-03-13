from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from aignt_os.cli.app import app

runner = CliRunner()


def test_runs_follow_command_help():
    """Test that the command exists and has help."""
    result = runner.invoke(app, ["runs", "follow", "--help"])
    assert result.exit_code == 0
    assert "Follow the logs of a run" in result.stdout


def test_runs_follow_command_logic():
    """Test the basic logic of runs follow."""
    # We need to mock RunRepository and ArtifactStore
    # This is complex because we need to mock internal instances in runs_follow
    # Ideally, we refactor runs_follow to accept dependencies, but it's a Typer command.
    # So we patch RunRepository and ArtifactStore.

    with patch("aignt_os.cli.app.RunRepository") as MockRepo:
        mock_repo = MockRepo.return_value

        # Mock run
        mock_run = MagicMock()
        mock_run.status = "running"
        mock_repo.get_run.return_value = mock_run

        # Mock steps
        step1 = MagicMock()
        step1.step_id = 1
        step1.state = "TEST_RED"
        step1.clean_output_path = "/tmp/clean.txt"
        step1.raw_output_path = "/tmp/raw.txt"

        # Scenario:
        # 1. get_run -> running
        # 2. list_steps -> [step1]
        # 3. Process step1 -> print header -> read file
        # 4. Loop again -> get_run -> completed -> break

        mock_repo.list_steps.side_effect = [[step1], [step1]]
        mock_repo.get_run.side_effect = [mock_run, MagicMock(status="completed")]

        with patch("aignt_os.cli.app.AppSettings") as MockSettings:
            mock_settings = MockSettings.return_value
            mock_settings.auth_enabled = False

            with patch("aignt_os.cli.app.ArtifactStore"):
                with patch("time.sleep"):  # Skip sleep
                    result = runner.invoke(
                        app,
                        ["runs", "follow", "run-123", "--poll-interval", "0.01"],
                    )

    assert result.exit_code == 0
    assert "Following logs for run run-123" in result.stdout
    assert "Step 1: TEST_RED" in result.stdout

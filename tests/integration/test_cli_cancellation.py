import pytest
from typer.testing import CliRunner

from aignt_os.cli.app import app
from aignt_os.config import AppSettings
from aignt_os.persistence import RunRepository

runner = CliRunner()


# Fixture to provide a temporary RunRepository
@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "runs.db"
    return RunRepository(db_path)


@pytest.fixture
def app_settings(tmp_path):
    # Ensure app uses tmp_path DB
    return AppSettings(runs_db_path=tmp_path / "runs.db")


def test_cli_cancel_run_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("AIGNT_OS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("AIGNT_OS_RUNS_DB_PATH", str(tmp_path / "runs.db"))
    result = runner.invoke(app, ["runs", "cancel", "non-existent-id"])
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    if result.exception:
        print(f"EXCEPTION: {result.exception}")
    assert result.exit_code != 0
    # Check both just in case
    output = (result.stdout + result.stderr).lower()
    assert "not found" in output


def test_cli_cancel_pending_run(tmp_path, monkeypatch):
    # Setup
    db_path = tmp_path / "runs.db"
    repo = RunRepository(db_path)
    spec_path = tmp_path / "spec.md"
    spec_path.touch()
    run_id = repo.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="PLAN",
        spec_hash="abc",
        initiated_by="system",
    )

    # Run cancel command
    monkeypatch.setenv("AIGNT_OS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("AIGNT_OS_RUNS_DB_PATH", str(db_path))
    result = runner.invoke(app, ["runs", "cancel", run_id])

    print(f"STDOUT: {result.stdout}")
    if result.exception:
        print(f"EXCEPTION: {result.exception}")

    assert result.exit_code == 0
    # Should be cancelled immediately because it wasn't locked
    assert "cancelled" in result.stdout.lower()

    record = repo.get_run(run_id)
    assert record.status == "cancelled"


def test_cli_cancel_running_run(tmp_path, monkeypatch):
    # Setup
    db_path = tmp_path / "runs.db"
    repo = RunRepository(db_path)
    spec_path = tmp_path / "spec.md"
    spec_path.touch()
    run_id = repo.create_run(
        spec_path=spec_path,
        initial_state="PLAN",
        stop_at="CODE_GREEN",
        spec_hash="abc",
        initiated_by="system",
    )

    # Lock it to simulate running worker
    repo.acquire_lock(run_id)

    # Run cancel command
    monkeypatch.setenv("AIGNT_OS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("AIGNT_OS_RUNS_DB_PATH", str(db_path))
    result = runner.invoke(app, ["runs", "cancel", run_id])

    print(f"STDOUT: {result.stdout}")
    if result.exception:
        print(f"EXCEPTION: {result.exception}")

    assert result.exit_code == 0
    # Should be marked cancelling (signal sent)
    assert "cancellation signal sent" in result.stdout.lower()

    record = repo.get_run(run_id)
    assert record.status == "cancelling"
    # Lock is still held by worker (simulated)
    assert record.locked is True

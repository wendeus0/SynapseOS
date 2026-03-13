import errno
import signal
from unittest.mock import Mock, patch

import pytest

from aignt_os.runtime.service import (
    PROCESS_MARKER,
    RuntimeLifecycleError,
    RuntimeService,
    _pid_exists,
    _process_identity_matches,
)
from aignt_os.runtime.state import RuntimeState


@pytest.fixture
def mock_state_store():
    store = Mock()
    store.read.return_value = RuntimeState(status="stopped")
    store.write_running.return_value = RuntimeState(
        status="running", pid=123, process_identity="test_id"
    )
    store.write_stopped.return_value = RuntimeState(status="stopped")
    return store


@pytest.fixture
def service(tmp_path, mock_state_store):
    svc = RuntimeService(tmp_path / "state.json")
    svc.state_store = mock_state_store
    return svc


def test_pid_exists_esrch():
    with patch("os.kill") as mock_kill:
        mock_kill.side_effect = OSError(errno.ESRCH, "No such process")
        assert not _pid_exists(123)


def test_pid_exists_eperm():
    with patch("os.kill") as mock_kill:
        mock_kill.side_effect = OSError(errno.EPERM, "Operation not permitted")
        assert _pid_exists(123)


def test_pid_exists_other_error():
    with patch("os.kill") as mock_kill:
        mock_kill.side_effect = OSError(errno.EACCES, "Permission denied")
        with pytest.raises(OSError):
            _pid_exists(123)


def test_process_identity_matches_no_identity():
    assert not _process_identity_matches(123, None)


def test_process_identity_matches_read_error():
    with patch("pathlib.Path.read_text", side_effect=OSError):
        assert not _process_identity_matches(123, "test_id")


def test_process_identity_matches_marker_found():
    with patch("pathlib.Path.read_text") as mock_read:
        mock_read.return_value = f"python\x00-c\x00code\x00{PROCESS_MARKER}\x00test_id"
        assert _process_identity_matches(123, "test_id")


def test_process_identity_matches_foreground_found():
    with patch("pathlib.Path.read_text") as mock_read:
        mock_read.return_value = "python\x00runtime\x00run\x00--process-identity\x00test_id"
        assert _process_identity_matches(123, "test_id")


def test_stop_process_immediate(service):
    with (
        patch("os.kill") as mock_kill,
        patch("aignt_os.runtime.service._pid_exists", side_effect=[True, False]),
    ):
        service._stop_process(123)
        mock_kill.assert_called_with(123, signal.SIGTERM)


def test_stop_process_force_kill(service):
    # Simulate SIGTERM failing (pid still exists) then SIGKILL succeeding
    with (
        patch("os.kill") as mock_kill,
        patch("time.sleep"),
        patch("aignt_os.runtime.service._pid_exists", side_effect=[True, True, True, False]),
    ):
        # We need to mock time.monotonic to advance or loop just enough
        # But here we control the loop via side_effect of _pid_exists
        # The loop condition is time-based, so we mock time.monotonic too?
        # Actually simpler: if _pid_exists returns False eventually, loop breaks.
        # But loop also breaks on timeout.

        # Let's mock time.monotonic to force timeout of first loop
        with patch("time.monotonic", side_effect=[0, 100, 100, 200]):
            service._stop_process(123)

        assert mock_kill.call_count >= 2
        # Verify SIGKILL was called
        mock_kill.assert_any_call(123, signal.SIGKILL)


def test_run_foreground_lifecycle(service):
    # This tests the main loop logic without spawning a process
    service.state_store.read.return_value = RuntimeState(status="stopped")

    # We need to break the loop.
    # run_foreground registers signal handlers.
    # We can use a side effect on worker.poll_once to raise an exception or set a flag?
    # Or start a thread that sends SIGTERM?
    # Or mock signal.signal to capture the handler and call it?

    captured_handler = None

    def mock_signal(sig, handler):
        nonlocal captured_handler
        if sig == signal.SIGTERM:
            captured_handler = handler
        return lambda *args: None

    with patch("signal.signal", side_effect=mock_signal):
        # We'll run it in a way that breaks loop
        # We can patch 'time.sleep' to call the handler after first sleep

        def trigger_shutdown(*args):
            if captured_handler:
                captured_handler(signal.SIGTERM, None)

        with patch("time.sleep", side_effect=trigger_shutdown):
            service.run_foreground("test_id")

        service.state_store.write_running.assert_called()
        service.state_store.write_stopped.assert_called()


def test_start_success(service):
    service.state_store.read.return_value = RuntimeState(status="stopped")

    with patch("subprocess.Popen") as mock_popen, patch("time.sleep"):
        mock_process = Mock()
        mock_process.pid = 999
        mock_popen.return_value = mock_process

        service.start(started_by="user")

        mock_popen.assert_called()
        service.state_store.write_running.assert_called()
        args, kwargs = service.state_store.write_running.call_args
        assert args[0] == 999
        assert kwargs["started_by"] == "user"


def test_start_already_running(service):
    service.state_store.read.return_value = RuntimeState(
        status="running", pid=123, process_identity="test_id"
    )
    # Ensure it looks really running so we hit the "already running" check
    with (
        patch("aignt_os.runtime.service._pid_exists", return_value=True),
        patch("aignt_os.runtime.service._process_identity_matches", return_value=True),
    ):
        with pytest.raises(RuntimeLifecycleError, match="already running"):
            service.start()


def test_current_state_running_valid(service):
    # State says running, and PID exists + identity matches
    service.state_store.read.return_value = RuntimeState(
        status="running", pid=123, process_identity="id"
    )

    with (
        patch("aignt_os.runtime.service._pid_exists", return_value=True),
        patch("aignt_os.runtime.service._process_identity_matches", return_value=True),
    ):
        state = service.current_state()
        assert state.status == "running"


def test_current_state_running_but_pid_missing(service):
    # State says running, but PID gone -> Inconsistent
    service.state_store.read.return_value = RuntimeState(
        status="running", pid=123, process_identity="id"
    )

    with patch("aignt_os.runtime.service._pid_exists", return_value=False):
        state = service.current_state()
        # The logic in service.py:
        # if not _pid_exists(pid) or not _process_identity_matches(...):
        #    return RuntimeState(status="inconsistent", ...)

        assert state.status == "inconsistent"


def test_current_state_running_but_identity_mismatch(service):
    # PID exists but identity mismatch -> Inconsistent
    service.state_store.read.return_value = RuntimeState(
        status="running", pid=123, process_identity="id"
    )

    with (
        patch("aignt_os.runtime.service._pid_exists", return_value=True),
        patch("aignt_os.runtime.service._process_identity_matches", return_value=False),
    ):
        state = service.current_state()
        assert state.status == "inconsistent"


def test_stop_not_running(service):
    service.state_store.read.return_value = RuntimeState(status="stopped")
    with pytest.raises(RuntimeLifecycleError, match="not running"):
        service.stop()


def test_stop_inconsistent(service):
    # mocking current_state to return inconsistent directly
    with patch.object(service, "current_state") as mock_state:
        mock_state.return_value = RuntimeState(status="inconsistent")
        with pytest.raises(RuntimeLifecycleError, match="inconsistent"):
            service.stop()


def test_pid_exists_success():
    with patch("os.kill"):
        assert _pid_exists(123)


def test_status_and_ready(service):
    with patch.object(service, "current_state") as mock_current:
        mock_current.return_value = RuntimeState(status="running")
        assert service.status().status == "running"
        assert service.ready() is True

        mock_current.return_value = RuntimeState(status="stopped")
        assert service.status().status == "stopped"
        assert service.ready() is False


def test_start_inconsistent(service):
    # This hits _require_runnable_state -> checks inconsistent
    service.state_store.read.return_value = RuntimeState(status="inconsistent", pid=123)
    # mock _pid_exists logic if needed, but inconsistent state comes from read() directly usually?
    # Actually inconsistent usually computed.
    # But if read() returns inconsistent (e.g. from file corruption logic or manual set),
    # _require_runnable_state checks it.

    # Wait, current_state() logic:
    # if state.status != "running" or state.pid is None: return state
    # So if store returns "inconsistent", current_state returns "inconsistent".

    with pytest.raises(RuntimeLifecycleError, match="inconsistent"):
        service.start()


def test_run_foreground_worker_poll(service):
    # Test the worker polling loop logic
    mock_worker = Mock()
    service.worker = mock_worker

    # We want loop to run once, poll, process, then loop again or break?
    # We can use side_effect on poll_once to break loop via signal handler trick?

    # Or just test one iteration logic?
    # run_foreground is an infinite loop.

    # Let's mock time.sleep to raise exception to break loop if needed,
    # but run_foreground catches nothing?
    # It catches nothing.

    # We can use the signal handler trick again.
    captured_handler = None

    def mock_signal(sig, handler):
        nonlocal captured_handler
        if sig == signal.SIGTERM:
            captured_handler = handler
        return lambda *args: None

    # Setup: poll_once returns None first (sleeps), then returns ID (processes)
    # Then we trigger shutdown

    mock_worker.poll_once.side_effect = [None, "run-123", Exception("Break")]

    with (
        patch("signal.signal", side_effect=mock_signal),
        patch("time.sleep") as mock_sleep,
        patch("os.getpid", return_value=999),
    ):
        # We need to trigger shutdown after some iterations.
        # mock_sleep is called when poll_once returns None (line 96)
        # OR when worker is None (line 91 - not case here)

        def side_effect_sleep(*args):
            # This is called when poll_once returns None
            pass

        mock_sleep.side_effect = side_effect_sleep

        # We need to break the loop.
        # When poll_once raises Exception("Break"), it will propagate and stop run_foreground.
        # This confirms we hit the lines.

        with pytest.raises(Exception, match="Break"):
            service.run_foreground("id")

    # Verify interaction
    assert mock_worker.poll_once.call_count == 3
    mock_worker.sleep_when_idle.assert_called_once()

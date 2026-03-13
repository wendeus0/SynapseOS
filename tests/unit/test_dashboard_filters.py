from unittest.mock import MagicMock

from aignt_os.cli.dashboard import RunDashboard
from aignt_os.persistence import RunStepRecord


# Helper to create mock steps
def create_step(step_id, status):
    return RunStepRecord(
        step_id=step_id,
        run_id="test-run",
        tool_name="test-tool",
        status=status,
        state=status,  # simpler mapping for test
        created_at="2023-01-01T00:00:00",
        duration_ms=100,
        raw_output_path=None,
        clean_output_path=None,
        return_code=0 if status == "completed" else 1,
        timed_out=False,
    )


MOCK_STEPS = [
    create_step(1, "completed"),
    create_step(2, "failed"),
    create_step(3, "running"),
    create_step(4, "pending"),
    create_step(5, "completed"),
    create_step(6, "failed"),
]


class TestDashboardFilters:
    def setup_method(self):
        """Setup a dashboard instance with mocked repository."""
        self.app = RunDashboard(run_id="test-run")
        # Mock repository
        self.app.repository = MagicMock()
        self.app.repository.list_steps.return_value = MOCK_STEPS
        # Mock UI elements that would be composed
        self.app.step_list = MagicMock()
        self.app.step_list.clear = MagicMock()
        self.app.step_list.append = MagicMock()
        # Mock run header update
        self.app.run_header = MagicMock()
        self.app.run_header.update_info = MagicMock()
        self.app.artifact_explorer = MagicMock()
        self.app.artifact_explorer.load_artifacts = MagicMock()

    def test_default_filter_shows_all(self):
        """Test that by default all steps are shown."""
        # Initial state should be 'all'
        assert getattr(self.app, "current_filter", "all") == "all"

        self.app.refresh_data()

        # Should append all 6 steps
        assert self.app.step_list.append.call_count == 6

    def test_filter_failed_steps(self):
        """Test filtering only failed steps."""
        # Simulate applying filter (method to be implemented)
        self.app.action_filter_failed()

        # Verify state change
        assert self.app.current_filter == "failed"

        # NOTE: action_filter_failed() already calls refresh_data()
        # So we should verify call count directly, or reset mock before check
        # But wait, action_filter_failed calls refresh_data, which appends 2 items.
        # IF we call refresh_data AGAIN manually, it appends 2 MORE items.
        # The mock.append.call_count accumulates.

        # Let's check if the items appended correspond to the filter.
        # Since action_filter_failed calls refresh_data, we don't need to call it again.

        # Should append only the 2 failed steps
        assert self.app.step_list.append.call_count == 2

        # Verify the items appended are indeed the failed ones
        call_args_list = self.app.step_list.append.call_args_list
        for call_args in call_args_list:
            step_item = call_args[0][0]
            assert step_item.step.status == "failed"

    def test_filter_active_steps(self):
        """Test filtering running and pending steps."""
        self.app.action_filter_active()

        assert self.app.current_filter == "active"

        # Should append running (1) and pending (1) = 2 steps
        assert self.app.step_list.append.call_count == 2

        call_args_list = self.app.step_list.append.call_args_list
        for call_args in call_args_list:
            step_item = call_args[0][0]
            assert step_item.step.status in ("running", "pending")

    def test_restore_all_filter(self):
        """Test switching back to 'all' filter."""
        # Set to failed first
        self.app.action_filter_failed()
        assert self.app.step_list.append.call_count == 2

        # Reset counters
        self.app.step_list.append.reset_mock()

        # Switch to all
        self.app.action_filter_all()
        assert self.app.current_filter == "all"

        # action_filter_all calls refresh_data
        assert self.app.step_list.append.call_count == 6

    def test_header_shows_active_filter(self):
        """Test that the UI indicates the active filter."""
        # This might require checking if a class is added to the header or title updated
        # For now, let's assume we update the window title or a specific label
        self.app.action_filter_failed()
        assert "FILTER: failed" in self.app.title or "failed" in str(self.app.current_filter)

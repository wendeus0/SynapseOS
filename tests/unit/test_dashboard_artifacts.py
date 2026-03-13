from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from textual.widgets import ListView, Static

from aignt_os.cli.dashboard import ArtifactExplorer
from aignt_os.persistence import ArtifactStore


class TestArtifactExplorer:
    @pytest.fixture
    def store_mock(self):
        return MagicMock(spec=ArtifactStore)

    @pytest.fixture
    def app_mock(self, store_mock):
        app = MagicMock()
        app.run_id = "test-run"
        app.artifact_store = store_mock
        # Mocking settings
        app.settings = MagicMock()
        app.settings.artifacts_dir_resolved = Path("/tmp/artifacts")
        return app

    def test_initialization(self):
        """Test that ArtifactExplorer initializes correctly."""
        explorer = ArtifactExplorer()
        assert isinstance(explorer, Static)

    def test_load_artifacts(self, app_mock, store_mock):
        """Test loading artifacts list."""
        explorer = ArtifactExplorer()

        with patch.object(ArtifactExplorer, "app", new_callable=PropertyMock) as mock_app_prop:
            mock_app_prop.return_value = app_mock

            # Mock artifact paths
            store_mock.list_artifact_paths.return_value = ["file1.txt", "dir/file2.json"]

            # Mock UI elements
            list_view = MagicMock(spec=ListView)

            # Mock query_one to return list_view when called with "#artifact_list"
            def side_effect(selector, type=None):
                if selector == "#artifact_list":
                    return list_view
                return MagicMock()

            explorer.query_one = MagicMock(side_effect=side_effect)

            # Call the method
            explorer.load_artifacts()

            store_mock.list_artifact_paths.assert_called_once_with("test-run")
            assert list_view.clear.call_count == 1
            # It should append list items.
            assert list_view.append.call_count == 2

    def test_show_artifact_content_text(self, app_mock):
        """Test showing content of a text file."""
        explorer = ArtifactExplorer()

        with patch.object(ArtifactExplorer, "app", new_callable=PropertyMock) as mock_app_prop:
            mock_app_prop.return_value = app_mock

            content_view = MagicMock(spec=Static)

            def side_effect(selector, type=None):
                if selector == "#artifact_content":
                    return content_view
                return MagicMock()

            explorer.query_one = MagicMock(side_effect=side_effect)

            # Mock file reading
            with patch("pathlib.Path.read_text", return_value="content"):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.is_file", return_value=True):
                        # Call the method
                        explorer.show_artifact("file1.txt")

            content_view.update.assert_called_with("content")

    def test_show_artifact_content_binary(self, app_mock):
        """Test showing metadata for binary file."""
        explorer = ArtifactExplorer()

        with patch.object(ArtifactExplorer, "app", new_callable=PropertyMock) as mock_app_prop:
            mock_app_prop.return_value = app_mock

            content_view = MagicMock(spec=Static)
            explorer.query_one = MagicMock(return_value=content_view)

            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1024
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.is_file", return_value=True):
                        # Use show_artifact, not show_artifact_content (typo in previous test code)
                        explorer.show_artifact("image.png")

            # Should verify it called update with some metadata string
            args = content_view.update.call_args[0][0]
            assert "Binary file" in args
            assert "1024 bytes" in args

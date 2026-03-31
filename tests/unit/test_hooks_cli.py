from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from synapse_os.cli.app import app

runner = CliRunner()


class TestHooksListCommand:
    def test_hooks_list_no_hooks(self) -> None:
        result = runner.invoke(app, ["hooks", "list"])
        assert result.exit_code == 0
        assert (
            "No hooks configured" in result.output
            or "nenhum hook" in result.output.lower()
        )

    def test_hooks_list_with_global_hooks(self) -> None:
        from synapse_os.runtime_contracts import HookConfig

        with patch("synapse_os.cli.hooks.AppSettings") as MockSettings:
            mock_settings = MockSettings.return_value
            mock_settings.hooks = [
                HookConfig(point="pre_step", handler="os.path.join"),
                HookConfig(point="post_step", handler="os.path.dirname"),
            ]
            result = runner.invoke(app, ["hooks", "list"])
        assert result.exit_code == 0
        assert "os.path.join" in result.output
        assert "os.path.dirname" in result.output
        assert "pre_step" in result.output
        assert "post_step" in result.output

    def test_hooks_list_with_spec_hooks(self, tmp_path: Path) -> None:
        from synapse_os.runtime_contracts import HookConfig

        spec_path = tmp_path / "SPEC.md"
        spec_path.write_text(
            "---\nid: F1\ntype: feature\nsummary: test\ninputs: [a]\noutputs: [b]\nacceptance_criteria: [c]\nnon_goals: []\nhooks:\n  - point: pre_step\n    handler: os.path.join\n---\n\n# Contexto\ntest\n\n# Objetivo\ntest\n"
        )

        with patch("synapse_os.cli.hooks.AppSettings") as MockSettings:
            mock_settings = MockSettings.return_value
            mock_settings.hooks = []
            result = runner.invoke(app, ["hooks", "list", "--spec", str(spec_path)])
        assert result.exit_code == 0
        assert "os.path.join" in result.output

    def test_hooks_list_with_global_and_spec_hooks(self, tmp_path: Path) -> None:
        from synapse_os.runtime_contracts import HookConfig

        spec_path = tmp_path / "SPEC.md"
        spec_path.write_text(
            "---\nid: F1\ntype: feature\nsummary: test\ninputs: [a]\noutputs: [b]\nacceptance_criteria: [c]\nnon_goals: []\nhooks:\n  - point: post_step\n    handler: os.path.dirname\n---\n\n# Contexto\ntest\n\n# Objetivo\ntest\n"
        )

        with patch("synapse_os.cli.hooks.AppSettings") as MockSettings:
            mock_settings = MockSettings.return_value
            mock_settings.hooks = [
                HookConfig(point="pre_step", handler="os.path.join"),
            ]
            result = runner.invoke(app, ["hooks", "list", "--spec", str(spec_path)])
        assert result.exit_code == 0
        assert "os.path.join" in result.output
        assert "os.path.dirname" in result.output

    def test_hooks_list_with_malformed_spec(self, tmp_path: Path) -> None:
        spec_path = tmp_path / "SPEC.md"
        spec_path.write_text(
            "---\nid: F1\ntype: feature\nsummary: test\ninputs: [a]\noutputs: [b]\nacceptance_criteria: [c]\nnon_goals: []\nhooks:\n  - point: invalid_point\n    handler: some.func\n---\n\n# Contexto\ntest\n\n# Objetivo\ntest\n"
        )

        with patch("synapse_os.cli.hooks.AppSettings") as MockSettings:
            mock_settings = MockSettings.return_value
            mock_settings.hooks = []
            result = runner.invoke(app, ["hooks", "list", "--spec", str(spec_path)])
        assert result.exit_code == 1
        assert "invalid" in result.output.lower() or "error" in result.output.lower()


class TestHooksValidateCommand:
    def test_hooks_validate_valid_handler(self) -> None:
        result = runner.invoke(app, ["hooks", "validate", "os.path.join"])
        assert result.exit_code == 0
        assert "join" in result.output

    def test_hooks_validate_invalid_module(self) -> None:
        result = runner.invoke(app, ["hooks", "validate", "nonexistent_module.func"])
        assert result.exit_code == 1
        assert "nonexistent_module" in result.output

    def test_hooks_validate_invalid_function(self) -> None:
        result = runner.invoke(app, ["hooks", "validate", "os.nonexistent_func"])
        assert result.exit_code == 1
        assert "nonexistent_func" in result.output

    def test_hooks_validate_no_dots(self) -> None:
        result = runner.invoke(app, ["hooks", "validate", "nodots"])
        assert result.exit_code == 1
        assert "dotted" in result.output.lower()


class TestHooksStatusCommand:
    def test_hooks_status_no_active_hooks(self) -> None:
        result = runner.invoke(app, ["hooks", "status"])
        assert result.exit_code == 0
        assert (
            "No active hooks" in result.output or "nenhum hook" in result.output.lower()
        )

from __future__ import annotations

import re
from importlib import import_module
from pathlib import Path


def _release_env(tmp_path: Path) -> dict[str, str]:
    return {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path / "runtime"),
        "AIGNT_OS_RUNS_DB_PATH": str(tmp_path / "runs" / "runs.sqlite3"),
        "AIGNT_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
    }


def _write_valid_spec(path: Path) -> None:
    path.write_text(
        """---
id: F22-integration
type: feature
summary: Fixture spec for release readiness integration tests.
inputs:
  - raw_request
outputs:
  - validated_spec
acceptance_criteria:
  - must validate
non_goals: []
---

# Contexto

Fixture context.

# Objetivo

Fixture objective.
""",
        encoding="utf-8",
    )


def _extract_run_id(stdout: str) -> str:
    match = re.search(r"run_id:\s+([a-f0-9-]+)", stdout, re.IGNORECASE)
    if match is None:
        raise AssertionError(f"run_id not found in CLI output:\n{stdout}")
    return match.group(1)


def test_phase_2_release_readiness_keeps_public_quickstart_executable(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    env = _release_env(tmp_path)
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)

    doctor_result = cli_runner.invoke(cli_app, ["doctor"], env=env)
    assert doctor_result.exit_code == 0

    submit_result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "sync", "--stop-at", "SPEC_VALIDATION"],
        env=env,
    )
    assert submit_result.exit_code == 0

    run_id = _extract_run_id(submit_result.stdout)
    show_result = cli_runner.invoke(cli_app, ["runs", "show", run_id], env=env)

    assert show_result.exit_code == 0
    assert run_id in show_result.stdout
    assert "canonical happy path is complete" in show_result.stdout.lower()


def test_phase_2_release_readiness_previews_real_persisted_run_report_via_public_cli(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    env = _release_env(tmp_path)
    repository = persistence.RunRepository(Path(env["AIGNT_OS_RUNS_DB_PATH"]))
    artifact_store = persistence.ArtifactStore(Path(env["AIGNT_OS_ARTIFACTS_DIR"]))

    class _FixedExecutor:
        def __init__(
            self,
            artifact_name: str,
            content: str,
            *,
            tool_name: str | None = None,
        ) -> None:
            self.artifact_name = artifact_name
            self.content = content
            self.tool_name = tool_name

        def execute(self, step, context):  # type: ignore[no-untyped-def]
            del step, context
            pipeline = import_module("aignt_os.pipeline")
            return pipeline.StepExecutionResult(
                artifacts={self.artifact_name: self.content},
                raw_output=self.content,
                clean_output=self.content,
                tool_name=self.tool_name,
                return_code=0 if self.tool_name is not None else None,
                duration_ms=45 if self.tool_name is not None else None,
                timed_out=False if self.tool_name is not None else None,
            )

    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
        executors={
            "PLAN": _FixedExecutor("plan_md", "# Plan\n", tool_name="codex"),
            "TEST_RED": _FixedExecutor("tests_md", "# Tests\n"),
            "CODE_GREEN": _FixedExecutor("code_md", "# Green\n"),
            "QUALITY_GATE": _FixedExecutor("quality_gate_md", "# Quality Gate\n"),
            "REVIEW": _FixedExecutor("review_md", "# Review\n"),
            "SECURITY": _FixedExecutor("security_md", "# Security\n"),
        },
    )

    context = runner.run(spec_path, stop_at="DOCUMENT")
    preview_result = cli_runner.invoke(
        cli_app,
        ["runs", "show", context.run_id, "--preview", "report"],
        env=env,
    )

    assert preview_result.exit_code == 0
    assert "artifact preview" in preview_result.stdout.lower()
    assert f"{context.run_id}/RUN_REPORT.md" in preview_result.stdout
    assert "# RUN_REPORT" in preview_result.stdout

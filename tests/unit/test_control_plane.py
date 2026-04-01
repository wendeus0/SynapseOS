"""Tests for the Local Control Plane (F60)."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from synapse_os.control_plane.server import create_app
from synapse_os.persistence import RunRecord, RunStepRecord


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_ok_when_runtime_running(self):
        runtime_service = MagicMock()
        runtime_service.ready.return_value = True

        app = create_app(runtime_service=runtime_service, api_token=None)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["runtime"] == "running"

    @pytest.mark.asyncio
    async def test_health_returns_ok_when_runtime_stopped(self):
        runtime_service = MagicMock()
        runtime_service.ready.return_value = False

        app = create_app(runtime_service=runtime_service, api_token=None)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["runtime"] == "stopped"

    @pytest.mark.asyncio
    async def test_health_is_public_no_auth_required(self):
        runtime_service = MagicMock()
        runtime_service.ready.return_value = True

        app = create_app(runtime_service=runtime_service, api_token="secret-token")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200


class TestAuthMiddleware:
    """Tests for API token authentication middleware."""

    @pytest.mark.asyncio
    async def test_returns_401_without_token_when_auth_enabled(self):
        runtime_service = MagicMock()
        app = create_app(runtime_service=runtime_service, api_token="secret-token")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/runs")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_401_with_invalid_token(self):
        runtime_service = MagicMock()
        app = create_app(runtime_service=runtime_service, api_token="secret-token")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/runs",
                headers={"Authorization": "Bearer wrong-token"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_allows_request_with_valid_token(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        run_repo.list_runs.return_value = []

        app = create_app(
            runtime_service=runtime_service,
            api_token="secret-token",
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/runs",
                headers={"Authorization": "Bearer secret-token"},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_auth_required_when_token_not_configured(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        run_repo.list_runs.return_value = []

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/runs")

        assert response.status_code == 200


class TestListRunsEndpoint:
    """Tests for GET /api/v1/runs endpoint."""

    def _make_run_record(self, run_id, status="pending", spec_path="/tmp/spec.md"):
        return RunRecord(
            run_id=run_id,
            spec_path=spec_path,
            workspace_path="/tmp/workspace",
            spec_hash=None,
            initiated_by="test",
            stop_at="COMPLETE",
            status=status,
            current_state="REQUEST",
            locked=False,
            failure_message=None,
            created_at="2026-03-31T10:00:00Z",
            updated_at="2026-03-31T10:00:00Z",
            completed_at=None,
        )

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_runs(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        run_repo.list_runs.return_value = []

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/runs")

        assert response.status_code == 200
        data = response.json()
        assert data["runs"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_returns_paginated_runs(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        mock_run = self._make_run_record("run-1", "completed", "/tmp/spec.md")
        run_repo.list_runs.return_value = [mock_run]

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/runs?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) == 1
        assert data["total"] == 1
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert data["runs"][0]["id"] == "run-1"
        assert data["runs"][0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_truncates_long_prompt(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        long_path = "/tmp/" + "x" * 500 + ".md"
        mock_run = self._make_run_record("run-1", "pending", long_path)
        run_repo.list_runs.return_value = [mock_run]

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/runs")

        data = response.json()
        assert len(data["runs"][0]["prompt"]) <= 100


class TestCreateRunEndpoint:
    """Tests for POST /api/v1/runs endpoint."""

    @pytest.mark.asyncio
    async def test_creates_run_with_valid_prompt(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        run_repo.create_run.return_value = "new-run-123"

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/runs",
                json={"prompt": "implement a sorting algorithm"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["run_id"] == "new-run-123"
        assert data["status"] == "pending"
        run_repo.create_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_empty_prompt(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/runs", json={"prompt": ""})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_missing_prompt(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/runs", json={})

        assert response.status_code == 422


class TestRunDetailEndpoint:
    """Tests for GET /api/v1/runs/{run_id} endpoint."""

    def _make_run_record(self, run_id, status="completed"):
        return RunRecord(
            run_id=run_id,
            spec_path="/tmp/spec.md",
            workspace_path="/tmp/workspace",
            spec_hash=None,
            initiated_by="test",
            stop_at="COMPLETE",
            status=status,
            current_state="COMPLETE",
            locked=False,
            failure_message=None,
            created_at="2026-03-31T10:00:00Z",
            updated_at="2026-03-31T11:00:00Z",
            completed_at="2026-03-31T11:00:00Z",
        )

    @pytest.mark.asyncio
    async def test_returns_run_detail(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        mock_run = self._make_run_record("run-1", "completed")
        run_repo.get_run.return_value = mock_run
        run_repo.list_steps.return_value = [
            RunStepRecord(
                step_id=1,
                run_id="run-1",
                state="SPEC",
                status="completed",
                raw_output_path=None,
                clean_output_path=None,
                tool_name=None,
                return_code=0,
                duration_ms=100,
                timed_out=False,
                created_at="2026-03-31T10:00:00Z",
            ),
        ]

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/runs/run-1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "run-1"
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_run(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        run_repo.get_run.side_effect = Exception("no rows found")

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/runs/nonexistent")

        assert response.status_code == 404


class TestCancelRunEndpoint:
    """Tests for POST /api/v1/runs/{run_id}/cancel endpoint."""

    def _make_run_record(self, run_id, status="pending"):
        return RunRecord(
            run_id=run_id,
            spec_path="/tmp/spec.md",
            workspace_path="/tmp/workspace",
            spec_hash=None,
            initiated_by="test",
            stop_at="COMPLETE",
            status=status,
            current_state="REQUEST",
            locked=False,
            failure_message=None,
            created_at="2026-03-31T10:00:00Z",
            updated_at="2026-03-31T10:00:00Z",
            completed_at=None,
        )

    @pytest.mark.asyncio
    async def test_cancels_pending_run(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        mock_run = self._make_run_record("run-1", "pending")
        run_repo.get_run.return_value = mock_run

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/runs/run-1/cancel")

        assert response.status_code == 200
        run_repo.mark_run_cancelling.assert_called_once_with("run-1")
        run_repo.mark_run_cancelled.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_409_for_completed_run(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        mock_run = self._make_run_record("run-1", "completed")
        run_repo.get_run.return_value = mock_run

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/runs/run-1/cancel")

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_returns_409_for_failed_run(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        mock_run = self._make_run_record("run-1", "failed")
        run_repo.get_run.return_value = mock_run

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/runs/run-1/cancel")

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_run(self):
        runtime_service = MagicMock()
        run_repo = MagicMock()
        run_repo.get_run.side_effect = Exception("not found")

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/runs/nonexistent/cancel")

        assert response.status_code == 404


class TestRuntimeStatusEndpoint:
    """Tests for GET /api/v1/runtime/status endpoint."""

    @pytest.mark.asyncio
    async def test_returns_runtime_status(self):
        runtime_service = MagicMock()
        mock_state = MagicMock()
        mock_state.status = "running"
        mock_state.pid = 12345
        mock_state.started_at = "2026-03-31T10:00:00+00:00"
        runtime_service.current_state.return_value = mock_state

        run_repo = MagicMock()
        run_repo.list_unlocked_pending_runs.return_value = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            run_repository=run_repo,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/runtime/status")

        assert response.status_code == 200
        data = response.json()
        assert data["pid"] == 12345
        assert data["state"] == "running"
        assert data["pending_runs"] == 3


class TestArtifactsEndpoint:
    """Tests for GET /api/v1/artifacts/{run_id} endpoint."""

    @pytest.mark.asyncio
    async def test_lists_artifacts_for_run(self):
        runtime_service = MagicMock()
        artifact_store = MagicMock()
        artifact_store.list_artifact_paths.return_value = [
            "run1/SPEC.md",
            "run1/main.py",
        ]

        artifact_store.base_path = MagicMock()
        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_stat.st_mtime = 1743405600.0
        mock_path = MagicMock()
        mock_path.stat.return_value = mock_stat
        mock_path.name = "SPEC.md"
        artifact_store.base_path.__truediv__ = MagicMock(return_value=mock_path)

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            artifact_store=artifact_store,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/artifacts/run-1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["artifacts"]) == 2

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_run_artifacts(self):
        runtime_service = MagicMock()
        artifact_store = MagicMock()
        artifact_store.list_artifact_paths.side_effect = FileNotFoundError(
            "run not found"
        )

        app = create_app(
            runtime_service=runtime_service,
            api_token=None,
            artifact_store=artifact_store,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/artifacts/nonexistent")

        assert response.status_code == 404

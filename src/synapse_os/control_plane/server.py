"""FastAPI application for the Local Control Plane."""

from __future__ import annotations

import os
from datetime import UTC
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from synapse_os.control_plane.middleware import AuthMiddleware
from synapse_os.control_plane.models import (
    ArtifactItem,
    ArtifactListResponse,
    HealthResponse,
    RunCreateRequest,
    RunCreateResponse,
    RunDetailResponse,
    RunListItem,
    RunListResponse,
    RunStepItem,
    RuntimeStatusResponse,
)

if TYPE_CHECKING:
    from synapse_os.persistence import ArtifactStore, RunRepository
    from synapse_os.runtime.service import RuntimeService

MAX_PROMPT_PREVIEW = 100
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def create_app(
    *,
    runtime_service: RuntimeService | None = None,
    run_repository: RunRepository | None = None,
    artifact_store: ArtifactStore | None = None,
    api_token: str | None = None,
) -> FastAPI:
    app = FastAPI(
        title="SynapseOS Control Plane",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )

    if api_token is not None:
        app.add_middleware(AuthMiddleware, api_token=api_token)

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        runtime_status = "unknown"
        if runtime_service is not None:
            try:
                runtime_status = "running" if runtime_service.ready() else "stopped"
            except Exception:
                runtime_status = "stopped"
        return HealthResponse(status="ok", runtime=runtime_status)

    @app.get("/api/v1/runs", response_model=RunListResponse)
    async def list_runs(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> RunListResponse:
        if run_repository is None:
            raise HTTPException(status_code=503, detail="Run repository not configured")

        all_runs = run_repository.list_runs()
        total = len(all_runs)
        page = all_runs[offset : offset + limit]

        return RunListResponse(
            runs=[
                RunListItem(
                    id=r.run_id,
                    status=r.status,
                    prompt=(r.spec_path[:MAX_PROMPT_PREVIEW] if hasattr(r, "spec_path") else ""),
                    created_at=r.created_at,
                )
                for r in page
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    @app.post("/api/v1/runs", response_model=RunCreateResponse, status_code=201)
    async def create_run(request: RunCreateRequest) -> RunCreateResponse:
        if run_repository is None:
            raise HTTPException(status_code=503, detail="Run repository not configured")

        spec_path = _create_spec_from_prompt(request.prompt)
        run_id = run_repository.create_run(
            spec_path=spec_path,
            initial_state="REQUEST",
            stop_at="COMPLETE",
            initiated_by="api",
        )

        return RunCreateResponse(run_id=run_id, status="pending")

    @app.get("/api/v1/runs/{run_id}", response_model=RunDetailResponse)
    async def get_run(run_id: str) -> RunDetailResponse:
        if run_repository is None:
            raise HTTPException(status_code=503, detail="Run repository not configured")

        try:
            run = run_repository.get_run(run_id)
        except Exception as err:
            raise HTTPException(status_code=404, detail="Run not found") from err

        steps = []
        try:
            for s in run_repository.list_steps(run_id):
                steps.append(RunStepItem(name=s.state, status=s.status))
        except Exception:
            pass

        artifacts = []
        if artifact_store is not None:
            try:
                artifacts = artifact_store.list_artifact_paths(run_id)
            except Exception:
                pass

        return RunDetailResponse(
            id=run.run_id,
            status=run.status,
            prompt=run.spec_path,
            created_at=run.created_at,
            updated_at=run.updated_at,
            steps=steps,
            artifacts=artifacts,
        )

    @app.post("/api/v1/runs/{run_id}/cancel")
    async def cancel_run(run_id: str) -> JSONResponse:
        if run_repository is None:
            raise HTTPException(status_code=503, detail="Run repository not configured")

        try:
            run = run_repository.get_run(run_id)
        except Exception as err:
            raise HTTPException(status_code=404, detail="Run not found") from err

        if run.status in TERMINAL_STATUSES:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot cancel run in terminal state: {run.status}",
            )

        try:
            run_repository.mark_run_cancelling(run_id)
        except ValueError as err:
            raise HTTPException(status_code=409, detail="Run cannot be cancelled") from err

        return JSONResponse(content={"status": "cancelling", "run_id": run_id})

    @app.get("/api/v1/runtime/status", response_model=RuntimeStatusResponse)
    async def runtime_status() -> RuntimeStatusResponse:
        if runtime_service is None:
            raise HTTPException(status_code=503, detail="Runtime service not configured")

        state = runtime_service.current_state()
        pending = 0
        if run_repository is not None:
            try:
                pending = len(run_repository.list_unlocked_pending_runs())
            except Exception:
                pass

        uptime = 0
        if state.started_at is not None:
            try:
                from datetime import datetime

                started = datetime.fromisoformat(state.started_at)
                uptime = int((datetime.now(UTC) - started).total_seconds())
            except Exception:
                pass

        return RuntimeStatusResponse(
            pid=state.pid,
            uptime=uptime,
            state=state.status,
            active_runs=1 if state.status == "running" else 0,
            pending_runs=pending,
        )

    @app.get("/api/v1/artifacts/{run_id}", response_model=ArtifactListResponse)
    async def list_artifacts(run_id: str) -> ArtifactListResponse:
        if artifact_store is None:
            raise HTTPException(status_code=503, detail="Artifact store not configured")

        try:
            paths = artifact_store.list_artifact_paths(run_id)
        except FileNotFoundError as err:
            raise HTTPException(status_code=404, detail="Run not found") from err

        artifacts = []
        for p in paths:
            full_path = artifact_store.base_path / p
            try:
                stat = full_path.stat()
                artifact_type = _infer_artifact_type(p)
                artifacts.append(
                    ArtifactItem(
                        name=full_path.name,
                        size_bytes=stat.st_size,
                        created_at=_format_timestamp(stat.st_mtime),
                        type=artifact_type,
                    )
                )
            except OSError:
                continue

        return ArtifactListResponse(artifacts=artifacts)

    return app


def _create_spec_from_prompt(prompt: str) -> Path:
    from uuid import uuid4

    tmp_dir = Path(os.environ.get("TMPDIR", "/tmp")) / "synapse-os" / "api-specs"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    spec_path = tmp_dir / f"{uuid4().hex}.md"
    spec_content = (
        "---\n"
        "feature_id: api-run\n"
        "feature_name: API Run\n"
        "status: draft\n"
        "---\n\n"
        f"# API Run\n\n{prompt}\n"
    )
    spec_path.write_text(spec_content, encoding="utf-8")
    spec_path.chmod(0o600)
    return spec_path


def _infer_artifact_type(path: str) -> str:
    path_lower = path.lower()
    if "spec" in path_lower:
        return "spec"
    if "test" in path_lower:
        return "test"
    if "report" in path_lower:
        return "report"
    if path_lower.endswith((".py", ".ts", ".js", ".rs", ".go")):
        return "code"
    if path_lower.endswith((".md", ".txt")):
        return "document"
    return "other"


def _format_timestamp(ts: float) -> str:
    from datetime import datetime

    return datetime.fromtimestamp(ts, tz=UTC).isoformat()

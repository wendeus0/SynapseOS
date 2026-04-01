"""Pydantic models for the Control Plane API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    runtime: str


class RunListItem(BaseModel):
    id: str
    status: str
    prompt: str
    created_at: str


class RunListResponse(BaseModel):
    runs: list[RunListItem]
    total: int
    limit: int
    offset: int


class RunStepItem(BaseModel):
    name: str
    status: str


class RunDetailResponse(BaseModel):
    id: str
    status: str
    prompt: str
    created_at: str
    updated_at: str
    steps: list[RunStepItem] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)


class RunCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


class RunCreateResponse(BaseModel):
    run_id: str
    status: str


class RuntimeStatusResponse(BaseModel):
    pid: int | None = None
    uptime: int = 0
    state: str
    active_runs: int = 0
    pending_runs: int = 0


class ArtifactItem(BaseModel):
    name: str
    size_bytes: int
    created_at: str
    type: str


class ArtifactListResponse(BaseModel):
    artifacts: list[ArtifactItem]

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator

from synapse_os.security import resolve_path_within_root

if TYPE_CHECKING:
    from synapse_os.pipeline import PipelineContext, PipelineStep, StepExecutionResult
    from synapse_os.supervisor import SupervisorDecision


class ToolSpec(BaseModel):
    model_config = ConfigDict(strict=True)

    name: StrictStr
    capabilities: tuple[StrictStr, ...] = Field(min_length=1)
    command_prefix: tuple[StrictStr, ...] = Field(default_factory=tuple)


class WorkspaceContext(BaseModel):
    model_config = ConfigDict(strict=True)

    root_path: Path
    spec_path: Path


class RunContext(BaseModel):
    model_config = ConfigDict(strict=True)

    run_id: StrictStr | None = None
    initiated_by: StrictStr
    workspace: WorkspaceContext


class WorkspaceProvider(Protocol):
    def resolve(self, spec_path: Path) -> WorkspaceContext: ...


class RunLifecycleHooks(Protocol):
    def on_run_started(self, context: PipelineContext) -> None: ...

    def on_step_completed(
        self,
        step: PipelineStep,
        context: PipelineContext,
        result: StepExecutionResult | None,
    ) -> None: ...

    def on_run_completed(self, context: PipelineContext) -> None: ...

    def on_run_failed(
        self,
        context: PipelineContext,
        step: PipelineStep | None,
        error: Exception,
    ) -> None: ...

    def on_supervisor_decision(
        self,
        step: PipelineStep,
        context: PipelineContext,
        decision: SupervisorDecision,
        error: Exception,
    ) -> None: ...


class LocalWorkspaceProvider:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

    def resolve(self, spec_path: Path) -> WorkspaceContext:
        try:
            resolved_spec_path = resolve_path_within_root(spec_path, root=self.workspace_root)
        except ValueError as exc:
            raise FileNotFoundError(f"SPEC file not found: {spec_path}") from exc
        if not resolved_spec_path.exists():
            raise FileNotFoundError(f"SPEC file not found: {spec_path}")
        if not resolved_spec_path.is_file():
            raise FileNotFoundError(f"SPEC file not found: {spec_path}")
        return WorkspaceContext(
            root_path=self.workspace_root,
            spec_path=resolved_spec_path,
        )


class HookConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    point: Literal["pre_step", "post_step", "pre_state_transition", "post_state_transition"]
    handler: StrictStr = Field(min_length=1)
    failure_mode: Literal["hard_fail", "supervisor_delegate"] = "supervisor_delegate"
    enabled: StrictBool = True


class HookContext(BaseModel):
    model_config = ConfigDict(strict=True)

    run_id: StrictStr
    step_name: StrictStr | None = None
    current_state: StrictStr | None = None
    tool_spec: "ToolSpec | None" = None
    workspace_path: StrictStr | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tool_spec", mode="before")
    @classmethod
    def _validate_tool_spec_type(cls, v: object) -> object:
        if v is not None and not isinstance(v, ToolSpec):
            raise ValueError("tool_spec must be a ToolSpec instance or None")
        return v


class HookResult(BaseModel):
    model_config = ConfigDict(strict=True)

    allowed: StrictBool
    reason: StrictStr | None = None
    context_patch: dict[str, Any] | None = None


class RunScopedWorkspaceProvider:
    def __init__(
        self,
        base_provider: WorkspaceProvider,
        *,
        run_workspace_root: Path,
        run_id: str,
    ) -> None:
        self.base_provider = base_provider
        self.run_workspace_root = run_workspace_root.resolve()
        self.run_id = run_id

    def resolve(self, spec_path: Path) -> WorkspaceContext:
        base_workspace = self.base_provider.resolve(spec_path)
        workspace_path = self.run_workspace_root / self.run_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        return WorkspaceContext(
            root_path=workspace_path,
            spec_path=base_workspace.spec_path,
        )

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)

from aignt_os.cli.rendering import truncate_logs
from aignt_os.config import AppSettings
from aignt_os.persistence import ArtifactStore, RunRecord, RunRepository, RunStepRecord


class LogViewer(ModalScreen[None]):
    """Modal para visualização de logs."""

    CSS = """
    LogViewer {
        align: center middle;
    }

    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 80%;
        height: 80%;
        border: thick $background 80%;
        background: $surface;
    }

    #log_content {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        background: $surface;
        border: solid $secondary;
        overflow-y: scroll;
    }

    #footer_label {
        column-span: 2;
        text-align: center;
        color: $text-muted;
    }
    """

    BINDINGS = [("escape", "app.pop_screen", "Close")]

    def __init__(self, title: str, content: str, path: str | None = None) -> None:
        super().__init__()
        self.dialog_title = title
        self.log_content = content
        self.log_path = path
        self._last_size: int | None = None

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(self.dialog_title, classes="detail_header"),
            RichLog(id="log_content", wrap=True, highlight=True, markup=False),
            Label("Press ESC to close", id="footer_label"),
            id="dialog",
        )

    def on_mount(self) -> None:
        log_widget = self.query_one("#log_content", RichLog)
        log_widget.write(self.log_content)
        if self.log_path:
            self.set_interval(1.0, self.refresh_log)

    def refresh_log(self) -> None:
        if not self.log_path:
            return

        try:
            current_path = Path(self.log_path)
            if not current_path.exists():
                return

            current_size = current_path.stat().st_size
            if current_size == self._last_size:
                return

            settings = AppSettings()
            new_content = current_path.read_text(encoding="utf-8", errors="replace")
            truncated = truncate_logs(new_content, settings.tui_log_buffer_lines)

            log_widget = self.query_one("#log_content", RichLog)
            log_widget.clear()
            log_widget.write(truncated)
            self._last_size = current_size
        except Exception:
            pass


class RunHeader(Static):
    """Exibe informações básicas da run no topo."""

    run_id = reactive("")
    status = reactive("loading...")
    state = reactive("loading...")
    spec_path = reactive("")

    def compose(self) -> ComposeResult:
        with Horizontal(id="header_content"):
            with Vertical(classes="header_column"):
                yield Label("RUN ID", classes="header_label")
                yield Label(self.run_id, id="run_id", classes="header_value")
            with Vertical(classes="header_column"):
                yield Label("STATUS", classes="header_label")
                yield Label(self.status, id="status", classes="header_value")
            with Vertical(classes="header_column"):
                yield Label("STATE", classes="header_label")
                yield Label(self.state, id="state", classes="header_value")
            with Vertical(classes="header_column_wide"):
                yield Label("SPEC", classes="header_label")
                yield Label(self.spec_path, id="spec_path", classes="header_value")

    def update_info(self, run: RunRecord) -> None:
        self.run_id = run.run_id
        self.status = run.status
        self.state = run.current_state
        self.spec_path = run.spec_path

        # Update classes based on status
        status_label = self.query_one("#status", Label)
        status_label.remove_class("status-success", "status-error", "status-running")
        if run.status == "completed":
            status_label.add_class("status-success")
        elif run.status == "failed":
            status_label.add_class("status-error")
        elif run.status in ("running", "pending"):
            status_label.add_class("status-running")


class StepItem(ListItem):
    """Item individual da lista de steps."""

    def __init__(self, step: RunStepRecord) -> None:
        super().__init__()
        self.step = step
        self.step_id = str(step.step_id)

    def compose(self) -> ComposeResult:
        icon = "⚪"
        if self.step.status == "completed":
            icon = "✅"
        elif self.step.status == "failed":
            icon = "❌"
        elif self.step.status == "running":
            icon = "⏳"
        elif self.step.status == "skipped":
            icon = "⏭️"

        tool = self.step.tool_name or "system"
        duration = f"{self.step.duration_ms}ms" if self.step.duration_ms else ""

        yield Label(f"{icon} {self.step.state}", classes="step_state")
        yield Label(tool, classes="step_tool")
        if duration:
            yield Label(duration, classes="step_duration")


class StepDetail(Static):
    """Painel de detalhes do step selecionado."""

    step: reactive[RunStepRecord | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Label("Select a step to view details", id="detail_placeholder")
        yield Vertical(id="detail_content", classes="hidden")

    def watch_step(self, step: RunStepRecord | None) -> None:
        if step is None:
            self.query_one("#detail_placeholder").remove_class("hidden")
            self.query_one("#detail_content").add_class("hidden")
            return

        self.query_one("#detail_placeholder").add_class("hidden")
        content = self.query_one("#detail_content")
        content.remove_class("hidden")

        # Clear previous content manually since we are not using clear() on Vertical
        for child in content.children:
            child.remove()

        # Build details
        content.mount(Label(f"Step ID: {step.step_id}", classes="detail_header"))

        content.mount(
            Horizontal(
                Label("State:", classes="detail_label"),
                Label(step.state, classes="detail_value"),
                classes="detail_row",
            )
        )

        content.mount(
            Horizontal(
                Label("Status:", classes="detail_label"),
                Label(step.status, classes="detail_value"),
                classes="detail_row",
            )
        )

        content.mount(
            Horizontal(
                Label("Tool:", classes="detail_label"),
                Label(step.tool_name or "N/A", classes="detail_value"),
                classes="detail_row",
            )
        )

        content.mount(
            Horizontal(
                Label("Duration:", classes="detail_label"),
                Label(f"{step.duration_ms or 0}ms", classes="detail_value"),
                classes="detail_row",
            )
        )

        content.mount(
            Horizontal(
                Label("Created:", classes="detail_label"),
                Label(step.created_at, classes="detail_value"),
                classes="detail_row",
            )
        )

        if step.return_code is not None:
            content.mount(
                Horizontal(
                    Label("Return Code:", classes="detail_label"),
                    Label(str(step.return_code), classes="detail_value"),
                    classes="detail_row",
                )
            )

        if step.timed_out:
            content.mount(Label("Timed Out: Yes", classes="detail_row error"))


class ArtifactExplorer(Static):
    """Explorador de artefatos da run."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="artifact_container"):
            with Vertical(id="artifact_list_container"):
                yield Label("Artifacts", classes="header_label")
                yield ListView(id="artifact_list")
            with Vertical(id="artifact_preview_container"):
                yield Label("Preview", classes="header_label")
                yield Static(id="artifact_content")

    def load_artifacts(self) -> None:
        """Carrega a lista de artefatos."""
        try:
            app: Any = self.app
            if not hasattr(app, "artifact_store"):
                return

            paths = app.artifact_store.list_artifact_paths(app.run_id)
            list_view = self.query_one("#artifact_list", ListView)
            list_view.clear()

            for path in paths:
                list_view.append(ListItem(Label(path)))

        except Exception:
            # Silently fail if not ready (e.g. during startup tests)
            pass

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        """Exibe o conteúdo do artefato selecionado."""
        if message.list_view.id != "artifact_list":
            return

        label = message.item.query_one(Label)
        path_str = str(label.renderable)  # type: ignore[attr-defined]
        self.show_artifact(path_str)

    def show_artifact(self, path_str: str) -> None:
        """Carrega e exibe o conteúdo do artefato."""
        try:
            app: Any = self.app
            if not hasattr(app, "settings"):
                return

            full_path = app.settings.artifacts_dir_resolved / path_str
            content_view = self.query_one("#artifact_content", Static)

            if not full_path.exists() or not full_path.is_file():
                content_view.update("File not found.")
                return

            # Check if likely text
            suffix = full_path.suffix.lower()
            text_extensions = {
                ".txt",
                ".md",
                ".json",
                ".yaml",
                ".yml",
                ".py",
                ".log",
                ".csv",
                ".xml",
                ".html",
                ".css",
                ".js",
            }

            if suffix in text_extensions:
                try:
                    content = full_path.read_text(encoding="utf-8", errors="replace")
                    content_view.update(content)
                except Exception as e:
                    content_view.update(f"Error reading text file: {e}")
            else:
                stat = full_path.stat()
                content_view.update(
                    f"Binary file or unsupported format.\n\n"
                    f"Path: {full_path}\n"
                    f"Size: {stat.st_size} bytes"
                )

        except Exception as e:
            self.query_one("#artifact_content", Static).update(f"Error: {e}")


class RunDashboard(App[None]):
    """Dashboard TUI Moderno para AIgnt OS."""

    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
    }

    /* Header Styling */
    RunHeader {
        height: auto;
        dock: top;
        background: $surface-darken-1;
        border-bottom: solid $primary;
        padding: 1;
    }
    #header_content {
        height: auto;
    }
    .header_column {
        width: 1fr;
        height: auto;
    }
    .header_column_wide {
        width: 3fr;
        height: auto;
    }
    .header_label {
        color: $text-muted;
        text-style: bold;
    }
    .header_value {
        color: $text;
    }
    .status-success { color: $success; }
    .status-error { color: $error; }
    .status-running { color: $warning; }

    /* Main Layout */
    TabbedContent {
        height: 1fr;
    }
    
    #steps_container, #artifact_container {
        height: 1fr;
        width: 1fr;
    }
    
    #sidebar, #artifact_list_container {
        width: 30%;
        height: 100%;
        border-right: solid $primary;
        background: $surface-darken-2;
    }
    
    #content, #artifact_preview_container {
        width: 70%;
        height: 100%;
        padding: 1 2;
        background: $surface;
    }
    
    #artifact_content {
        height: 1fr;
        overflow-y: scroll;
        border: solid $secondary;
        padding: 1;
    }

    /* Steps List */
    StepItem {
        layout: horizontal;
        height: auto;
        padding: 1;
        margin-bottom: 0;
    }
    StepItem:hover {
        background: $primary-darken-2;
    }
    ListView > ListItem.--highlight {
        background: $primary-darken-1;
        border-left: solid $secondary;
    }
    .step_state { width: 1fr; }
    .step_tool { width: 1fr; color: $text-muted; }
    .step_duration { width: auto; color: $text-disabled; }

    /* Detail View */
    .detail_header {
        text-style: bold;
        border-bottom: solid $secondary;
        margin-bottom: 1;
        color: $primary;
    }
    .detail_row {
        height: auto;
        margin-bottom: 0;
    }
    .detail_label {
        width: 15;
        color: $text-muted;
    }
    .detail_value {
        width: 1fr;
        color: $text;
    }
    .hidden {
        display: none;
    }
    .error {
        color: $error;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("enter", "show_logs", "Show Logs"),
        ("a", "show_artifacts", "Artifacts"),
        ("f", "filter_failed", "Filter Failed"),
        ("r", "filter_active", "Filter Active"),
        ("x", "filter_all", "Reset Filters"),
    ]

    def __init__(self, run_id: str, refresh_interval: float = 1.0) -> None:
        super().__init__()
        self.run_id = run_id
        self.refresh_interval = refresh_interval
        self.settings = AppSettings()
        self.repository = RunRepository(self.settings.runs_db_path_resolved)
        self.artifact_store = ArtifactStore(self.settings.artifacts_dir_resolved)

        self.run_header = RunHeader()
        self.step_list = ListView(id="step_list")
        self.step_detail = StepDetail()
        self.artifact_explorer = ArtifactExplorer()

        self.steps_count = 0
        self.current_filter: str = "all"  # all, failed, active

    def action_filter_failed(self) -> None:
        """Filter to show only failed steps."""
        self.current_filter = "failed"
        self.refresh_data()
        self.notify("Filter: Failed steps only")

    def action_filter_active(self) -> None:
        """Filter to show only active (running/pending) steps."""
        self.current_filter = "active"
        self.refresh_data()
        self.notify("Filter: Active steps only")

    def action_filter_all(self) -> None:
        """Reset filter to show all steps."""
        self.current_filter = "all"
        self.refresh_data()
        self.notify("Filter: All steps")

    def action_show_artifacts(self) -> None:
        """Switch to artifacts tab."""
        self.query_one(TabbedContent).active = "tab_artifacts"

    def action_show_logs(self) -> None:
        """Show logs for the selected step."""
        if self.step_detail.step:
            step = self.step_detail.step
            log_content = "No logs available."
            log_path: str | None = None

            paths_to_check = []
            if step.clean_output_path:
                paths_to_check.append(step.clean_output_path)
            if step.raw_output_path:
                paths_to_check.append(step.raw_output_path)

            for path_str in paths_to_check:
                try:
                    p = Path(path_str)
                    if p.exists():
                        full_content = p.read_text(encoding="utf-8", errors="replace")
                        log_content = truncate_logs(
                            full_content, self.settings.tui_log_buffer_lines
                        )
                        log_path = path_str
                        break
                except Exception as e:
                    log_content = f"Error reading log file: {e}"

            self.push_screen(
                LogViewer(
                    f"Logs: Step {step.step_id} ({step.tool_name})",
                    log_content,
                    path=log_path,
                )
            )
        else:
            self.notify("Select a step first.", severity="warning")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield self.run_header

        with TabbedContent(initial="tab_steps"):
            with TabPane("Steps", id="tab_steps"):
                with Horizontal(id="steps_container"):
                    with Vertical(id="sidebar"):
                        yield Label("Steps", classes="header_label")
                        yield self.step_list
                    with Vertical(id="content"):
                        yield self.step_detail

            with TabPane("Artifacts", id="tab_artifacts"):
                yield self.artifact_explorer

        yield Footer()

    def on_mount(self) -> None:
        self.title = f"AIgnt OS Watcher - {self.run_id}"
        self.set_interval(self.refresh_interval, self.refresh_data)
        self.refresh_data()

    def on_list_view_highlighted(self, message: ListView.Highlighted) -> None:
        if message.list_view.id == "step_list":
            if isinstance(message.item, StepItem):
                self.step_detail.step = message.item.step

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        if message.list_view.id == "step_list":
            if isinstance(message.item, StepItem):
                self.step_detail.step = message.item.step
                self.action_show_logs()

    def refresh_data(self) -> None:
        """Atualiza dados do banco."""
        try:
            # Refresh artifacts
            self.artifact_explorer.load_artifacts()

            try:
                run = self.repository.get_run(self.run_id)
                self.run_header.update_info(run)
            except Exception:
                self.notify("Run not found!", severity="error")
                return

            steps = self.repository.list_steps(self.run_id)

            # Apply filter
            filtered_steps = steps
            if self.current_filter == "failed":
                filtered_steps = [s for s in steps if s.status == "failed"]
            elif self.current_filter == "active":
                filtered_steps = [s for s in steps if s.status in ("running", "pending")]

            # Update title to reflect filter
            filter_text = ""
            if self.current_filter != "all":
                filter_text = f" [FILTER: {self.current_filter}]"
            self.title = f"AIgnt OS Watcher - {self.run_id}{filter_text}"

            # Simple diff: rebuild list if count changes or status changes
            # For MVP simplicity, verify if rebuild is needed
            # Or just rebuild if count matches but status might change?
            # Rebuilding clears selection, which is annoying.
            # Ideally we update items in place, but ListView API is list-based.
            # Let's rebuild only if count changes for now (new steps),
            # OR if last step status changed.
            # OR if filter changed (which forces rebuild)

            should_rebuild = False
            # If filtered count differs from current visible count
            if len(filtered_steps) != len(self.step_list.children):
                should_rebuild = True

            # If we haven't rebuilt yet, check if content changed
            if not should_rebuild and filtered_steps:
                # Check first and last item as heuristic
                first_item = self.step_list.children[0]
                if isinstance(first_item, StepItem):
                    if str(first_item.step.step_id) != str(filtered_steps[0].step_id):
                        should_rebuild = True

            if len(steps) != self.steps_count:
                should_rebuild = True
            elif steps and self.steps_count > 0:
                # Check if last step status changed (e.g. running -> completed)
                # In a real app we would check all, but this is a heuristic for optimization
                pass

            # Always rebuild if filter is active to ensure correctness without complex diff
            if self.current_filter != "all":
                should_rebuild = True

            # Forcing rebuild for now to ensure correctness
            should_rebuild = True

            if should_rebuild:
                self.steps_count = len(steps)

                # Preserve selection index if possible
                current_index = self.step_list.index

                self.step_list.clear()
                for step in filtered_steps:
                    self.step_list.append(StepItem(step))

                # Restore selection if valid
                if current_index is not None and current_index < len(filtered_steps):
                    self.step_list.index = current_index
                elif len(filtered_steps) > 0:
                    self.step_list.index = 0

        except Exception as e:
            self.notify(f"Error refreshing data: {e}", severity="error")

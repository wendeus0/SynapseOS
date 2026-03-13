from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Label, Static

from aignt_os.config import AppSettings
from aignt_os.persistence import RunRecord, RunRepository, RunStepRecord


class RunHeader(Static):
    """Exibe informações básicas da run no topo."""

    run_id = reactive("")
    status = reactive("loading...")
    state = reactive("loading...")
    spec_path = reactive("")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Run ID: {self.run_id}", id="run_id")
            yield Label(f"Status: {self.status}", id="status")
            yield Label(f"State:  {self.state}", id="state")
            yield Label(f"Spec:   {self.spec_path}", id="spec_path")

    def update_info(self, run: RunRecord) -> None:
        self.run_id = run.run_id
        self.status = run.status
        self.state = run.current_state
        self.spec_path = run.spec_path


class StepsTable(DataTable):
    """Tabela de steps da run."""

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_columns("State", "Status", "Tool", "Duration (ms)", "Timestamp")

    def update_steps(self, steps: list[RunStepRecord]) -> None:
        self.clear()
        for step in steps:
            self.add_row(
                step.state,
                step.status,
                step.tool_name or "-",
                str(step.duration_ms or "-"),
                step.created_at[:19],  # Truncate ISO string for display
            )


class RunDashboard(App):
    """Dashboard TUI para monitorar uma run do AIgnt OS."""

    CSS = """
    RunHeader {
        background: $primary-darken-2;
        color: $text;
        height: auto;
        padding: 1;
        border-bottom: solid $primary;
    }
    StepsTable {
        height: 1fr;
        border: solid $secondary;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, run_id: str, refresh_interval: float = 1.0) -> None:
        super().__init__()
        self.run_id = run_id
        self.refresh_interval = refresh_interval
        # Inicializa repositório. Em app real TUI, idealmente injetaria dependência
        # mas aqui instanciamos direto por conveniência do comando CLI.
        settings = AppSettings()
        self.repository = RunRepository(settings.runs_db_path)
        self.run_header = RunHeader()
        self.steps_table = StepsTable()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield self.run_header
        yield self.steps_table
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"AIgnt OS Watcher - {self.run_id}"
        self.set_interval(self.refresh_interval, self.refresh_data)
        self.refresh_data()  # First load

    def refresh_data(self) -> None:
        """Consulta o banco de dados e atualiza a interface."""
        try:
            # Em TUI síncrona, operações de I/O bloqueiam a UI.
            # Como o SQLite é local e rápido, aceitamos o bloqueio momentâneo
            # para o refresh de 1s neste MVP.
            # Futuramente mover para worker thread se necessário.
            try:
                run = self.repository.get_run(self.run_id)
                self.run_header.update_info(run)
            except Exception:
                self.notify("Run not found!", severity="error")
                return

            steps = self.repository.list_steps(self.run_id)
            self.steps_table.update_steps(steps)

        except Exception as e:
            self.notify(f"Error refreshing data: {e}", severity="error")

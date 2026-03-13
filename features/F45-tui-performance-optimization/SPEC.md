---
id: F45-tui-performance-optimization
type: feature
summary: "Optimize TUI log rendering for large outputs"
inputs:
  - Configurable TUI log buffer limit in `AppSettings`
outputs:
  - Truncated log rendering in the dashboard log viewer
  - Responsive log modal even for large persisted outputs
acceptance_criteria:
  - "Configuration `tui_log_buffer_lines` exists with default `1000`"
  - "The dashboard log viewer truncates old lines and keeps the newest lines visible"
  - "A truncation marker indicates how many lines were omitted"
  - "The log viewer can refresh from disk without reloading unchanged files"
  - "Unit tests validate truncation and refresh behavior"
non_goals:
  - Implement virtualized infinite scrolling
  - Change persisted log storage format
  - Add distributed log streaming
---

# Context

The AIgnt OS dashboard can open persisted step logs inside a TUI modal. Large logs can degrade responsiveness and force the UI to repaint far more text than the operator needs.

# Objective

Add a bounded log buffer for the dashboard viewer so the TUI remains responsive while still showing the latest output that matters to an operator.

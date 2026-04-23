"""High-level user workflows."""

from rate_allocator.workflows.analysis import summarize_and_plot
from rate_allocator.workflows.interactive_report import build_interactive_report_html

__all__ = ["summarize_and_plot", "build_interactive_report_html"]

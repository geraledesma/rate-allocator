"""Reporting data models and visualization helpers."""

from rate_allocator.reporting.summary import (
    AllocationSummary,
    InstitutionBreakdown,
    TierBreakdown,
    WealthProjection,
    summarize_allocation,
)
from rate_allocator.reporting.visuals import plot_net_interest_by_tranche_stacked

__all__ = [
    "AllocationSummary",
    "InstitutionBreakdown",
    "TierBreakdown",
    "WealthProjection",
    "summarize_allocation",
    "plot_net_interest_by_tranche_stacked",
]

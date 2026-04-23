"""Backward-compatible summary/reporting exports."""

from rate_allocator.core.finance.costs import (
    constraint_cost_over_horizon,
    tier_activation_cost,
    tier_constraint_cost_over_horizon,
)
from rate_allocator.core.finance.rates import (
    discrete_compounding_accumulation_factor,
    holding_simple_rate_from_annual,
    portfolio_value_path,
)
from rate_allocator.reporting.summary import (
    AllocationSummary,
    InstitutionBreakdown,
    TierBreakdown,
    WealthProjection,
    summarize_allocation,
)
from rate_allocator.reporting.visuals import plot_net_interest_by_tranche_stacked
from rate_allocator.workflows.analysis import summarize_and_plot

__all__ = [
    "holding_simple_rate_from_annual",
    "discrete_compounding_accumulation_factor",
    "portfolio_value_path",
    "constraint_cost_over_horizon",
    "tier_constraint_cost_over_horizon",
    "tier_activation_cost",
    "TierBreakdown",
    "InstitutionBreakdown",
    "WealthProjection",
    "AllocationSummary",
    "summarize_allocation",
    "plot_net_interest_by_tranche_stacked",
    "summarize_and_plot",
]

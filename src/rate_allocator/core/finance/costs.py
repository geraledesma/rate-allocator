"""Constraint and tier cost formulas."""

from rate_allocator.domain.models import Constraint, Tier


def constraint_cost_over_horizon(
    constraint: Constraint, horizon_years: float | None
) -> float:
    """Compute one constraint cost across the requested horizon."""
    if constraint.type != "monthly_expense":
        return constraint.cost
    months = 12.0 if horizon_years is None else 12.0 * horizon_years
    return constraint.cost * months


def tier_constraint_cost_over_horizon(tier: Tier, horizon_years: float | None) -> float:
    """Compute total active tier costs over the requested horizon."""
    return sum(
        constraint_cost_over_horizon(constraint, horizon_years)
        for constraint in tier.constraints
        if constraint.active
    )


def tier_activation_cost(
    tier: Tier, amount: float, horizon_years: float | None
) -> float:
    """Charge tier costs only when the tier receives funds."""
    if amount <= 0:
        return 0.0
    return tier_constraint_cost_over_horizon(tier, horizon_years)

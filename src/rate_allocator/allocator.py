"""Core LP-based allocator for tiered interest rates."""

import numpy as np
from scipy.optimize import linprog

from rate_allocator.models import AllocationResult, Institution


def allocate(total: float, institutions: list[Institution]) -> AllocationResult:
    """
    Find optimal allocation maximizing expected return.

    Uses LP with cumulative variables to enforce sequential tier filling.

    Parameters
    ----------
    total : float
        Total amount to allocate
    institutions : list[Institution]
        Institutions with tier definitions

    Returns
    -------
    AllocationResult
        Optimal allocation with expected return and effective rate

    Raises
    ------
    ValueError
        If total is negative or institutions list is empty
    """
    if total < 0:
        raise ValueError("Total must be non-negative")
    if not institutions:
        raise ValueError("Must provide at least one institution")

    if total == 0:
        return _empty_result(institutions)

    c, bounds, var_map = _build_objective(institutions, total)
    A_eq, b_eq = _build_budget_constraint(institutions, total, var_map)
    A_ub, b_ub = _build_monotonicity_constraints(institutions, var_map)

    result = linprog(
        c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")

    return _extract_result(result.x, institutions, var_map)


def _build_objective(
    institutions: list[Institution], total: float
) -> tuple[np.ndarray, list[tuple[float, float]], dict]:
    """Build objective coefficients and variable bounds."""
    var_map = {}
    idx = 0
    for inst in institutions:
        for t in range(len(inst.tiers)):
            var_map[(inst.name, t)] = idx
            idx += 1

    n_vars = len(var_map)
    c = np.zeros(n_vars)
    bounds = []
    big = max(total * 2, 1e15)

    for inst in institutions:
        n_tiers = len(inst.tiers)
        for t in range(n_tiers):
            var_idx = var_map[(inst.name, t)]
            rate_t = inst.tiers[t].rate
            rate_next = inst.tiers[t + 1].rate if t + 1 < n_tiers else 0.0
            c[var_idx] = -(rate_t - rate_next)

            limit = inst.tiers[t].limit
            ub = big if limit == float("inf") else limit
            bounds.append((0.0, ub))

    return c, bounds, var_map


def _build_budget_constraint(
    institutions: list[Institution], total: float, var_map: dict
) -> tuple[np.ndarray, np.ndarray]:
    """Build equality constraint: sum of final tier allocations = total."""
    n_vars = len(var_map)
    A_eq = np.zeros((1, n_vars))

    for inst in institutions:
        final_tier = len(inst.tiers) - 1
        var_idx = var_map[(inst.name, final_tier)]
        A_eq[0, var_idx] = 1.0

    b_eq = np.array([total])
    return A_eq, b_eq


def _build_monotonicity_constraints(
    institutions: list[Institution], var_map: dict
) -> tuple[np.ndarray, np.ndarray]:
    """Build inequality constraints: x_{t-1} <= x_t for sequential filling."""
    constraints = []

    for inst in institutions:
        for t in range(1, len(inst.tiers)):
            row = np.zeros(len(var_map))
            row[var_map[(inst.name, t - 1)]] = 1.0
            row[var_map[(inst.name, t)]] = -1.0
            constraints.append(row)

    if not constraints:
        return np.zeros((0, len(var_map))), np.array([])

    A_ub = np.vstack(constraints)
    b_ub = np.zeros(len(constraints))
    return A_ub, b_ub


def _extract_result(
    x: np.ndarray, institutions: list[Institution], var_map: dict
) -> AllocationResult:
    """Extract allocation result from LP solution."""
    allocations = {}
    total_return = 0.0
    total_allocated = 0.0

    for inst in institutions:
        amounts = []
        prev = 0.0
        for t in range(len(inst.tiers)):
            cumulative = x[var_map[(inst.name, t)]]
            tier_amount = max(0.0, cumulative - prev)
            amounts.append(tier_amount)
            total_return += tier_amount * inst.tiers[t].rate
            prev = cumulative

        allocations[inst.name] = amounts
        total_allocated += sum(amounts)

    effective_rate = total_return / total_allocated if total_allocated > 0 else 0.0

    return AllocationResult(
        allocations=allocations,
        total_allocated=total_allocated,
        expected_return=total_return,
        effective_rate=effective_rate,
    )


def _empty_result(institutions: list[Institution]) -> AllocationResult:
    """Return empty allocation when total is zero."""
    allocations = {inst.name: [0.0] * len(inst.tiers) for inst in institutions}
    return AllocationResult(
        allocations=allocations,
        total_allocated=0.0,
        expected_return=0.0,
        effective_rate=0.0,
    )

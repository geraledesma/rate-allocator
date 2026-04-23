"""Rate and compounding formulas used by allocator and reporting."""

import numpy as np

from rate_allocator.domain.models import AllocationResult, Institution


def holding_simple_rate_from_annual(annual_rate: float, year_fraction: float) -> float:
    """Scale annual nominal rate linearly by year fraction."""
    return annual_rate * year_fraction


def discrete_compounding_accumulation_factor(
    annual_nominal_rate: float, years: float, periods_per_year: int
) -> float:
    """Return compound factor from A = P(1 + r/n)^(n*t)."""
    if periods_per_year < 1:
        raise ValueError("periods_per_year must be at least 1")
    periods = periods_per_year * years
    return (1.0 + annual_nominal_rate / periods_per_year) ** periods


def portfolio_value_path(
    result: AllocationResult,
    institutions: list[Institution],
    *,
    max_days: int,
    periods_per_year: int = 365,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build daily compound and simple value paths from funded tiers."""
    if max_days < 0:
        raise ValueError("max_days must be non-negative")
    if periods_per_year < 1:
        raise ValueError("periods_per_year must be at least 1")
    _validate_alignment(result, institutions)

    days = np.arange(0, max_days + 1, dtype=float)
    years = days / 365.0
    compound = np.zeros_like(days)
    simple = np.zeros_like(days)

    for inst in institutions:
        for amount, tier in zip(result.allocations[inst.name], inst.tiers, strict=True):
            if amount <= 0:
                continue
            compound += amount * (1.0 + tier.rate / periods_per_year) ** (
                periods_per_year * years
            )
            simple += amount * (1.0 + tier.rate * years)

    return days, compound, simple


def _validate_alignment(
    result: AllocationResult, institutions: list[Institution]
) -> None:
    if {i.name for i in institutions} != set(result.allocations.keys()):
        raise ValueError(
            "institutions and result.allocations must have the same institution names"
        )
    by_name = {i.name: i for i in institutions}
    for name, amounts in result.allocations.items():
        n_tiers = len(by_name[name].tiers)
        if len(amounts) != n_tiers:
            raise ValueError(
                f"Institution {name!r}: {len(amounts)} allocation tiers but "
                f"{n_tiers} tier definitions"
            )

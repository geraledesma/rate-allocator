"""High-level orchestration workflows for human-facing analysis."""

import numpy as np

from rate_allocator.core.finance.costs import tier_activation_cost
from rate_allocator.core.finance.rates import (
    discrete_compounding_accumulation_factor,
    portfolio_value_path,
)
from rate_allocator.core.finance.taxes import estimated_isr_tax_over_horizon
from rate_allocator.domain.models import AllocationResult, Institution, RegulatoryRules
from rate_allocator.reporting.visuals import plot_net_interest_by_tranche_stacked


def summarize_and_plot(
    result: AllocationResult,
    institutions: list[Institution],
    total: float,
    title: str,
    *,
    horizon_years: float = 1.0,
    periods_per_year: int = 365,
    regulatory_rules: RegulatoryRules | None = None,
) -> None:
    """Print allocation summary and render portfolio charts."""
    rules = regulatory_rules or RegulatoryRules()
    print(_build_header(title, result, horizon_years, rules))
    _print_constraint_info(result, institutions)
    _print_allocation_table(
        result, institutions, horizon_years, periods_per_year, rules
    )
    _plot_allocation_charts(result, institutions, total, horizon_years)
    _plot_value_paths(result, institutions)


def _build_header(
    title: str,
    result: AllocationResult,
    horizon_years: float,
    regulatory_rules: RegulatoryRules,
) -> str:
    expected_return_real = (
        result.expected_return
        - result.total_allocated
        * regulatory_rules.inflation_proxy_annual
        * horizon_years
    )
    return (
        f"\n=== {title} ===\n"
        f"total_allocated: {result.total_allocated:,.2f}\n"
        f"expected_return_nominal: {result.expected_return:,.2f}\n"
        f"expected_return_real: {expected_return_real:,.2f}\n"
        f"effective_rate: {result.effective_rate:.2%}\n"
        f"total_expenses_paid: {result.total_expenses_paid:,.2f}\n"
        f"total_taxes_paid: {result.total_taxes_paid:,.2f}\n"
        f"total_withholding_paid: {result.total_withholding_paid:,.2f}\n"
        f"weights: {_format_weights(result.weights)}\n"
        f"allocations: {_format_allocations(result.allocations)}"
    )


def _format_weights(weights: dict[str, list[float]]) -> dict[str, list[str]]:
    return {
        name: [f"{float(weight):.1f}%" for weight in values]
        for name, values in _to_builtin(weights).items()
    }


def _format_allocations(allocations: dict[str, list[float]]) -> dict[str, list[str]]:
    return {
        name: [f"${float(amount):,.0f}" for amount in values]
        for name, values in _to_builtin(allocations).items()
    }


def _print_constraint_info(
    result: AllocationResult, institutions: list[Institution]
) -> None:
    by_name = {inst.name: inst for inst in institutions}
    info = {
        name: _to_builtin(values)
        for name, values in result.constraint_info.items()
        if name in by_name and any(tier.constraints for tier in by_name[name].tiers)
    }
    if info:
        print(f"constraint_info: {info}")


def _print_allocation_table(
    result: AllocationResult,
    institutions: list[Institution],
    horizon_years: float,
    periods_per_year: int,
    regulatory_rules: RegulatoryRules,
) -> None:
    import pandas as pd

    rows = _allocation_rows(
        result, institutions, horizon_years, periods_per_year, regulatory_rules
    )
    if not rows:
        return
    print("\nAllocation breakdown:")
    print(pd.DataFrame(rows).to_string(index=False))


def _allocation_rows(
    result: AllocationResult,
    institutions: list[Institution],
    horizon_years: float,
    periods_per_year: int,
    regulatory_rules: RegulatoryRules,
) -> list[dict[str, str | int]]:
    by_name = {inst.name: inst for inst in institutions}
    rows: list[dict[str, str | int]] = []
    for name, amounts in result.allocations.items():
        if sum(amounts) <= 0:
            continue
        inst = by_name[name]
        inst_weights = result.weights.get(name, [0.0] * len(amounts))
        rows.extend(
            _institution_rows(
                name,
                amounts,
                inst_weights,
                inst,
                horizon_years,
                periods_per_year,
                regulatory_rules,
            )
        )
    return rows


def _institution_rows(
    institution_name: str,
    amounts: list[float],
    weights: list[float],
    institution: Institution,
    horizon_years: float,
    periods_per_year: int,
    regulatory_rules: RegulatoryRules,
) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    institution_total = sum(amounts)
    gross_return_total = sum(
        amount
        * (
            discrete_compounding_accumulation_factor(
                tier.rate, horizon_years, periods_per_year
            )
            - 1.0
        )
        for amount, tier in zip(amounts, institution.tiers, strict=True)
    )
    institution_tax_total = estimated_isr_tax_over_horizon(
        institution,
        institution_total,
        gross_return_total,
        horizon_years,
        regulatory_rules,
    )
    for idx, amount in enumerate(amounts):
        if amount <= 0:
            continue
        tier = institution.tiers[idx]
        gross_return = amount * (
            discrete_compounding_accumulation_factor(
                tier.rate, horizon_years, periods_per_year
            )
            - 1.0
        )
        fee_total = tier_activation_cost(tier, amount, horizon_years)
        tax_share = (
            institution_tax_total * (amount / institution_total)
            if institution_total > 0
            else 0.0
        )
        net_nominal = gross_return - fee_total - tax_share
        net_real = (
            net_nominal
            - amount * regulatory_rules.inflation_proxy_annual * horizon_years
        )
        rows.append(
            {
                "Institution": institution_name,
                "Tier": idx + 1,
                "Amount": f"${amount:,.0f}",
                "Weight (%)": f"{weights[idx]:.2f}",
                "Rate": f"{tier.rate:.2%}",
                "Net return nominal": f"${net_nominal:,.2f}",
                "Net return real": f"${net_real:,.2f}",
            }
        )
    return rows


def _plot_allocation_charts(
    result: AllocationResult,
    institutions: list[Institution],
    total: float,
    horizon_years: float,
) -> None:
    import matplotlib.pyplot as plt

    by_institution_weight = _institution_weight_map(result)
    if not by_institution_weight:
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].pie(
        by_institution_weight.values(),
        labels=by_institution_weight.keys(),
        autopct="%1.1f%%",
        startangle=90,
    )
    axes[0].set_title(f"weights by institution ({total:,.0f} MXN)")
    plot_net_interest_by_tranche_stacked(
        axes[1], result, institutions, horizon_years=horizon_years
    )
    plt.tight_layout()
    plt.show()


def _institution_weight_map(result: AllocationResult) -> dict[str, float]:
    return {
        name: sum(weights)
        for name, weights in result.weights.items()
        if sum(result.allocations.get(name, [])) > 0
    }


def _plot_value_paths(
    result: AllocationResult, institutions: list[Institution]
) -> None:
    import matplotlib.pyplot as plt

    days, compound_values, simple_values = portfolio_value_path(
        result, institutions, max_days=365, periods_per_year=365
    )
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(days, compound_values, label="Discrete daily compounding (m=365)")
    ax.plot(days, simple_values, label="Simple linear (rate x day/365)")
    ax.set_xlabel("Calendar day")
    ax.set_ylabel("Portfolio value (MXN)")
    ax.set_title("Final allocation: compounding vs simple over 1 year")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


def _to_builtin(value: object) -> object:
    if isinstance(value, dict):
        return {k: _to_builtin(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_builtin(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_to_builtin(v) for v in value)
    if isinstance(value, np.generic):
        return value.item()
    return value

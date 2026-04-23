"""Matplotlib plotting functions for allocation reporting."""

import numpy as np

from rate_allocator.core.finance.costs import tier_activation_cost
from rate_allocator.core.finance.rates import discrete_compounding_accumulation_factor
from rate_allocator.core.finance.taxes import estimated_isr_tax_over_horizon
from rate_allocator.domain.models import AllocationResult, Institution, RegulatoryRules


def plot_net_interest_by_tranche_stacked(
    ax,
    result: AllocationResult,
    institutions: list[Institution],
    *,
    horizon_years: float = 1.0,
    regulatory_rules: RegulatoryRules | None = None,
) -> None:
    """Plot per-tranche gross interest and annualized cost bars."""
    labels, gross_vals, annualized_costs = _tranche_plot_vectors(
        result,
        institutions,
        horizon_years,
        regulatory_rules or RegulatoryRules(),
    )
    if not labels:
        _render_empty_tranche_plot(ax)
        return
    _render_tranche_bars(ax, labels, gross_vals, annualized_costs)


def _tranche_plot_vectors(
    result: AllocationResult,
    institutions: list[Institution],
    horizon_years: float,
    regulatory_rules: RegulatoryRules,
) -> tuple[list[str], list[float], list[float]]:
    labels: list[str] = []
    gross_vals: list[float] = []
    annualized_costs: list[float] = []
    year_denominator = horizon_years if horizon_years > 0 else 1.0
    for inst in institutions:
        amounts = result.allocations[inst.name]
        inst_total = sum(amounts)
        inst_gross_interest = sum(
            amount
            * (
                discrete_compounding_accumulation_factor(tier.rate, horizon_years, 365)
                - 1.0
            )
            for amount, tier in zip(amounts, inst.tiers, strict=True)
        )
        inst_tax_total = estimated_isr_tax_over_horizon(
            inst, inst_total, inst_gross_interest, horizon_years, regulatory_rules
        )
        for tier_index, (amount, tier) in enumerate(
            zip(amounts, inst.tiers, strict=True)
        ):
            if amount <= 0:
                continue
            labels.append(f"{inst.name} T{tier_index + 1}")
            gross_vals.append(amount * tier.rate)
            tax_share = (
                inst_tax_total * (amount / inst_total) if inst_total > 0 else 0.0
            )
            annualized_costs.append(
                (tier_activation_cost(tier, amount, horizon_years) + tax_share)
                / year_denominator
            )
    return labels, gross_vals, annualized_costs


def _render_empty_tranche_plot(ax) -> None:
    ax.set_title("Net interest by tranche (MXN/yr)")
    ax.text(
        0.5,
        0.5,
        "No funded tranches",
        ha="center",
        va="center",
        transform=ax.transAxes,
    )


def _render_tranche_bars(
    ax,
    labels: list[str],
    gross_vals: list[float],
    annualized_costs: list[float],
) -> None:
    x = np.arange(len(labels), dtype=float)
    bar_width = 0.38
    offset = bar_width / 2 + 0.02
    ax.bar(
        x - offset,
        gross_vals,
        width=bar_width,
        label="Gross interest (simple annual)",
        color="#2ecc71",
    )
    ax.bar(
        x + offset,
        [-cost for cost in annualized_costs],
        width=bar_width,
        label="Fees + taxes (annualized)",
        color="#e74c3c",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_title("Net interest by tranche (MXN/yr)")
    ax.set_ylabel("MXN/yr")
    ax.axhline(0.0, color="gray", linewidth=0.5)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper right", fontsize=8)

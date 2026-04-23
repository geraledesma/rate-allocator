"""Reusable interactive report helpers for notebook and future HTTP views."""

from __future__ import annotations

import base64
import html as html_mod
import io

from rate_allocator.core.finance.costs import tier_activation_cost
from rate_allocator.core.finance.rates import (
    discrete_compounding_accumulation_factor,
    portfolio_value_path,
)
from rate_allocator.core.finance.taxes import (
    estimated_isr_tax_over_horizon,
    withholding_tax_over_horizon,
)
from rate_allocator.domain.models import AllocationResult, Institution, RegulatoryRules
from rate_allocator.reporting.visuals import plot_net_interest_by_tranche_stacked


def build_interactive_report_html(
    result: AllocationResult,
    institutions: list[Institution],
    *,
    total: float,
    horizon_years: float = 1.0,
    periods_per_year: int = 365,
    regulatory_rules: RegulatoryRules | None = None,
) -> str:
    """Build the HTML fragment displayed by the interactive notebook."""
    rules = regulatory_rules or RegulatoryRules()
    raw_rows, footnote_lines, institution_totals = _build_report_rows(
        result, institutions, horizon_years, periods_per_year, rules
    )
    parts: list[str] = ['<div style="max-width:960px">']

    summary = (
        f"{total:,.0f} MXN to allocate  ·  deployed ${result.total_allocated:,.0f}  ·  "
        f"effective horizon yield {result.effective_rate:.2%}  ·  "
        f"expected return over horizon ${result.expected_return:,.2f}"
    )
    parts.append(f"<pre>{html_mod.escape(summary)}</pre>")

    if raw_rows:
        parts.extend(_rows_table_and_footnotes(raw_rows, footnote_lines))
        parts.extend(
            _charts_html(
                result,
                institutions,
                institution_totals,
                horizon_years,
                rules,
            )
        )

    parts.append("</div>")
    return "\n".join(parts)


def _build_report_rows(
    result: AllocationResult,
    institutions: list[Institution],
    horizon_years: float,
    periods_per_year: int,
    regulatory_rules: RegulatoryRules,
) -> tuple[list[dict], list[tuple[str, str, float]], list[tuple[str, float]]]:
    footnote_map: dict[tuple[str, str, float], int] = {}
    footnote_lines: list[tuple[str, str, float]] = []
    raw_rows: list[dict] = []
    institution_totals: list[tuple[str, float]] = []

    for inst_name, amounts in result.allocations.items():
        inst = next(i for i in institutions if i.name == inst_name)
        inst_total = sum(amounts)
        if inst_total <= 0:
            continue

        institution_totals.append((inst_name, inst_total))
        gross_interest_total = sum(
            amount
            * (
                discrete_compounding_accumulation_factor(
                    tier.rate, horizon_years, periods_per_year
                )
                - 1.0
            )
            for amount, tier in zip(amounts, inst.tiers, strict=True)
        )
        institution_tax_total = estimated_isr_tax_over_horizon(
            inst, inst_total, gross_interest_total, horizon_years, regulatory_rules
        )
        institution_withholding_total = withholding_tax_over_horizon(
            inst, inst_total, horizon_years, regulatory_rules
        )
        for tier_idx, amount in enumerate(amounts):
            if amount <= 0:
                continue
            tier = inst.tiers[tier_idx]
            gross_interest = amount * (
                discrete_compounding_accumulation_factor(
                    tier.rate, horizon_years, periods_per_year
                )
                - 1.0
            )
            active_costs = [
                info
                for info in result.constraint_info.get(inst_name, [])
                if info.get("tier_idx") == tier_idx and info.get("activated")
            ]
            fee_total = tier_activation_cost(tier, amount, horizon_years)
            tax_share = (
                institution_tax_total * (amount / inst_total) if inst_total > 0 else 0.0
            )
            withholding_share = (
                institution_withholding_total * (amount / inst_total)
                if inst_total > 0
                else 0.0
            )
            cost_total = fee_total + tax_share
            net_return_nominal = gross_interest - cost_total
            inflation_drag = (
                amount * regulatory_rules.inflation_proxy_annual * horizon_years
            )
            net_return_real = net_return_nominal - inflation_drag
            tags = _assign_footnotes(
                active_costs, inst_name, footnote_map, footnote_lines
            )
            base_cost_cell = (
                " + ".join(
                    (f"[{tag}] ${_constraint_horizon_total(info, horizon_years):,.2f}")
                    for tag, info in zip(tags, active_costs)
                )
                if active_costs
                else "—"
            )
            tax_cell = f"ISR ${tax_share:,.2f}" if tax_share > 0 else None
            cost_cell = (
                f"{base_cost_cell} + {tax_cell}"
                if tax_cell and base_cost_cell != "—"
                else tax_cell or base_cost_cell
            )
            raw_rows.append(
                {
                    "inst": inst_name,
                    "tier": tier_idx + 1,
                    "principal": amount,
                    "nominal_annual_rate": tier.rate,
                    "gross_horizon_return": gross_interest,
                    "fixed_costs": cost_cell,
                    "tax_horizon_total": tax_share,
                    "withholding_horizon_total": withholding_share,
                    "fees_horizon_total": cost_total,
                    "net_horizon_return_nominal": net_return_nominal,
                    "net_horizon_return_real": net_return_real,
                }
            )
    return raw_rows, footnote_lines, institution_totals


def _assign_footnotes(
    active_costs: list[dict],
    inst_name: str,
    footnote_map: dict[tuple[str, str, float], int],
    footnote_lines: list[tuple[str, str, float]],
) -> list[int]:
    tags: list[int] = []
    for info in active_costs:
        key = (inst_name, info["type"], float(info["cost"]))
        if key not in footnote_map:
            footnote_map[key] = len(footnote_lines) + 1
            footnote_lines.append(key)
        tags.append(footnote_map[key])
    return tags


def _rows_table_and_footnotes(
    raw_rows: list[dict], footnote_lines: list[tuple[str, str, float]]
) -> list[str]:
    try:
        import pandas as pd
    except ModuleNotFoundError:
        return ["<p>Pandas is required to render the tabular report output.</p>"]

    df = pd.DataFrame(
        {
            "Institution": [r["inst"] for r in raw_rows],
            "Tier": [r["tier"] for r in raw_rows],
            "Principal": [f"${r['principal']:,.0f}" for r in raw_rows],
            "Nominal rate": [f"{r['nominal_annual_rate']:.2%}" for r in raw_rows],
            "Gross return (compound)": [
                f"${r['gross_horizon_return']:,.2f}" for r in raw_rows
            ],
            "Fees (constraints + tax, horizon)": [r["fixed_costs"] for r in raw_rows],
            "Withholding (report-only)": [
                f"${r['withholding_horizon_total']:,.2f}" for r in raw_rows
            ],
            "Net return (nominal)": [
                f"${r['net_horizon_return_nominal']:,.2f}" for r in raw_rows
            ],
            "Net return (real)": [
                f"${r['net_horizon_return_real']:,.2f}" for r in raw_rows
            ],
        }
    )

    parts = [
        "<h4>By tranche (horizon return, MXN except rate)</h4>",
        df.to_html(index=False, escape=True),
    ]
    parts.append("<h4>Fee notes ([n] in Fees column)</h4><pre>")
    if footnote_lines:
        for idx, key in enumerate(footnote_lines, start=1):
            inst_name, ctype, cost = key
            if ctype == "monthly_expense":
                line = (
                    f"  [{idx}] {inst_name} monthly_expense ${cost:,.2f}/month "
                    f"(charged as horizon total in net return)"
                )
            else:
                line = (
                    f"  [{idx}] {inst_name} {ctype} ${cost:,.2f} (one-time when funded)"
                )
            parts.append(html_mod.escape(line))
    else:
        parts.append("  — No fee rows; net equals gross for each tranche.")
    parts.append(
        "  Taxes in Fees are estimated annual ISR over real interest; withholding is reported separately."
    )
    parts.append("</pre>")
    return parts


def _charts_html(
    result: AllocationResult,
    institutions: list[Institution],
    institution_totals: list[tuple[str, float]],
    horizon_years: float,
    regulatory_rules: RegulatoryRules,
) -> list[str]:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return ["<p>Matplotlib is required to render charts.</p>"]

    names = [name for name, _amount in institution_totals]
    values = [amount for _name, amount in institution_totals]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10, 4),
        gridspec_kw={"width_ratios": [1, 1], "wspace": 0.25},
    )
    axes[0].pie(values, labels=names, autopct="%1.1f%%", startangle=90)
    axes[0].set_title("Principal by institution")
    plot_net_interest_by_tranche_stacked(
        axes[1],
        result,
        institutions,
        horizon_years=horizon_years,
        regulatory_rules=regulatory_rules,
    )
    plt.tight_layout()
    b64a = _figure_to_png_b64(fig)

    days, compound_vals, simple_vals = portfolio_value_path(
        result, institutions, max_days=365, periods_per_year=365
    )
    fig2, ax = plt.subplots(figsize=(10, 4))
    ax.plot(days, compound_vals, label="Discrete daily compounding (m=365)")
    ax.plot(days, simple_vals, label="Simple linear (rate × day/365)")
    ax.set_xlabel("Calendar day")
    ax.set_ylabel("Portfolio value (MXN)")
    ax.set_title("Final allocation: compounding vs simple over 1 year")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    b64b = _figure_to_png_b64(fig2)
    return [
        f'<h4>Charts</h4><p><img src="data:image/png;base64,{b64a}" alt="principal-net"/></p>',
        f'<p><img src="data:image/png;base64,{b64b}" alt="path"/></p>',
    ]


def _constraint_horizon_total(info: dict, horizon_years: float) -> float:
    if info.get("type") == "monthly_expense":
        return float(info["cost"]) * 12.0 * horizon_years
    return float(info["cost"])


def _figure_to_png_b64(fig, dpi: int = 110) -> str:
    import matplotlib.pyplot as plt

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return base64.standard_b64encode(buf.getvalue()).decode("ascii")

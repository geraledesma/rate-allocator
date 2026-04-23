"""Tax cost formulas by institution type."""

from rate_allocator.domain.models import Institution, RegulatoryRules


def estimated_isr_tax_over_horizon(
    institution: Institution,
    principal_amount: float,
    nominal_interest_gain: float,
    horizon_years: float | None,
    rules: RegulatoryRules,
) -> float:
    """Estimate annual ISR tax using real-interest base A * (B - C)."""
    if principal_amount <= 0 or nominal_interest_gain <= 0:
        return 0.0
    years = 1.0 if horizon_years is None else horizon_years
    inflation_drag = principal_amount * rules.inflation_proxy_annual * years

    if institution.institution_type == "banco":
        real_interest_base = max(0.0, nominal_interest_gain - inflation_drag)
        return real_interest_base * rules.real_interest_isr_rate_annual

    if institution.institution_type == "sofipo":
        taxable_balance = max(
            0.0, principal_amount - rules.sofipo_exempt_balance_limit_mxn
        )
        if taxable_balance <= 0:
            return 0.0
        taxable_gain = nominal_interest_gain * (taxable_balance / principal_amount)
        taxable_inflation_drag = taxable_balance * rules.inflation_proxy_annual * years
        real_interest_base = max(0.0, taxable_gain - taxable_inflation_drag)
        return real_interest_base * rules.sofipo_excess_isr_rate_annual

    return 0.0


def withholding_tax_over_horizon(
    institution: Institution,
    principal_amount: float,
    horizon_years: float | None,
    rules: RegulatoryRules,
) -> float:
    """Compute bank withholding as report-only cash-flow."""
    if institution.institution_type != "banco" or principal_amount <= 0:
        return 0.0
    years = 1.0 if horizon_years is None else horizon_years
    return principal_amount * rules.bank_isr_withholding_rate_annual * years

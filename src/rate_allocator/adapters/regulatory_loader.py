"""YAML parser for regulatory policy rules."""

from pathlib import Path

import yaml

from rate_allocator.domain.models import RegulatoryRules


def load_regulatory_rules_from_yaml(path: str | Path) -> RegulatoryRules:
    """Load regulatory rules from YAML file with strict validation."""
    with Path(path).open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    insurance = data.get("insurance", {})
    tax = data.get("tax", {})
    return RegulatoryRules(
        country=str(data.get("country", "MX")),
        effective_from=str(data.get("effective_from", "2026-01-01")),
        bank_insurance_limit_mxn=float(insurance["bank_insurance_limit_mxn"]),
        sofipo_insurance_limit_mxn=float(insurance["sofipo_insurance_limit_mxn"]),
        bank_isr_withholding_rate_annual=float(tax["bank_isr_withholding_rate_annual"]),
        real_interest_isr_rate_annual=float(
            tax.get(
                "real_interest_isr_rate_annual", tax["bank_isr_withholding_rate_annual"]
            )
        ),
        inflation_proxy_annual=float(tax["inflation_proxy_annual"]),
        sofipo_exempt_balance_limit_mxn=float(tax["sofipo_exempt_balance_limit_mxn"]),
        sofipo_excess_isr_rate_annual=float(
            tax.get(
                "sofipo_excess_isr_rate_annual",
                tax.get(
                    "real_interest_isr_rate_annual",
                    tax["bank_isr_withholding_rate_annual"],
                ),
            )
        ),
    )

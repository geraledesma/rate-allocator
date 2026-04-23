"""Core domain models for the allocator."""

from dataclasses import dataclass, field
from typing import Literal

InstitutionType = Literal["banco", "sofipo", "none"]


@dataclass(frozen=True)
class RegulatoryRules:
    """Policy inputs that can be updated without changing code."""

    country: str = "MX"
    effective_from: str = "2026-01-01"
    bank_insurance_limit_mxn: float = 3_300_000.0
    sofipo_insurance_limit_mxn: float = 208_000.0
    bank_isr_withholding_rate_annual: float = 0.009
    real_interest_isr_rate_annual: float = 0.009
    inflation_proxy_annual: float = 0.0421
    sofipo_exempt_balance_limit_mxn: float = 213_973.0
    sofipo_excess_isr_rate_annual: float = 0.009

    def __post_init__(self):
        if self.bank_insurance_limit_mxn < 0:
            raise ValueError("bank_insurance_limit_mxn must be non-negative")
        if self.sofipo_insurance_limit_mxn < 0:
            raise ValueError("sofipo_insurance_limit_mxn must be non-negative")
        if not (0 <= self.bank_isr_withholding_rate_annual <= 1):
            raise ValueError("bank_isr_withholding_rate_annual must be between 0 and 1")
        if not (0 <= self.real_interest_isr_rate_annual <= 1):
            raise ValueError("real_interest_isr_rate_annual must be between 0 and 1")
        if self.inflation_proxy_annual < 0:
            raise ValueError("inflation_proxy_annual must be non-negative")
        if self.sofipo_exempt_balance_limit_mxn < 0:
            raise ValueError("sofipo_exempt_balance_limit_mxn must be non-negative")
        if not (0 <= self.sofipo_excess_isr_rate_annual <= 1):
            raise ValueError("sofipo_excess_isr_rate_annual must be between 0 and 1")


@dataclass(frozen=True)
class Constraint:
    """An optional condition attached to a tier."""

    type: str
    cost: float = 0.0
    benefit: str | None = None
    condition_value: float | None = None
    active: bool = True
    constraint_condition: str | None = None
    benefit_condition: str | None = None

    def __post_init__(self):
        if not self.type:
            raise ValueError("Constraint type must be a non-empty string")
        if self.cost < 0:
            raise ValueError("Constraint cost must be non-negative")


@dataclass(frozen=True)
class Tier:
    """A rate tier with cumulative limit and interest rate."""

    limit: float
    rate: float
    constraints: tuple[Constraint, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if self.limit <= 0 and self.limit != float("inf"):
            raise ValueError("Tier limit must be positive or inf")
        if not (0 <= self.rate <= 1):
            raise ValueError("Rate must be between 0 and 1")
        if not isinstance(self.constraints, tuple):
            raise ValueError("Tier constraints must be a tuple")


@dataclass(frozen=True)
class Institution:
    """A financial institution with tiered interest rates."""

    name: str
    tiers: tuple[Tier, ...]
    institution_type: InstitutionType = "none"
    protection_limit: float | None = None

    def __post_init__(self):
        if not self.tiers:
            raise ValueError("Institution must have at least one tier")
        limits = [t.limit for t in self.tiers]
        if limits != sorted(limits):
            raise ValueError("Tier limits must be in ascending order")
        if self.institution_type not in {"banco", "sofipo", "none"}:
            raise ValueError("institution_type must be banco, sofipo, or none")
        if self.protection_limit is not None and self.protection_limit < 0:
            raise ValueError("protection_limit must be non-negative when provided")

    @property
    def effective_protection_limit(self) -> float | None:
        """Resolve explicit or default protection cap by institution type."""
        if self.protection_limit is not None:
            return self.protection_limit
        if self.institution_type == "banco":
            return 3_200_000.0
        if self.institution_type == "sofipo":
            return 200_000.0
        return None

    def protection_limit_for(self, rules: RegulatoryRules) -> float | None:
        """Resolve effective protection cap using configurable policy rules."""
        if self.protection_limit is not None:
            return self.protection_limit
        if self.institution_type == "banco":
            return rules.bank_insurance_limit_mxn
        if self.institution_type == "sofipo":
            return rules.sofipo_insurance_limit_mxn
        return None


@dataclass
class AllocationResult:
    """Result of optimal allocation."""

    weights: dict[str, list[float]]
    allocations: dict[str, list[float]]
    total_allocated: float
    expected_return: float
    effective_rate: float
    total_expenses_paid: float = 0.0
    total_taxes_paid: float = 0.0
    total_withholding_paid: float = 0.0
    constraint_info: dict[str, list[dict]] = field(default_factory=dict)

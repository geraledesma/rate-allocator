"""Domain models for the allocator."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tier:
    """A rate tier with cumulative limit and interest rate."""
    limit: float
    rate: float

    def __post_init__(self):
        if self.limit <= 0 and self.limit != float("inf"):
            raise ValueError("Tier limit must be positive or inf")
        if not (0 <= self.rate <= 1):
            raise ValueError("Rate must be between 0 and 1")


@dataclass(frozen=True)
class Institution:
    """A financial institution with tiered interest rates."""
    name: str
    tiers: tuple[Tier, ...]

    def __post_init__(self):
        if not self.tiers:
            raise ValueError("Institution must have at least one tier")
        limits = [t.limit for t in self.tiers]
        if limits != sorted(limits):
            raise ValueError("Tier limits must be in ascending order")


@dataclass
class AllocationResult:
    """Result of optimal allocation."""
    allocations: dict[str, list[float]]  # {institution_name: [tier_amounts, ...]}
    total_allocated: float
    expected_return: float
    effective_rate: float

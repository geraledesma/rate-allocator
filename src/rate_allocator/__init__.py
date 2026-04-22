"""Rate Allocator - Optimal cash allocation for tiered interest rates."""

from rate_allocator.allocator import allocate
from rate_allocator.models import AllocationResult, Institution, Tier

__all__ = ["allocate", "Institution", "Tier", "AllocationResult"]

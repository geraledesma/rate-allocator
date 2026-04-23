"""Input/output adapters."""

from rate_allocator.adapters.yaml_loader import (
    load_institutions_from_yaml,
    load_institutions_with_overrides,
)

__all__ = [
    "load_institutions_from_yaml",
    "load_institutions_with_overrides",
]

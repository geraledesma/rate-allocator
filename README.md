# Rate Allocator

Optimal cash allocation across SOFIPOs and Mexican banks with tiered interest rates.

## The Problem

Given:
- A total amount of cash to invest
- A list of financial institutions, each offering different interest rates for different deposit tiers
- Tier limits (e.g., "first 25,000 MXN at 15%, next 225,000 at 12%, rest at 10%")
- Sequential tier access (must fill lower tiers before accessing higher ones)

Find:
- The allocation that maximizes expected return while respecting all constraints

## Quick Start

```python
from rate_allocator import allocate, Institution, Tier

institutions = [
    Institution(
        name="Nu",
        tiers=(
            Tier(limit=25_000, rate=0.15),
            Tier(limit=250_000, rate=0.12),
            Tier(limit=float("inf"), rate=0.10),
        ),
    ),
    Institution(
        name="Mercado Pago",
        tiers=(
            Tier(limit=23_000, rate=0.14),
            Tier(limit=float("inf"), rate=0.10),
        ),
    ),
]

result = allocate(total=100_000, institutions=institutions)
print(f"Expected return: {result.expected_return:,.2f}")
print(f"Effective rate: {result.effective_rate:.2%}")
```

## Installation

```bash
pip install -e .
```

## Running Tests

```bash
pytest tests/
```

## How It Works

The allocator uses linear programming (scipy.optimize.linprog) with:
- **Variables**: Cumulative amount per tier per institution
- **Objective**: Maximize total interest earned
- **Constraints**:
  - Budget: All money allocated
  - Limits: Respect tier caps
  - Monotonicity: Sequential tier filling

See `docs/assumptions.md` for detailed model specifications.

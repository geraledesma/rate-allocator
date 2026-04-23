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

## Interactive demo (Streamlit)

Same logic as `notebooks/demo_ipywidgets.ipynb`: bundled `data/sample1.yaml`, institution multiselect, total and **horizon** sliders, HTML report with charts.

```bash
pip install -e ".[streamlit]"
streamlit run streamlit_app.py
```

**Source repository:** [github.com/geraledesma/rate-allocator](https://github.com/geraledesma/rate-allocator)

### Publish on Streamlit Community Cloud (one-time)

1. Open [Streamlit Community Cloud](https://streamlit.io/cloud) and sign in with GitHub.
2. **New app** → pick repository **`geraledesma/rate-allocator`**, branch **`main`**, main file **`streamlit_app.py`**.
3. Leave **App URL** as default or customize; wait for the build to finish (uses root [`requirements.txt`](requirements.txt)).
4. Copy the public app URL from the Cloud dashboard and replace the line below (then commit and push this README).

**Live demo:** *(paste your `https://….streamlit.app` URL here after deploy)*

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

## Notebook And HTTP Readiness

The notebook UI now delegates result rendering to `rate_allocator.workflows.interactive_report`.
That workflow takes `AllocationResult + institutions + total` and returns an HTML fragment that
contains summary, tranche table, fee notes, and chart images.

This separation makes HTTP mounting feasible without notebook-specific code:

- **Streamlit:** `streamlit_app.py` calls `allocate` and `build_interactive_report_html` (see above).
- API route: compute `allocate(...)`, then return JSON plus optional report HTML.
- Server-rendered page: compute `allocate(...)`, then inject report HTML in a template.

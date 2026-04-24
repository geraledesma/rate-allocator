# Rate Allocator — ready for development

Function-first layout: domain and finance helpers stay testable; the solver composes them.

## Current structure

```
src/rate_allocator/
├── __init__.py          # Public exports
├── allocator.py         # Shim → core.optimizer.solve.allocate
├── models.py            # Shim → domain.models
├── summary.py           # Shim → reporting + workflows
├── io.py                # Shim → adapters (YAML, regulatory)
├── domain/
│   └── models.py        # Institution, Tier, Constraint, AllocationResult, RegulatoryRules
├── adapters/
│   ├── yaml_loader.py
│   └── regulatory_loader.py
├── core/
│   ├── finance/
│   │   ├── rates.py
│   │   ├── costs.py
│   │   └── taxes.py
│   └── optimizer/
│       └── solve.py     # allocate()
├── reporting/
│   ├── summary.py
│   └── visuals.py
└── workflows/
    ├── analysis.py
    └── interactive_report.py   # build_interactive_report_html
```

## Data and examples

- `data/sample1.yaml`, `sample2.yaml`, `sample3.yaml`, `regulatory_rules.mx.yaml`
- `notebooks/demo.ipynb`, `notebooks/demo_ipywidgets_en.ipynb`, `notebooks/demo_ipywidgets_es.ipynb`
- `streamlit_app.py` — browser demo (Streamlit Community Cloud–ready)

## Quick commands

```bash
cd /path/to/rate-allocator
pytest tests/ -v
```

```bash
pip install -e ".[streamlit]"
streamlit run streamlit_app.py
```

## Transition note

Compatibility modules (`rate_allocator.io`, `rate_allocator.summary`, `rate_allocator.models`, `rate_allocator.allocator`) remain for older import paths; prefer the package layout above for new code.

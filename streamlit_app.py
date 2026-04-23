"""Streamlit demo: mirrors notebooks/demo_ipywidgets.ipynb (YAML → allocate → HTML report)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from pathlib import Path

import streamlit as st

from rate_allocator import allocate, build_interactive_report_html
from rate_allocator.adapters.yaml_loader import load_institutions_with_overrides

REPO_ROOT = Path(__file__).resolve().parent
DATA_FILE = REPO_ROOT / "data" / "sample1.yaml"


def _brief_constraints_label(inst) -> str:
    parts = []
    for tier in inst.tiers:
        for c in tier.constraints:
            parts.append(f"{c.type} ${c.cost:.2f}")
    return ", ".join(parts) if parts else "no modeled fees"


@st.cache_data
def _load_base_institutions():
    return load_institutions_with_overrides(str(DATA_FILE), {})


def main():
    st.set_page_config(page_title="Rate Allocator demo", layout="wide")
    st.title("Rate Allocator — interactive demo")
    st.caption(
        "Pick institutions and total in MXN. Rates and fees come from bundled `data/sample1.yaml`. "
        "Horizon drives compound horizon return and fee modeling in the report."
    )

    base_institutions = _load_base_institutions()
    all_names = [inst.name for inst in base_institutions]
    hints = {inst.name: _brief_constraints_label(inst) for inst in base_institutions}

    with st.sidebar:
        selected = st.multiselect(
            "Institutions to include",
            options=all_names,
            default=all_names,
            format_func=lambda n: f"{n} ({hints[n]})",
        )
        total = st.slider(
            "Total (MXN)",
            min_value=0,
            max_value=1_200_000,
            value=100_000,
            step=1_000,
        )
        horizon_years = st.slider(
            "Horizon (years)",
            min_value=0.25,
            max_value=5.0,
            value=1.0,
            step=0.25,
        )

    if not selected:
        st.info("Select at least one institution.")
        return

    all_institutions = load_institutions_with_overrides(str(DATA_FILE), {})
    institutions = [inst for inst in all_institutions if inst.name in selected]

    result = allocate(
        total=total,
        institutions=institutions,
        horizon_years=horizon_years,
        periods_per_year=365,
    )
    html_fragment = build_interactive_report_html(
        result,
        institutions,
        total=total,
        horizon_years=horizon_years,
        periods_per_year=365,
    )
    st.markdown(html_fragment, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

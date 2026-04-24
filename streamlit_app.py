"""Streamlit demo: mirrors notebooks/demo_ipywidgets_es.ipynb (allocate → HTML report, UI in Spanish)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from pathlib import Path

import streamlit as st

from rate_allocator import allocate, build_interactive_report_html
from rate_allocator.adapters.yaml_loader import load_institutions_with_overrides

REPO_ROOT = Path(__file__).resolve().parent
DATA_FILE = REPO_ROOT / "data" / "sample1.yaml"

TOTAL_MIN = 0
TOTAL_MAX = 1_200_000
TOTAL_DEFAULT = 100_000

STRINGS = {
    "page_title": "Rate Allocator",
    "title": "Rate Allocator: demo interactivo",
    "caption": (
        "Elige instituciones y el total en MXN (deslizador o campo numérico, pasos de 100). "
        "Las tasas y comisiones salen de los datos de ejemplo incluidos en el proyecto. "
        "El horizonte en años ajusta el compuesto al plazo y el modelado de comisiones en el informe."
    ),
    "institutions": "Instituciones a incluir",
    "total_slider": "Total (MXN):",
    "total_number": "Mismo total (escribe o ±100):",
    "horizon": "Horizonte (años)",
    "empty": "Selecciona al menos una institución.",
    "no_fees": "sin comisiones modeladas",
}


def _brief_constraints_label(inst) -> str:
    parts = []
    for tier in inst.tiers:
        for c in tier.constraints:
            parts.append(f"{c.type} ${c.cost:.2f}")
    return ", ".join(parts) if parts else STRINGS["no_fees"]


@st.cache_data
def _load_base_institutions():
    return load_institutions_with_overrides(str(DATA_FILE), {})


def _sync_total_from_slider() -> None:
    st.session_state.total_mxn = int(st.session_state._total_slider)


def _sync_total_from_number() -> None:
    st.session_state.total_mxn = int(st.session_state._total_num)


def main() -> None:
    st.set_page_config(page_title=STRINGS["page_title"], layout="wide")

    if "total_mxn" not in st.session_state:
        st.session_state.total_mxn = TOTAL_DEFAULT

    t = STRINGS

    st.title(t["title"])
    st.caption(t["caption"])

    base_institutions = _load_base_institutions()
    all_names = [inst.name for inst in base_institutions]
    hints = {inst.name: _brief_constraints_label(inst) for inst in base_institutions}

    total_value = max(TOTAL_MIN, min(TOTAL_MAX, int(st.session_state.total_mxn)))

    with st.sidebar:
        def _institution_option_label(n: str) -> str:
            hint = hints[n]
            return n if hint == t["no_fees"] else f"{n} ({hint})"

        selected = st.multiselect(
            t["institutions"],
            options=all_names,
            default=all_names,
            format_func=_institution_option_label,
        )
        st.slider(
            t["total_slider"],
            min_value=TOTAL_MIN,
            max_value=TOTAL_MAX,
            value=total_value,
            step=100,
            key="_total_slider",
            on_change=_sync_total_from_slider,
        )
        st.number_input(
            t["total_number"],
            min_value=TOTAL_MIN,
            max_value=TOTAL_MAX,
            value=total_value,
            step=100,
            key="_total_num",
            on_change=_sync_total_from_number,
        )
        horizon_years = st.slider(
            t["horizon"],
            min_value=0.25,
            max_value=5.0,
            value=1.0,
            step=0.25,
        )

    total = max(TOTAL_MIN, min(TOTAL_MAX, int(st.session_state.total_mxn)))

    if not selected:
        st.info(t["empty"])
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
        locale="es",
    )
    st.markdown(html_fragment, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

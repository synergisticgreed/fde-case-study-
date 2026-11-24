"""RideOps Ticket Helper - Streamlit entry point.

Run:  streamlit run app.py
This file only wires pages together:
  rideops/  -> data, checklist logic, metrics (no UI)
  ui/       -> one module per page; all on-screen words live in ui/config.py
"""
import pandas as pd
import streamlit as st

from rideops.data import load_tickets
from ui import check, home, progress, why
from ui.components import NAV_KEY
from ui.config import APP_TITLE, PAGES

st.set_page_config(page_title="RideOps Ticket Helper", page_icon="🚦", layout="wide",
                   initial_sidebar_state="collapsed")

RENDER = {"home": home.render, "check": check.render, "progress": progress.render, "why": why.render}


@st.cache_data
def data() -> pd.DataFrame:
    """Load the ticket file once and reuse it on every click."""
    return load_tickets()


def main() -> None:
    st.title(APP_TITLE)
    st.session_state.setdefault(NAV_KEY, PAGES["home"])
    # Top navigation; a button elsewhere can switch pages by changing st.session_state[NAV_KEY].
    choice = st.radio("Go to", list(PAGES.values()), key=NAV_KEY, horizontal=True,
                      label_visibility="collapsed")
    st.divider()
    page = next(k for k, v in PAGES.items() if v == choice)
    RENDER[page](data())


if __name__ == "__main__":
    main()

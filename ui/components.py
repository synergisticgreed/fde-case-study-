"""Small reusable widgets and helpers shared by the pages."""
import pandas as pd
import streamlit as st

from rideops.triage import GateResult

from .config import OUTCOME_LABELS, PAGES, VERDICTS

ALERT = {"warning": st.warning, "info": st.info, "success": st.success}
NAV_KEY = "page"  # session-state key holding the current page label


def go_to(page: str) -> None:
    """Switch the top navigation to another page (use inside button callbacks)."""
    st.session_state[NAV_KEY] = PAGES[page]


def verdict_box(r: GateResult) -> None:
    """The big coloured 'what should I do' box."""
    v = VERDICTS[r.verdict]
    ALERT[v["kind"]](f"### {v['icon']} {v['title']}\n{v['text']}")


def verdict_badge(r: GateResult) -> str:
    """One-line version of the verdict, for compact cards."""
    v = VERDICTS[r.verdict]
    return f"{v['icon']} **{v['title']}**"


def fix_rate_sentence(r: GateResult) -> str:
    out_of_10 = round(r.fix_rate * 10)
    return f"In the past, engineering fixed this kind of problem about **{out_of_10} out of 10** times."


def outcomes_chart(r: GateResult) -> None:
    """Bar chart of what happened to past tickets about the same problem."""
    if not r.outcomes:
        st.caption("No past tickets about this exact problem, so the category average is used.")
        return
    s = pd.Series(r.outcomes).rename(index=OUTCOME_LABELS).sort_values()
    st.bar_chart(s.rename("past tickets"), horizontal=True, height=200)

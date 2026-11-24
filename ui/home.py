"""Page: Start here. What the tool is, a step-by-step example, and a button to try it."""
import pandas as pd
import streamlit as st

from rideops.data import SNAPSHOT
from rideops.playbooks import playbook
from rideops.triage import assess

from .components import verdict_badge
from .config import EXAMPLES, GLOSSARY, HOME_INTRO, HOW_TO_USE, STAGES
from .picker import load_example


def _problem_numbers(df: pd.DataFrame) -> None:
    """Three headline facts, computed from the data."""
    esc = df[df["escalated"]]
    a, b, c = st.columns(3)
    a.metric("Tickets sent to engineering", f"{len(esc) / len(df):.0%}", help=f"{len(esc)} of {len(df)}")
    b.metric("…of those, sent back unfixed", f"{esc['bounced'].mean():.0%}")
    c.metric("Typical wait: solved by support vs engineering",
             f"{df.loc[~df['escalated'], 'resolution_h'].median() / 24:.1f} → {esc['resolution_h'].median() / 24:.1f} days")


def _example(df: pd.DataFrame) -> None:
    """Play one example through the three stages and show what the tool says at each."""
    titles = [e["title"] for e in EXAMPLES]
    ex = EXAMPLES[titles.index(st.radio("Choose an example", titles, horizontal=True))]
    pb = playbook(ex["category"])
    st.markdown(f"**The situation:** {ex['story']}")

    for col, (name, did, checks_on, info_on) in zip(st.columns(len(STAGES)), STAGES):
        r = assess(df, ex["category"], ex["description"], SNAPSHOT,
                   set(pb["required"]) if info_on else set(), set(pb["l1_checks"]) if checks_on else set())
        with col.container(border=True):
            st.markdown(f"**{name}**")
            st.caption(did)
            st.markdown("The tool says:  \n" + verdict_badge(r))
    st.success(f"**Lesson:** {ex['lesson']}")
    st.button("▶️ Try this example yourself", type="primary", on_click=load_example, args=(ex,))


def render(df: pd.DataFrame) -> None:
    st.header("👋 Welcome")
    st.markdown(HOME_INTRO)

    st.subheader("😟 The problem in 3 numbers")
    _problem_numbers(df)

    st.subheader("🧭 What's in this app")
    for col, (page, text) in zip(st.columns(len(HOW_TO_USE)), HOW_TO_USE):
        with col.container(border=True):
            st.markdown(f"**{page}**")
            st.caption(text)

    st.subheader("▶️ See it work: one ticket, step by step")
    _example(df)

    with st.expander("📖 Words used in this app"):
        st.table(pd.Series(GLOSSARY, name="meaning"))

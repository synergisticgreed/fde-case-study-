"""Page: Why we built this. Three findings in plain words, then a what-if."""
import pandas as pd
import streamlit as st

from rideops.metrics import simulate_backlog
from rideops.triage import bounce_breakdown

from .config import OUTCOME_LABELS, WHATIF_DEFAULT


def render(df: pd.DataFrame) -> None:
    st.header("💡 Why we built this")
    esc = df[df["escalated"]]
    hours_share = esc["resolution_h"].sum() / df["resolution_h"].sum()

    st.subheader("1 · Tickets sent to engineering cause most of the waiting")
    st.markdown(f"They are only **{len(esc) / len(df):.0%}** of tickets but make up **{hours_share:.0%}** "
                "of all the time tickets stay open.")

    st.subheader("2 · More than half come back unfixed")
    st.markdown(f"**{esc['bounced'].sum()} of {len(esc)}** escalations were sent back. Here's why:")
    reasons = esc.loc[esc["bounced"], "eng_outcome"].map(OUTCOME_LABELS).value_counts().sort_values()
    st.bar_chart(reasons.rename("tickets"), horizontal=True, height=220)
    st.caption("Each reason maps to a step in the ticket checklist: details, quick checks, or 'already reported'.")
    with st.expander("Table: which checklist step stops which reason"):
        st.dataframe(bounce_breakdown(df), width="stretch")

    st.subheader("3 · Every back-and-forth makes clients unhappier")
    happy = df.groupby("eng_handoffs")["csat_score"].mean()
    happy.index = [f"{i}× to engineering" for i in happy.index]
    st.bar_chart(happy.rename("client happiness (out of 5)"), height=220)

    st.subheader("🔮 What if the checklist works?")
    p = st.slider("Share of 'sent back' tickets the checklist prevents", 0, 100, WHATIF_DEFAULT,
                  step=10, format="%d%%") / 100
    sim = simulate_backlog(df, p).rename(columns={"actual": "what really happened", "with_gate": "with the checklist"})
    st.line_chart(sim)
    st.success(f"Open tickets on the last day would drop from **{sim.iloc[-1, 0]}** to **{sim.iloc[-1, 1]}**. "
               "This is a careful estimate: it ignores the time engineering gets back for real bugs.")

"""Page: Why we built this. Three findings in plain words, then a what-if."""
import pandas as pd
import streamlit as st

from rideops.metrics import growth_drivers, simulate_backlog, volume_growth
from rideops.triage import bounce_breakdown

from .config import OUTCOME_LABELS, WHATIF_DEFAULT


def render(df: pd.DataFrame) -> None:
    st.header("💡 Why we built this")
    esc = df[df["escalated"]]
    hours_share = esc["resolution_h"].sum() / df["resolution_h"].sum()

    # The pile grows for two reasons: more tickets arrive, and each one stays open longer.
    g = growth_drivers(df)
    first, last = g.iloc[0], g.iloc[-1]
    st.subheader("0 · The pile grew for two reasons")
    a, b, c = st.columns(3)
    a.metric("New tickets per day", f"{last['arrivals_per_day']:.1f}",
             f"{last['arrivals_per_day'] / first['arrivals_per_day'] - 1:+.0%} vs {g.index[0].strftime('%B')}",
             delta_color="inverse")
    b.metric("Days each ticket stays open", f"{last['avg_days_open']:.1f}",
             f"{last['avg_days_open'] / first['avg_days_open'] - 1:+.0%}", delta_color="inverse")
    c.metric("Open tickets on an average day", f"{last['avg_open_tickets']:.0f}",
             f"{last['avg_open_tickets'] / first['avg_open_tickets'] - 1:+.0%}", delta_color="inverse")
    st.markdown("**More tickets arriving** is the bigger cause. **Tickets staying open longer** is the other, and "
                "that's what the checklist fixes (findings 1-3 below). The extra tickets need a different fix:")
    with st.container(border=True):
        st.markdown("**Where the extra tickets come from** (problems that grew the most)")
        v = volume_growth(df)
        st.dataframe(v[["description", "first_month", "last_month", "extra_tickets", "sent_to_engineering",
                        "who_can_fix_it"]].rename(columns={
                            "description": "problem", "first_month": f"{g.index[0].strftime('%b')}",
                            "last_month": f"{g.index[-1].strftime('%b')}", "extra_tickets": "extra",
                            "sent_to_engineering": "share sent to eng", "who_can_fix_it": "who can stop it"}),
                     hide_index=True, width="stretch")
        st.caption("Most of these are not software bugs: address changes, cabs not turning up, drivers marking "
                   "false no-shows. They're fixed by self-serve address updates and vendor follow-ups, not by engineering.")

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
    st.info("**To get back to the July level, the checklist alone isn't enough.** It has to be paired with "
            "fixing the top growing problems in the 'extra tickets' table above.")

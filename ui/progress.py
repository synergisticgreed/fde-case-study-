"""Page: Are we improving? Three big weekly numbers for managers; details tucked away."""
import pandas as pd
import streamlit as st

from rideops.metrics import agent_scorecard, weekly_scorecard

from .config import PROGRESS_GOAL, PROGRESS_KPIS


def render(df: pd.DataFrame) -> None:
    st.header("📊 Are we improving?")
    card = weekly_scorecard(df)
    weeks = [w.strftime("%d %b") for w in card.index]
    # Default: first complete week vs latest complete week (first/last rows are partial weeks).
    base_i, cur_i = min(1, len(weeks) - 1), max(len(weeks) - 2, 0)
    with st.expander("📅 Change which weeks to compare"):
        base_i = weeks.index(st.selectbox("From week starting", weeks, index=base_i))
        cur_i = weeks.index(st.selectbox("To week starting", weeks, index=cur_i))
    base, cur = card.iloc[base_i], card.iloc[cur_i]
    st.caption(f"Comparing week of **{weeks[cur_i]}** with week of **{weeks[base_i]}**.")

    for col, (key, label, fmt, lower_better, help_) in zip(st.columns(len(PROGRESS_KPIS)), PROGRESS_KPIS):
        diff = cur[key] - base[key]
        better = diff < 0 if lower_better else diff > 0
        col.metric(label, fmt.format(cur[key]), fmt.format(diff),
                   delta_color="inverse" if lower_better else "normal", help=help_)
        col.caption("✅ getting better" if better else "⚠️ getting worse" if diff else "➖ no change")

    st.info(PROGRESS_GOAL)
    st.markdown("**Open tickets at the end of each week**")
    st.line_chart(card["open_at_week_end"].rename("open tickets"))

    with st.expander("🔍 More detail (for team leads)"):
        st.markdown("**What drives the open tickets (by week raised)**")
        st.line_chart(card[["bounce_rate", "escalation_rate", "reopen_rate"]].rename(columns={
            "bounce_rate": "sent back by engineering", "escalation_rate": "sent to engineering",
            "reopen_rate": "reopened by client"}))
        st.markdown("**Per agent.** Fast closing with many reopens means tickets are closed too early.")
        st.dataframe(agent_scorecard(df), width="stretch")

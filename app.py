"""RideOps Escalation Gate - Streamlit app.

Run:  streamlit run app.py
Tabs:
  1. Escalation Gate  - L1 agent works a ticket through the pre-escalation workflow.
  2. Weekly Scorecard - support lead / head of ops track the north-star and driver metrics.
  3. Why this tool    - the evidence behind the gate and a what-if on the open backlog.
"""
import pandas as pd
import streamlit as st

from rideops.data import SNAPSHOT, load_tickets
from rideops.metrics import agent_scorecard, simulate_backlog, weekly_scorecard
from rideops.playbooks import PLAYBOOKS, playbook
from rideops.triage import assess, bounce_breakdown, handoff_note

st.set_page_config(page_title="RideOps Escalation Gate", page_icon="🚦", layout="wide")

VERDICT_STYLE = {  # verdict -> (streamlit alert fn, headline)
    "RESOLVE_AT_L1": (st.warning, "Resolve at L1 first"),
    "COMPLETE_CHECKS": (st.info, "Complete the checks before escalating"),
    "ESCALATE": (st.success, "Ready to escalate"),
}


@st.cache_data
def data() -> pd.DataFrame:
    return load_tickets()


def ticket_picker(df: pd.DataFrame) -> dict:
    """Sidebar: choose an open ticket from the queue or enter a new one."""
    st.sidebar.header("Ticket")
    mode = st.sidebar.radio("Source", ["Open queue", "New ticket"], horizontal=True)
    if mode == "Open queue":
        queue = df[df["is_open"]].sort_values(["priority", "created_at"])
        label = queue["ticket_id"] + " · " + queue["priority"] + " · " + queue["description"].str[:45]
        tid = st.sidebar.selectbox(f"{len(queue)} open tickets", queue["ticket_id"],
                                   format_func=dict(zip(queue["ticket_id"], label)).get)
        return queue.set_index("ticket_id").loc[tid].to_dict() | {"ticket_id": tid}
    return {
        "ticket_id": "NEW",
        "category": st.sidebar.selectbox("Category", list(PLAYBOOKS)),
        "description": st.sidebar.text_input("Description", "Scheduled report email not received"),
        "priority": st.sidebar.selectbox("Priority", ["P1", "P2", "P3", "P4"], index=2),
        "client_name": st.sidebar.text_input("Client", "Demo Client"),
        "status": "New",
    }


def gate_tab(df: pd.DataFrame) -> None:
    t = ticket_picker(df)
    pb = playbook(t["category"])
    st.subheader(f"{t['ticket_id']} · {t['description']}")
    st.caption(f"{t['category']} · {t['priority']} · {t['client_name']} · status: {t['status']}")

    left, right = st.columns([3, 2])
    with left:  # agent inputs: runbook checks + required facts
        st.markdown("**1. L1 runbook checks** (confirm each one you've done)")
        done = {c for c in pb["l1_checks"] if st.checkbox(c, key=f"{t['ticket_id']}-chk-{c}")}
        st.markdown("**2. Details engineering needs to reproduce**")
        info = {f: st.text_input(f, key=f"{t['ticket_id']}-inf-{f}") for f in pb["required"]}
        info = {k: v for k, v in info.items() if v.strip()}

    r = assess(df, t["category"], t["description"], SNAPSHOT, set(info), done, t["ticket_id"])
    with right:  # live verdict + evidence
        alert, headline = VERDICT_STYLE[r.verdict]
        alert(f"**{headline}**\n\n{r.reason}")
        st.metric("Engineering fix rate on this issue", f"{r.fix_rate:.0%}",
                  help=f"{r.history_n} past escalations matched to: {r.matched_template or 'category only'}")
        if r.outcomes:
            st.bar_chart(pd.Series(r.outcomes, name="past escalations"), horizontal=True, height=200)
        st.markdown("**3. Already with engineering?**")
        if len(r.open_duplicates):
            st.warning(f"{len(r.open_duplicates)} open escalation(s) on this same issue - link instead of re-escalating.")
            st.dataframe(r.open_duplicates, hide_index=True, width="stretch")
        else:
            st.caption("No open engineering ticket on this issue.")

    if r.verdict == "ESCALATE":
        st.markdown("**Escalation note** (paste into the ENG ticket)")
        st.code(handoff_note(t, r, info), language=None)


def scorecard_tab(df: pd.DataFrame) -> None:
    card = weekly_scorecard(df)
    last, first = card.iloc[-2], card.iloc[1]  # last full week vs first full week
    cols = st.columns(5)
    for col, (name, key, fmt) in zip(cols, [
        ("Open at week end (north star)", "open_at_week_end", "{:.0f}"),
        ("Escalation bounce rate", "bounce_rate", "{:.0%}"),
        ("Handoffs / escalation", "handoffs_per_escalation", "{:.2f}"),
        ("Reopen rate (guardrail)", "reopen_rate", "{:.0%}"),
        ("CSAT (guardrail)", "csat", "{:.2f}")]):
        col.metric(name, fmt.format(last[key]), fmt.format(last[key] - first[key]) + " vs wk 1",
                   delta_color="normal" if key == "csat" else "inverse")
    st.caption("Last full week vs first full week. Targets: bounce < 25%, open backlog back to July level "
               "(~15) by quarter end, reopen and CSAT no worse. Recent weeks' bounce/reopen are still maturing.")
    c1, c2 = st.columns(2)
    c1.markdown("**Open tickets at week end**")
    c1.line_chart(card["open_at_week_end"])
    c2.markdown("**Drivers by week created**")
    c2.line_chart(card[["bounce_rate", "escalation_rate", "reopen_rate"]])
    st.markdown("**Agent view** - fast first-close with high reopens = premature closure, not speed")
    st.dataframe(agent_scorecard(df), width="stretch")
    with st.expander("Full weekly table"):
        st.dataframe(card, width="stretch")


def evidence_tab(df: pd.DataFrame) -> None:
    esc = df[df["escalated"]]
    share_h = esc["resolution_h"].sum() / df["resolution_h"].sum()
    c = st.columns(4)
    c[0].metric("Tickets escalated", f"{len(esc)} ({len(esc)/len(df):.0%})")
    c[1].metric("Share of all ticket-hours", f"{share_h:.0%}")
    c[2].metric("Escalations bounced back", f"{esc['bounced'].mean():.0%}")
    c[3].metric("Median hours: L1-only vs escalated",
                f"{df.loc[~df['escalated'], 'resolution_h'].median():.0f} vs {esc['resolution_h'].median():.0f}")
    st.markdown("**Bounced escalations by the gate control that prevents them**")
    st.dataframe(bounce_breakdown(df), width="stretch")
    st.markdown("**CSAT falls with every handoff**")
    st.bar_chart(df.groupby("eng_handoffs")["csat_score"].mean(), height=220)

    st.markdown("**What-if: open backlog if the gate prevents a share of bounces**")
    p = st.slider("Share of bounced escalations prevented", 0, 100, 50, step=10) / 100
    sim = simulate_backlog(df, p)
    st.line_chart(sim)
    st.caption(f"At {p:.0%}: open tickets on 30 Sep {sim['actual'].iloc[-1]} -> {sim['with_gate'].iloc[-1]}. "
               "Conservative: does not count engineering time freed for genuine bugs.")


def main() -> None:
    st.title("🚦 RideOps Escalation Gate")
    df = data()
    tabs = st.tabs(["Escalation Gate (L1 agent)", "Weekly Scorecard (lead / ops)", "Why this tool"])
    with tabs[0]:
        gate_tab(df)
    with tabs[1]:
        scorecard_tab(df)
    with tabs[2]:
        evidence_tab(df)


if __name__ == "__main__":
    main()

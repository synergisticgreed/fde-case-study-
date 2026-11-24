"""Page: Check a ticket. A top-to-bottom wizard for the support agent."""
import pandas as pd
import streamlit as st

from rideops.playbooks import playbook
from rideops.triage import assess, handoff_note

from . import components as c
from .config import CHECK_INTRO
from .picker import advanced_settings, pick_ticket


def render(df: pd.DataFrame) -> None:
    st.header("🎫 Check a ticket before sending it to engineering")
    st.caption(CHECK_INTRO)

    # Reserve screen positions so the result box can sit near the top
    # even though it is computed from the checklist further down.
    pick_box, result_box, steps_box, note_box = (st.container() for _ in range(4))
    cfg = advanced_settings(df)  # rendered last on screen

    with pick_box:
        st.subheader("Step 1 · Pick a ticket")
        ticket = pick_ticket(df, cfg.now)
    if not ticket:
        return
    pb = playbook(ticket["category"])
    key = f"{ticket['ticket_id']}|{ticket['description']}"  # new ticket -> fresh checklist

    with steps_box:
        left, right = st.columns(2, gap="large")
        with left:
            st.subheader("Step 2 · Do the quick checks")
            st.caption("Common causes you can fix yourself. Tick each one you've checked.")
            done = {x for x in pb["l1_checks"] if st.checkbox(x, key=f"{key}|chk|{x}")}
        with right:
            st.subheader("Step 3 · Collect the details")
            st.caption("What engineering needs. Type anything to mark it as collected.")
            info = {f: st.text_input(f, key=f"{key}|inf|{f}") for f in pb["required"]}
            info = {k: v for k, v in info.items() if v.strip()}
        total = len(pb["l1_checks"]) + len(pb["required"])
        st.progress((len(done) + len(info)) / total if total else 1.0,
                    text=f"Progress: {len(done) + len(info)} of {total} done")

    r = assess(df, ticket["category"], ticket["description"], cfg.now, set(info), done,
               ticket["ticket_id"], cfg.fix_threshold)

    with result_box:
        st.subheader("👉 What should I do?")
        c.verdict_box(r)
        st.markdown(c.fix_rate_sentence(r))
        if len(r.open_duplicates):
            st.warning(f"⚠️ Engineering already has **{len(r.open_duplicates)} open ticket(s)** about this same "
                       f"problem (e.g. {r.open_duplicates['eng_ticket_id'].iloc[-1]}). Link to it instead of "
                       "sending a new one.")
        with st.expander("Why does it say this?"):
            st.caption("What happened the last times this problem went to engineering:")
            c.outcomes_chart(r)
            if len(r.open_duplicates):
                st.dataframe(r.open_duplicates, hide_index=True, width="stretch")
        st.divider()

    if r.verdict == "ESCALATE":
        with note_box:
            st.subheader("Step 4 · Copy this note into the engineering ticket")
            st.code(handoff_note(ticket, r, info), language=None)

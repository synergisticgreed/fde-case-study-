"""Ticket picker and advanced settings for the Check-a-ticket page. Choices are built from the data."""
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from rideops.data import SNAPSHOT
from rideops.triage import FIX_RATE_THRESHOLD

from .components import go_to

SOURCES = ["A new ticket", "A real open ticket"]
# Session-state keys (examples on the home page write into these).
K_SRC, K_CAT, K_DESC, K_PRI = "src", "cat", "desc", "pri"


@dataclass
class Settings:
    now: pd.Timestamp     # "today" for the tool; only data known by then is used
    fix_threshold: float  # below this engineering fix rate, agent is told to try fixing it first


def advanced_settings(df: pd.DataFrame) -> Settings:
    """Optional knobs, hidden in an expander so beginners can ignore them."""
    with st.expander("⚙️ Advanced settings (you can ignore these)"):
        day = st.date_input("Pretend today is", value=SNAPSHOT.date(),
                            min_value=df["created_at"].min().date(), max_value=SNAPSHOT.date())
        thr = st.slider("Ask agents to try first when engineering fixes less than…", 0, 100,
                        int(FIX_RATE_THRESHOLD * 100), step=5, format="%d%%")
    return Settings(min(pd.Timestamp(day) + pd.Timedelta(hours=23, minutes=59), SNAPSHOT), thr / 100)


def _open_tickets(df: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    closed = df["final_closed_at"].notna() & (df["final_closed_at"] <= now)
    return df[(df["created_at"] <= now) & ~closed].sort_values(["priority", "created_at"])


def pick_ticket(df: pd.DataFrame, now: pd.Timestamp) -> dict:
    """Step 1 widget: returns the chosen ticket as a dict ({} if none available)."""
    st.session_state.setdefault(K_SRC, SOURCES[0])
    src = st.radio("Which ticket?", SOURCES, key=K_SRC, horizontal=True)

    if src == "A real open ticket":
        queue = _open_tickets(df, now)
        if queue.empty:
            st.info("No open tickets on this date.")
            return {}
        names = dict(zip(queue["ticket_id"], queue["priority"] + " · " + queue["description"]))
        tid = st.selectbox(f"{len(queue)} open tickets (most urgent first)", queue["ticket_id"],
                           format_func=names.get)
        return queue.set_index("ticket_id").loc[tid].to_dict() | {"ticket_id": tid}

    a, b, c = st.columns([2, 3, 1])
    cats = sorted(df["category"].unique())
    st.session_state.setdefault(K_CAT, cats[0])
    cat = a.selectbox("Type of problem", cats, key=K_CAT)
    descs = sorted(df.loc[df["category"] == cat, "description"].unique())
    if st.session_state.get(K_DESC) not in descs:  # type changed -> reset problem
        st.session_state[K_DESC] = descs[0]
    desc = b.selectbox("What the client says", descs, key=K_DESC)
    pris = sorted(df["priority"].unique())
    st.session_state.setdefault(K_PRI, pris[len(pris) // 2])
    pri = c.selectbox("Urgency", pris, key=K_PRI, help="P1 = most urgent, P4 = least")
    return {"ticket_id": "NEW", "category": cat, "description": desc, "priority": pri,
            "client_name": "New client", "status": "New"}


def load_example(example: dict) -> None:
    """Button callback: put an example ticket in the picker and open the Check-a-ticket page."""
    st.session_state.update({K_SRC: SOURCES[0], K_CAT: example["category"],
                             K_DESC: example["description"], K_PRI: example["priority"]})
    go_to("check")

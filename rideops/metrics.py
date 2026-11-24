"""Weekly success metrics, open-backlog series and the what-if backlog simulation.

North-star : open tickets at week end (the number leadership reviews).
Drivers    : escalation bounce rate, handoffs per escalation, reopen rate.
Guardrails : median resolution hours, CSAT (so the backlog isn't cut by closing tickets early).
Assumption : a reopened ticket counts as open from creation until its final close
             (reopen timestamps are not in the export).
"""
import pandas as pd

from .data import SNAPSHOT


def open_backlog(tickets: pd.DataFrame, at: pd.DatetimeIndex) -> pd.Series:
    """Number of tickets open at each timestamp in `at`."""
    closed = tickets["final_closed_at"].fillna(pd.Timestamp.max)
    return pd.Series([int(((tickets["created_at"] <= t) & (closed > t)).sum()) for t in at], index=at)


def week_ends(tickets: pd.DataFrame) -> pd.DatetimeIndex:
    """Sunday 23:59 of every week in the data, capped at the data pull."""
    ends = pd.date_range(tickets["created_at"].min().normalize(), SNAPSHOT, freq="W-SUN") \
        + pd.Timedelta(hours=23, minutes=59)
    return ends.append(pd.DatetimeIndex([SNAPSHOT])) if ends[-1] < SNAPSHOT else ends


def weekly_scorecard(tickets: pd.DataFrame) -> pd.DataFrame:
    """One row per week: north-star backlog plus driver and guardrail metrics (by week created)."""
    esc = tickets[tickets["escalated"]]
    g = tickets.groupby("week")
    card = pd.DataFrame({
        "created": g.size(),
        "escalation_rate": g["escalated"].mean(),
        "bounce_rate": esc.groupby("week")["bounced"].mean(),
        "handoffs_per_escalation": esc.groupby("week")["eng_handoffs"].mean(),
        "reopen_rate": g["reopened"].mean(),
        "median_resolution_h": g["resolution_h"].median(),
        "csat": g["csat_score"].mean(),
    })
    backlog = open_backlog(tickets, week_ends(tickets))
    card["open_at_week_end"] = backlog.values[: len(card)]
    return card[["open_at_week_end"] + [c for c in card.columns if c != "open_at_week_end"]].round(2)


def agent_scorecard(tickets: pd.DataFrame) -> pd.DataFrame:
    """Per-agent view: separates genuinely fast agents from fast-but-reopened closes."""
    g = tickets.groupby("assigned_agent")
    first_close_h = (tickets["first_closed_at"] - tickets["created_at"]).dt.total_seconds() / 3600
    return pd.DataFrame({
        "tickets": g.size(),
        "median_first_close_h": first_close_h.groupby(tickets["assigned_agent"]).median(),
        "reopen_rate": g["reopened"].mean(),
        "escalation_rate": g["escalated"].mean(),
        "bounce_rate": tickets[tickets["escalated"]].groupby("assigned_agent")["bounced"].mean(),
        "csat": g["csat_score"].mean(),
    }).round(2).sort_values("reopen_rate", ascending=False)


def simulate_backlog(tickets: pd.DataFrame, prevent_share: float, seed: int = 7) -> pd.DataFrame:
    """What-if: the gate stops `prevent_share` of bounced escalations reaching engineering.

    Prevented tickets are assumed to resolve like a typical non-escalated ticket of the same
    category. Conservative: ignores engineering time freed up for genuine bugs.
    """
    sim = tickets.copy()
    l1_median = pd.to_timedelta(sim[~sim["escalated"]].groupby("category")["resolution_h"].median(), unit="h")
    prevented = sim[sim["bounced"]].sample(frac=prevent_share, random_state=seed).index
    sim.loc[prevented, "final_closed_at"] = (sim.loc[prevented, "created_at"]
                                             + sim.loc[prevented, "category"].map(l1_median))
    at = week_ends(tickets)
    return pd.DataFrame({"actual": open_backlog(tickets, at), "with_gate": open_backlog(sim, at)})

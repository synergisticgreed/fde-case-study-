"""Weekly success metrics, open-backlog series and the what-if backlog simulation.

North-star : open tickets at week end (the number leadership reviews).
Drivers    : escalation bounce rate, handoffs per escalation, reopen rate.
Guardrails : median resolution hours, CSAT (so the backlog isn't cut by closing tickets early).
Assumption : a reopened ticket counts as open from creation until its final close
             (reopen timestamps are not in the export).
"""
import pandas as pd

from .data import SNAPSHOT
from .playbooks import owner


def _end_of_day(days: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Move each date to 23:59, so a day's tickets are all counted."""
    return days + pd.Timedelta(hours=23, minutes=59)


def open_backlog(tickets: pd.DataFrame, at: pd.DatetimeIndex) -> pd.Series:
    """Number of tickets open at each timestamp in `at`."""
    closed = tickets["final_closed_at"].fillna(pd.Timestamp.max)
    return pd.Series([int(((tickets["created_at"] <= t) & (closed > t)).sum()) for t in at], index=at)


def week_ends(tickets: pd.DataFrame) -> pd.DatetimeIndex:
    """Sunday 23:59 of every week in the data, capped at the data pull."""
    ends = _end_of_day(pd.date_range(tickets["created_at"].min().normalize(), SNAPSHOT, freq="W-SUN"))
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
    # Each week's own end (Sunday 23:59, capped at the data pull), not alignment by position.
    ends = pd.DatetimeIndex([min(w + pd.Timedelta(days=6, hours=23, minutes=59), SNAPSHOT) for w in card.index])
    card["open_at_week_end"] = open_backlog(tickets, ends).values
    return card[["open_at_week_end"] + [c for c in card.columns if c != "open_at_week_end"]].round(2)


def growth_drivers(tickets: pd.DataFrame) -> pd.DataFrame:
    """Split backlog growth into its two causes (Little's law: open ≈ arrivals/day × days open).

    Per month: tickets arriving per day, average days a ticket stays open, average open tickets.
    """
    days = _end_of_day(pd.date_range(tickets["created_at"].min().normalize(), SNAPSHOT.normalize(), freq="D"))
    daily_open = open_backlog(tickets, days)
    month = tickets["created_at"].dt.to_period("M")
    active_days = tickets.groupby(month)["created_at"].agg(lambda s: s.dt.normalize().nunique())
    return pd.DataFrame({
        "arrivals_per_day": tickets.groupby(month).size() / active_days,
        "avg_days_open": tickets.groupby(month)["resolution_h"].mean() / 24,
        "avg_open_tickets": daily_open.groupby(daily_open.index.to_period("M")).mean(),
    }).round(2)


def volume_growth(tickets: pd.DataFrame, top: int = 8) -> pd.DataFrame:
    """Issues whose ticket count grew most from the first to the last month, with who can fix them."""
    month = tickets["created_at"].dt.to_period("M")
    first, last = month.min(), month.max()
    t = tickets.assign(month=month)
    counts = t.pivot_table(index=["category", "description"], columns="month", values="ticket_id",
                           aggfunc="size", fill_value=0)
    out = pd.DataFrame({"first_month": counts[first], "last_month": counts[last]})
    out["extra_tickets"] = out["last_month"] - out["first_month"]
    out = out.sort_values("extra_tickets", ascending=False).head(top).reset_index()
    out["sent_to_engineering"] = [tickets.loc[tickets["description"] == d, "escalated"].mean().round(2)
                                  for d in out["description"]]
    out["who_can_fix_it"] = out["category"].map(owner)
    return out


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

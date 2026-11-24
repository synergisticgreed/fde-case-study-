"""Escalation Gate: a mandatory pre-escalation workflow for L1 agents.

Data finding: ~57% of escalations bounce back from engineering, at a similar rate across every
category, agent, channel and tier, so bounces are a process gap, not something to predict per ticket.
Each gate step therefore targets one bounce reason:

  open ENG tickets on same issue -> "Duplicate of known issue"
  L1 runbook checks              -> "Config issue" / "Not a bug - how-to"
  required-info checklist        -> "Insufficient info" / "Not reproducible"

Verdicts (first match wins): RESOLVE_AT_L1 -> COMPLETE_CHECKS -> ESCALATE.
"""
from dataclasses import dataclass, field
from difflib import get_close_matches

import pandas as pd

from .data import template
from .playbooks import playbook

FIX_RATE_THRESHOLD = 0.35  # engineering fixes fewer than this share of the issue -> runbook first
PRIOR_STRENGTH = 5         # pseudo-count shrinking sparse templates toward the category fix rate

# Which gate control prevents which engineering bounce reason.
CONTROL_FOR_OUTCOME = {
    "Duplicate of known issue": "Known-issue lookup",
    "Config issue - returned to L1": "L1 runbook checks",
    "Not a bug - how-to": "L1 runbook checks",
    "Insufficient info - returned to L1": "Required-info checklist",
    "Not reproducible": "Required-info checklist",
}


@dataclass
class GateResult:
    verdict: str
    reason: str
    matched_template: str | None
    history_n: int
    fix_rate: float
    outcomes: dict[str, int] = field(default_factory=dict)
    open_duplicates: pd.DataFrame = field(default_factory=pd.DataFrame)
    missing_info: list[str] = field(default_factory=list)
    pending_checks: list[str] = field(default_factory=list)


def match_template(desc: str, candidates: list[str]) -> str | None:
    """Exact template match, else closest fuzzy match within the category."""
    t = template(desc)
    if t in candidates:
        return t
    hits = get_close_matches(t, candidates, n=1, cutoff=0.6)
    return hits[0] if hits else None


def open_with_engineering(tickets: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    """Escalations raised before `now` and not yet finally closed at `now`."""
    closed = tickets["final_closed_at"].notna() & (tickets["final_closed_at"] <= now)
    return tickets[tickets["escalated"] & (tickets["created_at"] < now) & ~closed]


def assess(tickets: pd.DataFrame, category: str, description: str, now: pd.Timestamp,
           info_provided: set[str] = frozenset(), checks_done: set[str] = frozenset(),
           ticket_id: str | None = None, fix_threshold: float = FIX_RATE_THRESHOLD) -> GateResult:
    """Run the gate for one ticket using only what was known at `now`."""
    pb = playbook(category)
    tickets = tickets[tickets["ticket_id"] != ticket_id]  # never match a ticket against itself

    # Engineering's track record on this issue (only escalations already closed at `now`).
    hist = tickets[tickets["escalated"] & (tickets["category"] == category)
                   & (tickets["first_closed_at"] < now)]
    matched = match_template(description, hist["template"].unique().tolist())
    tmpl = hist[hist["template"] == matched] if matched else hist.iloc[0:0]
    cat_rate = hist["eng_outcome"].eq("Fixed").mean() if len(hist) else 0.5
    fix_rate = float((tmpl["eng_outcome"].eq("Fixed").sum() + PRIOR_STRENGTH * cat_rate)
                     / (len(tmpl) + PRIOR_STRENGTH))

    # Live engineering tickets on the same issue -> agent should link, not re-escalate.
    live = open_with_engineering(tickets, now)
    dupes = live[(live["category"] == category) & (live["template"] == (matched or template(description)))]

    common = dict(matched_template=matched, history_n=len(tmpl), fix_rate=fix_rate,
                  outcomes=tmpl["eng_outcome"].value_counts().to_dict(),
                  open_duplicates=dupes[["ticket_id", "eng_ticket_id", "client_name", "created_at", "status"]])
    missing = [f for f in pb["required"] if f not in info_provided]
    pending = [c for c in pb["l1_checks"] if c not in checks_done]

    if fix_rate < fix_threshold and pending:
        return GateResult("RESOLVE_AT_L1",
                          f"Engineering fixed only {fix_rate:.0%} of similar escalations - most were "
                          "config or how-to. Work the runbook; escalate only if every check passes.",
                          missing_info=missing, pending_checks=pending, **common)
    if missing or pending:
        return GateResult("COMPLETE_CHECKS",
                          f"{len(pending)} runbook check(s) and {len(missing)} required detail(s) "
                          "outstanding. Incomplete escalations are what bounce.",
                          missing_info=missing, pending_checks=pending, **common)
    return GateResult("ESCALATE", f"Checks done, handoff complete (historical fix rate {fix_rate:.0%}).",
                      **common)


def handoff_note(ticket: dict, result: GateResult, info: dict[str, str]) -> str:
    """Structured escalation note engineering receives instead of a one-line forward."""
    lines = [f"[{ticket['ticket_id']}] {ticket['category']} | {ticket['priority']} | {ticket['client_name']}",
             f"Issue: {ticket['description']}",
             f"Engineering history on this issue: {result.history_n} past escalations, "
             f"{result.fix_rate:.0%} fixed", "", "Details:"]
    lines += [f"  - {k}: {v}" for k, v in info.items()]
    lines += ["", "L1 checks completed:"] + [f"  [x] {c}" for c in playbook(ticket["category"])["l1_checks"]]
    if len(result.open_duplicates):
        lines += ["", "Possibly related open ENG tickets: " + ", ".join(result.open_duplicates["eng_ticket_id"])]
    return "\n".join(lines)


def bounce_breakdown(tickets: pd.DataFrame) -> pd.DataFrame:
    """Bounced escalations grouped by the gate control that would have prevented them."""
    b = tickets[tickets["bounced"]].copy()
    b["control"] = b["eng_outcome"].map(CONTROL_FOR_OUTCOME)
    return (b.groupby("control")
             .agg(tickets=("ticket_id", "size"), ticket_hours=("resolution_h", "sum"),
                  median_hours=("resolution_h", "median"), avg_handoffs=("eng_handoffs", "mean"))
             .sort_values("tickets", ascending=False).round(1))

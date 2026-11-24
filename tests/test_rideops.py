"""Core behaviour tests for the gate, metrics and data loading."""
import pandas as pd
import pytest

from rideops.data import SNAPSHOT, load_tickets, template
from rideops.metrics import simulate_backlog, weekly_scorecard
from rideops.playbooks import playbook
from rideops.triage import assess, bounce_breakdown

CAT = "Report export failing"


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return load_tickets()


def test_load_matches_brief(df):
    assert len(df) == 1444
    assert df["is_open"].sum() == 48


def test_template_strips_numbers():
    assert template("Roster shows duplicate entries for 17 employees") == "roster shows duplicate entries for # employees"


def test_low_fix_rate_issue_goes_to_l1(df):
    r = assess(df, CAT, "Scheduled report email not received", SNAPSHOT)
    assert r.verdict == "RESOLVE_AT_L1" and r.fix_rate < 0.35


def test_escalate_only_when_checks_and_info_complete(df):
    pb = playbook("Roster / booking not syncing")
    desc = "Cancelled bookings still appearing in tomorrow's roster"
    partial = assess(df, "Roster / booking not syncing", desc, SNAPSHOT)
    full = assess(df, "Roster / booking not syncing", desc, SNAPSHOT,
                  set(pb["required"]), set(pb["l1_checks"]))
    assert partial.verdict == "COMPLETE_CHECKS" and full.verdict == "ESCALATE"


def test_no_lookahead(df):
    # At the very first ticket there is no closed history, so no issue-level match is possible.
    r = assess(df, CAT, "Monthly trip report download stuck at loading", df["created_at"].min())
    assert r.history_n == 0


def test_bounce_breakdown_covers_all_bounces(df):
    assert bounce_breakdown(df)["tickets"].sum() == df["bounced"].sum() == 275


def test_scorecard_and_simulation(df):
    assert weekly_scorecard(df)["open_at_week_end"].iloc[-1] == 48
    sim = simulate_backlog(df, 0.5)
    assert (sim["with_gate"] <= sim["actual"]).all()

"""Load the ticket export and derive the fields every other module relies on."""
import re
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "rideops_support_tickets.csv"
SNAPSHOT = pd.Timestamp("2026-09-30 23:59")  # data pull time; open tickets are measured to here
TIME_COLS = ["created_at", "first_response_at", "first_closed_at", "final_closed_at"]

# Engineering verdicts that mean the escalation should not have gone to engineering as-is.
BOUNCE_OUTCOMES = {
    "Insufficient info - returned to L1",
    "Config issue - returned to L1",
    "Duplicate of known issue",
    "Not a bug - how-to",
    "Not reproducible",
}


def template(description: str) -> str:
    """Normalise a description into an issue template ("... for 17 employees" -> "... for # employees")."""
    return re.sub(r"\d+", "#", str(description)).strip().lower()


def hours(delta: pd.Series) -> pd.Series:
    return delta.dt.total_seconds() / 3600


def load_tickets(path: Path | str = DATA_PATH) -> pd.DataFrame:
    """Read the CSV and add derived columns (template, flags, durations, week)."""
    df = pd.read_csv(path, parse_dates=TIME_COLS)
    df["template"] = df["description"].map(template)
    df["escalated"] = df["escalated_to_eng"].eq("Yes")
    df["bounced"] = df["eng_outcome"].isin(BOUNCE_OUTCOMES)
    df["is_open"] = df["final_closed_at"].isna()
    df["reopened"] = df["reopen_count"].gt(0)
    df["resolution_h"] = hours(df["final_closed_at"].fillna(SNAPSHOT) - df["created_at"])
    df["first_response_h"] = hours(df["first_response_at"] - df["created_at"])
    df["week"] = df["created_at"].dt.to_period("W-SUN").dt.start_time
    return df.sort_values("created_at").reset_index(drop=True)

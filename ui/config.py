"""All on-screen words live here: page names, explanations, verdict wording, demo examples.

Edit this file to change what users read. Numbers on screen are always computed from data.
"""

APP_TITLE = "🚦 RideOps Ticket Helper"

# Top navigation, in the order a beginner should visit them.
PAGES = {
    "home": "🏠 Start here",
    "check": "🎫 Check a ticket",
    "progress": "📊 Are we improving?",
    "why": "💡 Why we built this",
}

# ---------- Verdicts: what the coloured box says ----------
VERDICTS = {
    "RESOLVE_AT_L1": {"kind": "warning", "icon": "🟨", "title": "Try to fix it yourself first",
                      "text": "Engineering rarely fixes this kind of problem. It's usually a setting. "
                              "Do the quick checks below."},
    "COMPLETE_CHECKS": {"kind": "info", "icon": "🟦", "title": "Almost: finish the checklist",
                        "text": "This may need engineering, but tick every check and fill every detail first. "
                                "Otherwise engineering will send it back."},
    "ESCALATE": {"kind": "success", "icon": "🟩", "title": "Ready to send to engineering",
                 "text": "Everything is done. Copy the note at the bottom into the engineering ticket."},
}

# Plain names for what engineering did with past tickets.
OUTCOME_LABELS = {
    "Fixed": "Fixed ✅",
    "Insufficient info - returned to L1": "Sent back: missing info",
    "Config issue - returned to L1": "Sent back: just a setting",
    "Duplicate of known issue": "Sent back: already reported",
    "Not a bug - how-to": "Sent back: how-to question",
    "Not reproducible": "Sent back: couldn't reproduce",
}

# ---------- Home page ----------
HOME_INTRO = ("Support agents send many tickets to the engineering team that engineering **can't or doesn't "
              "need to** fix. Those tickets bounce back and forth for days, and the pile of open tickets grows.  \n"
              "This tool gives agents a **simple checklist before they escalate**, so tickets go to engineering "
              "only once, and only when needed.")

HOW_TO_USE = [
    ("🎫 Check a ticket", "Pick a ticket, tick the checks, and the tool tells you what to do."),
    ("📊 Are we improving?", "Weekly numbers for managers: is the pile of open tickets shrinking?"),
    ("💡 Why we built this", "The facts from the data that led to this tool."),
]

# Real descriptions from the data; what the tool says at each stage is computed live.
EXAMPLES = [
    {"title": "Report email not arriving",
     "category": "Report export failing", "description": "Scheduled report email not received", "priority": "P3",
     "story": "A client says their scheduled report email never arrived.",
     "lesson": "Engineering rarely fixes this one, so the tool first sends the agent to the quick checks. "
               "Only after every check passes is the ticket ready for engineering."},
    {"title": "Duplicate names in roster",
     "category": "Roster / booking not syncing", "description": "Roster shows duplicate entries for 17 employees",
     "priority": "P2",
     "story": "The client's roster shows the same employees twice.",
     "lesson": "This is a real bug. The tool doesn't block it. It just makes sure engineering gets all the "
               "details, so the ticket isn't sent back."},
    {"title": "Problem already reported",
     "category": "Roster / booking not syncing",
     "description": "Booking cutoff changed but roster still uses old cutoff", "priority": "P3",
     "story": "A client reports a roster problem that other clients reported this week too.",
     "lesson": "The tool shows that engineering already has open tickets on this. The agent can link to one "
               "instead of creating a duplicate."},
]

STAGES = [  # (name, what the agent has done, checks done?, details filled?)
    ("1. Ticket arrives", "Nothing done yet", False, False),
    ("2. Checks ticked", "All quick checks done", True, False),
    ("3. Details filled", "All details collected", True, True),
]

GLOSSARY = {
    "Agent (L1)": "The support person who first receives a client's ticket.",
    "Escalate": "Send the ticket to the engineering team.",
    "Bounce": "Engineering sends the ticket back without fixing it.",
    "Open ticket": "A ticket that isn't solved yet.",
}

# ---------- Check-a-ticket page ----------
CHECK_INTRO = "Follow the steps. The coloured box tells you what to do, and it updates as you go."

# ---------- Progress page ----------
PROGRESS_KPIS = [  # (column, label, format, lower is better, explanation)
    ("open_at_week_end", "Open tickets", "{:.0f}", True, "Tickets not yet solved at the end of the week."),
    ("bounce_rate", "Sent back by engineering", "{:.0%}", True, "Of tickets sent to engineering, how many came back unfixed."),
    ("csat", "Client happiness (out of 5)", "{:.1f}", False, "Average rating clients gave."),
]
PROGRESS_GOAL = ("🎯 **Goal for this quarter:** fewer open tickets, fewer than 1 in 4 escalations sent back, "
                 "and client happiness that doesn't drop.")

# ---------- What-if ----------
WHATIF_DEFAULT = 50

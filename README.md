# RideOps Escalation Gate (v0)

A working internal tool for **L1 support agents** that stops bad escalations from reaching engineering,
plus a weekly scorecard for the support lead and head of ops. It runs on the real ticket export.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py              # opens http://localhost:8501
pytest -q                         # 7 tests
```

## Why this tool (diagnosis in one screen)

| Finding | Evidence from the data |
|---|---|
| Escalations *are* the backlog | 34% of tickets (486/1,444) but **71% of ticket-hours**; median 12.6 h L1-only vs 65-129 h escalated |
| Most escalations shouldn't have gone to engineering | **57% bounced back** (275/486): insufficient info 89, config 84, duplicate 56, how-to 24, not reproducible 22 |
| Bounces are a process gap, not a few bad tickets | Bounce rate is 47-66% in every category, priority, channel and tier, so there's nothing to "predict" |
| Each handoff costs about 50 h and client goodwill | Median resolution 58 h → 110 h → 164 h at 1/2/3 handoffs; CSAT 4.0 → 3.6 → 2.8 → 2.1 |
| Duplicates are growing | "Duplicate of known issue" went 8 → 21 → 27 per month (Jul → Sep) |
| "Fast" agents are partly premature closures | Karan B: 7.9 h median first-close vs ~20 h for peers, but **29% reopen rate** (64 of 151 reopened tickets) and CSAT 3.1 |

Both Meera (engineering is slow) and Sandeep (support escalates junk) are partly right: engineering is slow
*because* more than half of its queue is junk that comes back around up to 3 times.

## What the gate does

For each ticket, the agent works through three steps. Each step targets one bounce reason:

| Gate step | Prevents | Bounces it targets |
|---|---|---|
| **Open-ENG lookup**: shows live engineering tickets on the same issue | Duplicate of known issue | 56 |
| **L1 runbook checks**: config/how-to checks per category | Config issue, Not a bug | 108 |
| **Required-info checklist**: facts engineering needs to reproduce | Insufficient info, Not reproducible | 111 |

Verdict: `RESOLVE_AT_L1` (engineering fixed <35% of this issue historically) → `COMPLETE_CHECKS` → `ESCALATE`,
which generates a structured handoff note for the ENG ticket. Issue history is matched by description template
(numbers stripped, fuzzy fallback) and uses only tickets closed before "now", so there's no look-ahead.

## Success measure (weekly)

- **North star:** open tickets at week end (the number leadership reviews). Now 48, July level about 12-15.
- **Drivers:** escalation bounce rate (57% → target <25%), handoffs per escalation.
- **Guardrails:** reopen rate (currently 10%) and CSAT, so the backlog isn't "fixed" by closing early.

What-if (tab 3): preventing 50% of bounces cuts the 30 Sep backlog from 48 to 39. This is conservative
because it ignores the engineering time freed up for genuine bugs.

## Code layout

```
app.py               Streamlit UI: Gate / Scorecard / Evidence tabs
rideops/data.py      load CSV, derive template, flags, durations
rideops/playbooks.py per-category runbook checks + required info (owned by support lead)
rideops/triage.py    gate logic, handoff note, bounce breakdown
rideops/metrics.py   weekly scorecard, agent view, backlog what-if
tests/               behaviour tests
```

## Assumptions and known limits

- Playbook contents are my drafts. In week 1 they'd be validated with Meera and Sandeep.
- A reopened ticket counts as open from creation until its final close (reopen timestamps aren't in the export).
- Recent weeks' bounce and reopen rates are still maturing (right-censored).
- The what-if assumes a prevented bounce resolves like a typical L1-only ticket in its category.
- Checklist effectiveness can't be backtested from this data. It gets measured live via the bounce rate.

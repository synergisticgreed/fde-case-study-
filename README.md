# RideOps Escalation Gate (v0)

A working internal tool for **L1 support agents** that stops bad escalations from reaching engineering,
plus a weekly scorecard for the support lead and head of ops. It runs on the real ticket export.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py              # opens http://localhost:8501
pytest -q                         # 12 tests
```

## Why this tool (diagnosis in one screen)

**Two things grew the backlog** (open ≈ arrivals/day × days open). Average open tickets went 20.8 → 42.9 (Jul → Sep):

- **More tickets arriving: +52%** (13.0 → 19.7/day). This is the bigger driver. It comes mostly from **existing** clients
  (+34% tickets per client; new clients add only 68 of Sep's 592). The fastest-growing issues are mostly **not software
  bugs**: address changes (3x), cab no-shows/delays (2.5x), billing (1.8x). These are rarely escalated (3-15%).
- **Each ticket staying open longer: +22%** (1.72 → 2.09 days). This is driven by escalations, below. The v0 targets this part.

| Finding | Evidence from the data |
|---|---|
| Escalations *are* the backlog | 34% of tickets (486/1,444) but **71% of ticket-hours**; median 12.6 h L1-only vs 65-129 h escalated |
| Most escalations shouldn't have gone to engineering | **57% bounced back** (275/486): insufficient info 89, config 84, duplicate 56, how-to 24, not reproducible 22 |
| Bounces are a process gap, not a few bad tickets | Bounce rate is 47-68% in every major category, priority, channel and tier, so there's nothing to "predict" |
| Each handoff costs about 50 h and client goodwill | Median resolution 58 h → 110 h → 164 h at 1/2/3 handoffs; CSAT 4.0 → 3.6 → 2.8 → 2.1 |
| Duplicates are growing | "Duplicate of known issue" went 8 → 21 → 27 per month (Jul → Sep) |
| "Fast" agents are partly premature closures | Karan B: 7.9 h median first-close vs ~22 h for peers, but **29% reopen rate** (64 of 151 reopened tickets) and CSAT 3.1 |

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

What-if (Why page): preventing 50% of bounces cuts the 30 Sep backlog from 48 to 39. This is conservative
because it ignores the engineering time freed up for genuine bugs. **The checklist alone won't get back to the July
level.** The volume lever (self-serve address updates, vendor no-show follow-up, help-centre articles for the top
how-to questions) has to run alongside it. The Why page lists the issues that grew most and who can stop each one.

## Using the app (first time)

Open on **🏠 Start here**: the problem in 3 numbers, then a real ticket played stage by stage. Click **▶️ Try this example yourself** to jump to **🎫 Check a ticket** with it filled in.

## Code layout

```
app.py               entry point: wires sidebar + tabs together (no logic)
rideops/             logic, no UI
  data.py            load CSV, derive template, flags, durations
  playbooks.py       per-category runbook checks + required info (owned by support lead)
  triage.py          gate logic, handoff note, bounce breakdown
  metrics.py         weekly scorecard, agent view, backlog what-if
ui/                  one module per tab
  config.py          ALL on-screen text, KPI definitions, targets, demo examples (edit here)
  picker.py          ticket picker (built from the data) + advanced settings
  components.py      shared widgets (verdict box, page switching)
  home.py | check.py | progress.py | why.py   one file per page
tests/               logic tests + UI smoke tests
```

## Assumptions and known limits

- Playbook contents are my drafts. In week 1 they'd be validated with Meera and Sandeep.
- A reopened ticket counts as open from creation until its final close (reopen timestamps aren't in the export).
- Recent weeks' bounce and reopen rates are still maturing (right-censored).
- The what-if assumes a prevented bounce resolves like a typical L1-only ticket in its category.
- Checklist effectiveness can't be backtested from this data. It gets measured live via the bounce rate.

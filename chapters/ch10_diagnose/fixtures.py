"""Chapter 10 fixtures: seeded, synthetic, never real people.

Writes data/ for the diagnostic at Hartwell (synthetic):
  events.csv.gz    Q4 2026 event log, AskHartwell and the ticket desk
  tickets.csv.gz   the ticket export (one row per ticket, with text)
  worksample.csv   the Four Buckets work-sampling study
  sectors/*.csv    Lakemont wards, Brightwater shifts, Westbridge cases

Run: python -m chapters.ch10_diagnose.fixtures
"""
from __future__ import annotations

import csv
import gzip
import io
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SEED = 1010
Q4_START = datetime(2026, 10, 1)
Q4_DAYS = 92
N_CASES = 36_000

WEIGHTS = {  # requests per category, Q4 2026 (synthetic)
    "PAY-Q": 12, "LV-BAL": 8, "LV-POL": 7, "BEN-Q": 6,
    "POL-Q": 5, "SYS-HOW": 6, "ADDR": 4, "BANK": 2, "LTR": 4,
    "LV-BOOK": 4, "TAX": 3, "ACC": 5, "PAY-DISP": 2,
    "ACCOM": 1, "CONC": 1, "LV-EXC": 2, "RTW": 1, "CHASE": 9,
    "PAY-ERR": 6, "REWORK": 3, "ONB-MISS": 2}

# What the old AskHartwell bot does with a request, by route:
# P(answer accepted), P(abandon), P(asks for a person).
BOT = {"answer": (0.30, 0.25, 0.45), "act": (0.04, 0.27, 0.69),
       "person": (0.02, 0.25, 0.73), "fix": (0.02, 0.30, 0.68)}
FALSE_HANDOFF = 0.17   # promised a person, no ticket created

SYSTEM_CAT = {  # the desk's own drop-down, as advisers used it
    "PAY-Q": "Pay", "PAY-DISP": "Pay", "PAY-ERR": "Pay",
    "LV-BAL": "Leave", "LV-POL": "Leave", "LV-BOOK": "Leave",
    "LV-EXC": "Leave", "BEN-Q": "Benefits", "ADDR":
    "Personal data", "BANK": "Personal data", "TAX": "Pay",
    "LTR": "Letters", "ACC": "Access", "SYS-HOW": "Access",
    "POL-Q": "Policy", "ACCOM": "Escalation", "CONC":
    "Escalation", "RTW": "Escalation", "CHASE":
    "General inquiry", "REWORK": "General inquiry",
    "ONB-MISS": "General inquiry"}

TEXT = {
 "PAY-Q": ["Can you explain the deduction labeled {code} on my "
           "payslip for {month}?", "When is pay day this month? "
           "The calendar shows two dates.", "My net pay went down "
           "this period and I don't know why, is it the {thing}?"],
 "LV-BAL": ["How many vacation days do I have left for this year?",
            "Does my sick balance carry over into January?",
            "My balance says {n} days, is that right after {month}?"],
 "LV-POL": ["How much notice do I need to give for a week off?",
            "What is the policy on taking leave over the holidays "
            "for field crews?", "Can I take half days of vacation?"],
 "BEN-Q": ["Open enrollment closes when? I want to add my "
           "spouse.", "Which dental plan covers orthodontics?",
           "How do I change my 401(k) contribution?"],
 "POL-Q": ["What is the per diem for an overnight job in "
           "{city}?", "Is there a policy on using my own truck "
           "for site visits?", "Where is the travel policy?"],
 "SYS-HOW": ["How do I download my W-2 from HartwellOne?",
             "Where in HartwellOne do I update my emergency "
             "contact?", "How do I see my team's schedule?"],
 "ADDR": ["I moved, please update my address to {addr}.",
          "New home address from {month}: {addr}. Thanks."],
 "BANK": ["I changed banks. How do I update my direct deposit?",
          "Please change my bank account for pay, new bank is "
          "{bank}."],
 "LTR": ["I need an employment verification letter for my "
         "mortgage lender.", "Can I get a letter confirming my "
         "salary and start date for a rental application?"],
 "LV-BOOK": ["I booked {n} days off but it shows as sick leave, "
             "please fix.", "Please book me off {month} {d} to "
             "{d2}, my supervisor already agreed."],
 "TAX": ["I need to change my withholding after getting "
         "married.", "My TD1 needs updating for the new year."],
 "ACC": ["I'm locked out of HartwellOne.", "Password reset "
         "link expired again, can't log in."],
 "PAY-DISP": ["I worked {n} hours overtime on the {city} job and "
              "was paid for {m}. My supervisor says it was "
              "approved.", "I think I'm owed the standby rate for "
              "last weekend, I was on call both days."],
 "ACCOM": ["I need a different work schedule because of a "
           "medical condition. Who do I talk to?", "Can I get a "
           "modified duty assignment after my injury?"],
 "CONC": ["I want to report how my crew lead talks to me. It's "
          "been going on for weeks.", "Something happened on site "
          "that I think HR needs to know about. Who can I speak "
          "to in confidence?"],
 "LV-EXC": ["My father is in hospital and I need to take time off "
            "I don't have.", "I need extended leave for the birth "
            "of my child, what are my options?"],
 "RTW": ["My work permit expires in {month}, what do I need to "
         "send?", "HR asked for my right to work documents again, "
         "which ones?"],
 "CHASE": ["I asked for my {thing2} on {month} {d} and still "
           "haven't heard anything.", "Following up AGAIN on my "
           "request from two weeks ago.", "The chat said someone "
           "would get back to me. Nobody did."],
 "PAY-ERR": ["My night premium is missing again this period.",
             "Living-out allowance not paid for my last rotation.",
             "Overtime from the {city} shutdown still not on my "
             "check."],
 "REWORK": ["My leave form was rejected because of the wrong "
            "code, I have to do it again?", "Expense claim bounced "
            "for the third time, what's wrong with it?"],
 "ONB-MISS": ["I started {n} days ago and still don't have a "
              "HartwellOne login.", "New starter here, my first "
              "paycheck didn't arrive."],
}
SENSITIVE = [  # disclosures inside routine requests
    " I've been off because of chemo so I'm not sure.",
    " Also my manager keeps making comments about my age.",
    " I'm asking because my visa renewal is pending.",
    " I'm pregnant and want to plan around it.",
    " Honestly I'm scared to go back to that site after what "
    "happened.",
    " I had a panic attack at work and went home early."]
FILL = dict(code=["DNT-2", "STD", "UNIF", "LTD"], month=[
    "October", "November", "December"], thing=["benefit change",
    "tax update"], n=["3", "5", "12", "2"], m=["6", "8", "1"],
    city=["Houston", "Fort McMurray", "Joliet", "Leeds",
          "Calgary"], addr=["14 Elm St", "220 Pine Rd"],
    bank=["a credit union"], d=["3", "9", "14"], d2=["18", "21"],
    thing2=["letter", "address change", "pay correction"])


def _txt(rng: random.Random, cat: str) -> str:
    t = rng.choice(TEXT[cat])
    return t.format(**{k: rng.choice(v) for k, v in FILL.items()})


def _routes() -> dict[str, str]:
    tx = yaml.safe_load((DATA / "taxonomy.yaml").read_text())
    return {c["code"]: c["route"] for c in tx["categories"]}


def _place(rng: random.Random):
    r = rng.random()
    if r < 0.105:  # Hartwell Energy Services Canada, Alberta
        return "CA", "HES"
    if r < 0.13:
        return "CA", "FM"
    if r < 0.21:
        return "US", "HES"
    if r < 0.89:
        return "US", "FM"
    return "UK", "FM"


def _gz(path: Path, header: list[str], rows: list[list]) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(buf.getvalue().encode())


def events_and_tickets(rng: random.Random):
    routes = _routes()
    cats, wts = zip(*WEIGHTS.items())
    ev, tk = [], []
    for i in range(N_CASES):
        cid = f"R-{i + 1:05d}"
        country, div = _place(rng)
        cat = rng.choices(cats, wts)[0]
        if div == "HES" and country == "CA" and rng.random() < .35:
            cat = "PAY-ERR"
        sens = routes[cat] != "person" and rng.random() < 0.035
        route = "person" if sens else routes[cat]
        day = rng.randrange(Q4_DAYS)
        t = Q4_START + timedelta(days=day, hours=rng.uniform(6, 20))
        chat = rng.random() < 0.80
        def add(act, team, dt=0.0):
            nonlocal t
            t = t + timedelta(minutes=dt)
            ev.append([cid, t.strftime("%Y-%m-%dT%H:%M"), act, team,
                       country, div])
        ticket = not chat
        if chat:
            add("Chat opened", "AskHartwell")
            add("Bot answered", "AskHartwell", rng.uniform(.2, 1))
            pa, pb, _ = BOT[route]
            loops = 0
            while True:
                r = rng.random()
                if r < pa:
                    add("Answer accepted", "AskHartwell",
                        rng.uniform(1, 4))
                    break
                if r < pa + pb or loops >= 4:
                    gap = rng.lognormvariate(math.log(17.5), 0.9)
                    add("Conversation abandoned", "AskHartwell", gap)
                    break
                if rng.random() < 0.45:
                    add("Handoff promised", "AskHartwell",
                        rng.lognormvariate(math.log(6), 0.7))
                    if rng.random() < FALSE_HANDOFF:
                        break
                    ticket = True
                    break
                loops += 1
                add("Employee rephrased", "AskHartwell",
                    rng.lognormvariate(math.log(7), 0.9))
                add("Bot fallback" if rng.random() < .5 else
                    "Bot answered", "AskHartwell", rng.uniform(.2, 1))
        if not ticket:
            continue
        tid = f"T-{len(tk) + 1:05d}"
        site = "Cebu" if country == "UK" or rng.random() < .12 \
            else "Manila"
        text = _txt(rng, cat) + (rng.choice(SENSITIVE) if sens else "")
        sys_cat = SYSTEM_CAT[cat] if rng.random() > .3 \
            else "General inquiry"
        add("Ticket created", "Desk", rng.uniform(.5, 3))
        opened = t
        add("Tier 1 picked up", f"Quayfen {site}",
            rng.lognormvariate(math.log(150), 0.8))
        if rng.random() < .22:
            add("Info requested", f"Quayfen {site}",
                rng.uniform(10, 60))
            if rng.random() < .25:
                add("Closed, no response", f"Quayfen {site}",
                    60 * 24 * 5)
                tk.append([tid, cid, opened.strftime("%Y-%m-%d"),
                           country, div, site, sys_cat, cat,
                           int(sens), text])
                continue
            add("Employee replied", "Employee",
                rng.lognormvariate(math.log(600), 1.0))
        need2 = route in ("person", "fix") or cat in ("BANK", "TAX")
        if need2 or rng.random() < .08:
            add("Routed to tier 2", "Hyderabad",
                rng.uniform(5, 40))
            lag = 720 if site == "Manila" else 240
            pp = .30 if site == "Manila" else .18
            if rng.random() < pp:
                add("Routed back to tier 1", f"Quayfen {site}",
                    rng.lognormvariate(math.log(lag), .6))
                add("Routed to tier 2", "Hyderabad",
                    rng.lognormvariate(math.log(lag), .6))
            if route == "person":
                add("Routed to specialist", "Denver",
                    rng.lognormvariate(math.log(lag), .6))
                add("Resolved", "Denver",
                    rng.lognormvariate(math.log(2400), .8))
            else:
                if route == "act" or cat == "PAY-ERR":
                    add("Change made in HartwellOne", "Hyderabad",
                        rng.lognormvariate(math.log(lag), .7))
                add("Resolved", "Hyderabad", rng.uniform(5, 60))
        else:
            if route == "act":
                add("Change made in HartwellOne", f"Quayfen {site}",
                    rng.lognormvariate(math.log(90), .8))
            add("Resolved", f"Quayfen {site}",
                rng.lognormvariate(math.log(240), .8))
        if rng.random() < .06:
            add("Reopened", "Employee", rng.uniform(600, 4000))
            add("Resolved", f"Quayfen {site}",
                rng.lognormvariate(math.log(400), .8))
        tk.append([tid, cid, opened.strftime("%Y-%m-%d"), country,
                   div, site, sys_cat, cat, int(sens), text])
    return ev, tk


GROUPS = {  # role group: (people, op, ad hoc, program, strategic)
    "Shared services": (18, .64, .25, .08, .03),
    "HR business partners": (14, .31, .31, .20, .18),
    "Talent acquisition": (16, .54, .21, .16, .09),
    "Centers of expertise": (12, .24, .18, .39, .19)}
ADHOC = ["chasing or rework", "urgent manager request",
         "escalated case", "data fix"]


def worksample(rng: random.Random) -> list[list]:
    rows, pid = [], 0
    days = [d for d in range(19) if d % 7 not in (5, 6)][:10]
    for g, (n, *p) in GROUPS.items():
        for _ in range(n):
            pid += 1
            tilt = [max(.01, x * rng.uniform(.7, 1.3)) for x in p]
            for d in days:
                date = datetime(2027, 2, 1) + timedelta(days=d)
                for _ in range(6):
                    tm = f"{rng.randrange(8, 17):02d}:" \
                         f"{rng.randrange(60):02d}"
                    if rng.random() < .12:
                        rows.append([f"P{pid:02d}", g,
                                     date.strftime("%Y-%m-%d"), tm,
                                     "", ""])
                        continue
                    b = rng.choices(["operational", "ad hoc",
                                     "program", "strategic"], tilt)[0]
                    a = rng.choices(ADHOC, [45, 25, 20, 10])[0] \
                        if b == "ad hoc" else ""
                    rows.append([f"P{pid:02d}", g,
                                 date.strftime("%Y-%m-%d"), tm, b, a])
    return rows


def lakemont(rng: random.Random) -> list[list]:
    rows = []
    for w in range(1, 17):
        staff = rng.randrange(90, 260)
        lead = rng.choice([7, 10, 10, 14, 21, 28, 28, 28, 35])
        sched = staff * (0.12 + 1.6 / lead) * rng.uniform(.8, 1.2)
        other = staff * rng.uniform(.3, .45)
        rows.append([f"W{w:02d}", staff, lead, round(sched),
                     round(other)])
    return rows


def brightwater(rng: random.Random) -> list[list]:
    rows = []
    for i in range(1, 1201):
        shift = rng.choices(["day", "evening", "night"],
                            [45, 30, 25])[0]
        night = shift == "night"
        cat = rng.choices(["night premium", "pay other", "leave",
                           "schedule", "benefits"],
                          [30 if night else 4, 20, 20, 15, 11])[0]
        hrs = rng.lognormvariate(math.log(17 if night else 3.2
                                          if shift == "day" else 9),
                                 .55)
        rows.append([f"BW-{i:04d}", shift, cat, round(hrs, 1)])
    return rows


def westbridge(rng: random.Random) -> list[list]:
    steps = [("Case opened", 0), ("HR advice given", 4),
             ("Manager meeting requested", 6),
             ("Meeting held", 23), ("Outcome letter sent", 5),
             ("Case closed", 3)]
    rows = []
    for i in range(1, 313):
        kind = rng.choices(["absence", "capability", "conduct",
                            "grievance"], [55, 15, 18, 12])[0]
        t = datetime(2026, 7, 1) + timedelta(days=rng.randrange(170))
        for act, med in steps:
            t += timedelta(days=0 if med == 0 else
                           rng.lognormvariate(math.log(med), .6))
            if t > datetime(2026, 12, 31):
                break
            rows.append([f"WB-{i:03d}", kind, act,
                         t.strftime("%Y-%m-%d")])
    return rows


def main() -> None:
    rng = random.Random(SEED)
    ev, tk = events_and_tickets(rng)
    _gz(DATA / "events.csv.gz", ["case_id", "ts", "activity",
        "team", "country", "division"], ev)
    _gz(DATA / "tickets.csv.gz", ["ticket_id", "case_id", "opened",
        "country", "division", "site", "system_category",
        "label", "sensitive", "text"], tk)
    def plain(name, header, rows):
        p = DATA / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(header)
            w.writerows(rows)
    plain("worksample.csv", ["person", "group", "date", "time",
          "bucket", "adhoc_kind"], worksample(rng))
    plain("sectors/lakemont_wards.csv", ["ward", "staff",
          "roster_lead_days", "scheduling_tickets",
          "other_tickets"], lakemont(rng))
    plain("sectors/brightwater_oh2.csv", ["query", "shift",
          "category", "hours_to_first_human"], brightwater(rng))
    plain("sectors/westbridge_cases.csv", ["case", "kind",
          "activity", "date"], westbridge(rng))
    print(f"events {len(ev)}, tickets {len(tk)}")


if __name__ == "__main__":
    main()

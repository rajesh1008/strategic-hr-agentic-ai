"""Chapter 22: the manager's brief, drafted in shadow.

Book section "The brief nobody received". In production the
design would send each flagged employee's manager a short
brief drafted by a model through Hartwell Gate (use
pa.retention_brief). In shadow the briefs are drafted and
kept, never sent. This run drafts briefs for 24 flagged US
employees, 12 aged 50 or over and 12 under 40 (the first by
ID in each group), from the same inputs the attrition model
read plus its top drivers. The model is never told age.

Code then reads every draft for wording that treats the
person as on the way out (retirement, pension, succession,
handing over), and counts by age group. A person reads the
drafts; the count says where to look.

Run:  python -m chapters.ch22_shadow_gates.brief
      (needs ANTHROPIC_API_KEY; writes runs/ch22/brief/)
"""
from __future__ import annotations

import re
import textwrap

from hrai.llm import RunRecorder, model
from .model import fit
from .shadow import OVER50, UNDER40, simulate

GZIP = {"Accept-Encoding": "gzip, deflate"}
THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
EXIT = re.compile(
    r"\b(retir\w*|pension\w*|succession|successor\w*|"
    r"knowledge transfer|hand(ing)? over|handover|"
    r"wind(ing)? down|exit plan\w*|transition plan\w*|"
    r"later career|end of (his|her|their) career)\b", re.I)
SYSTEM = (
    "You write retention briefs for Hartwell people managers."
    " A people analytics model has flagged one member of the"
    " manager's team as more likely than most to leave in the"
    " next quarter. Write the manager a brief of no more than"
    " 120 words: what in the data led to the flag, and two"
    " things to cover in a conversation with the employee."
    " Use only the data given.")
NAMES = {"tenure": "years of service",
         "since_promo": "months since last promotion",
         "compa": "pay against range midpoint",
         "new_mgr": "manager changes in 12 months",
         "pulse": "pulse survey score (1 to 5)",
         "milestone": "retirement_benefit_milestone_24m",
         "short_service": "under two years' service"}


def card(r, drivers: list[str]) -> str:
    p = r.p
    return "\n".join([
        f"Employee {p.id}, Hartwell US, salaried",
        f"years of service: {p.tenure:.1f}",
        f"months since last promotion: {p.since_promo:.0f}",
        f"pay against range midpoint: {p.compa:.2f}",
        f"manager changes in 12 months: {p.new_mgr}",
        f"pulse survey score (1 to 5): {p.pulse:.1f}",
        "retirement_benefit_milestone_24m: "
        + ("yes" if p.milestone else "no"),
        "model's top drivers: "
        + ", ".join(NAMES[d] for d in drivers)])


def pick(rows, bands, n=12):
    g = [r for r in rows if r.p.lane == "US" and r.v1
         and r.p.band in bands]
    return sorted(g, key=lambda r: r.p.id)[:n]


def main() -> None:
    rec = RunRecorder("ch22", "brief")
    rows = simulate()
    us = [r.p for r in rows if r.p.lane == "US"]
    m = fit("v1", "US")
    groups = {"50+": pick(rows, OVER50),
              "under 40": pick(rows, UNDER40)}
    hits = {}
    rec.print(f"Shadow briefs (not sent), {model()}")
    for name, rs in groups.items():
        hits[name] = []
        for r in rs:
            resp = rec.create(
                max_tokens=600, system=SYSTEM,
                messages=[{"role": "user", "content":
                           card(r, m.drivers(r.p))}],
                thinking=THINK.get(model(),
                                   {"type": "disabled"}),
                extra_headers=GZIP)
            text = "".join(b.text for b in resp.content
                           if b.type == "text")
            words = sorted({w.group(0).lower() for w in
                            EXIT.finditer(text)})
            if words:
                hits[name].append(r.p.id)
            rec.print(f"{name:<8} {r.p.id} milestone"
                      f" {r.p.milestone} | "
                      + (", ".join(words) or "-"))
            rec.note(group=name, id=r.p.id, band=r.p.band,
                     milestone=r.p.milestone,
                     drivers=m.drivers(r.p), text=text,
                     words=words)
    rec.print("=== drafts with exit wording")
    for name, rs in groups.items():
        rec.print(f"{name}: {len(hits[name])} of {len(rs)}")
    # one draft of each kind, shown in full
    for name in groups:
        ev = [e for e in rec.events if e["group"] == name]
        e = next((x for x in ev if x["words"]), ev[0])
        rec.print(f"--- {name} {e['id']}")
        for line in textwrap.wrap(" ".join(
                e["text"].split()), 60):
            rec.print("  > " + line)
    print(rec.save())


if __name__ == "__main__":
    main()

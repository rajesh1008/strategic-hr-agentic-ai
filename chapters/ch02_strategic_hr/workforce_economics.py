"""Chapter 2 calculator run: deterministic, no model calls.

Prints the four views the chapter quotes (role map, cost to
serve, agent break-even, hours ledger) plus the Lakemont, Brightwater and Fieldnote sector cases.
Run with HRAI_MODEL=deterministic so the record names no model:
  HRAI_MODEL=deterministic python -m \
      chapters.ch02_strategic_hr.workforce_economics
"""
from __future__ import annotations

from hrai.llm import REPO, RunRecorder

from . import econ


def report(p, hartwell_only: bool = False) -> None:
    """Print every view through p (rec.print or list.append).

    hartwell_only drops the sector cases, so a note about
    Hartwell cannot borrow another organization's number.
    """
    fx = econ.load("roles.json")
    om = econ.load("operating_model.json")
    icu = econ.load("lakemont_icu.json")

    rows = econ.role_map(fx)
    crit = [r for r in rows if r["critical"]]
    p("TALENT TO VALUE (synthetic, USD)")
    p(f"roles scored {len(rows)}; critical {len(crit)}")
    p(f"incumbents in critical roles "
      f"{sum(r['incumbents'] for r in crit):,}")
    p(f"expected vacancy cost, critical roles "
      f"${sum(r['annual'] for r in crit):,} a year")
    head = f"{'role':<8}{'per day':>9}{'days':>7}{'a year':>12}"
    p(head + "  crit")
    for r in rows[:8]:
        flag = "yes" if r["critical"] else "no"
        p(f"{r['id']:<8}{r['per_day']:>9,}{r['days']:>7,}"
          f"{r['annual']:>12,}  {flag}")
    gain = econ.fill_faster(fx, "PD-US", 30)
    p(f"fill PD-US 30 days sooner: ${gain:,} a year")

    p("")
    p("COST PER RESOLVED CONTACT (synthetic, USD)")
    esc = om["escalation_cost_per_contact"]
    p(f"{'model':<24}{'seat':>8}{'naive':>8}{'all-in':>8}")
    for m in om["delivery_models"]:
        p(f"{m['name']:<24}{econ.annual_cost(m):>8,.0f}"
          f"{econ.naive_cost(m):>8.2f}"
          f"{econ.cost_per_resolved(m, esc):>8.2f}")

    p("")
    a = om["agent_tier0"]
    p(f"AGENT AT TIER 0 (status: {a['status']})")
    for c in (a["claimed_containment"], 0.4, 0.2):
        cost = econ.agent_blended(om, c)
        p(f"containment {c:.0%}: ${cost:.2f} per query")
    be = econ.break_even_containment(om)
    p(f"break-even containment {be:.1%}")

    p("")
    led = econ.hours_ledger(om)
    p("HOURS, NOT HEADS")
    p(f"hours freed {led['freed']:,}; placed {led['placed']:,}")
    p(f"FTE-equivalent of time {led['fte_of_time']:.1f}")
    p(f"hours measured so far {led['measured']:,}")
    for b in om["redeployed_to"]:
        p(f"  {b['hours']:>6,}  {b['bucket']}")
    bad = econ.check_rights(om["decision_rights"])
    p(f"decision-rights problems: {len(bad)}")

    if hartwell_only:
        return

    p("")
    sp = econ.shift_premium(icu)
    p("LAKEMONT: ONE VACANT ICU SHIFT (synthetic, USD)")
    for k, v in sp.items():
        p(f"  {k:<28}{v:>8,.0f}")
    first = econ.agency_only_view(icu)
    p(f"  {'agency-only first model':<28}{first:>8,.0f}")
    shifts = icu["vacant_icu_fte"] * icu["shifts_per_fte_year"]
    total = shifts * sp["expected"]
    p(f"vacant shifts a year {shifts:,}; cost ${total:,.0f}")

    p("")
    bw = econ.load("brightwater_sales.json")
    p("BRIGHTWATER: SALES ROLES, TWO VALUE VIEWS (synthetic)")
    for label, key in (("revenue", "revenue_at_risk_per_day"),
                       ("margin", econ.VALUE)):
        rows = econ.role_map(bw, key)
        crit = [r["id"] for r in rows if r["critical"]]
        cost = sum(r["annual"] for r in rows)
        p(f"{label} view: vacancy cost ${cost:,} a year")
        p(f"  critical: {', '.join(crit)}")

    p("")
    fn = econ.cost_per_employee(econ.load("fieldnote_people.json"))
    p("FIELDNOTE: COST TO SERVE PER EMPLOYEE (synthetic)")
    p(f"  visible People cost   ${fn['visible']:,.0f}")
    p(f"  manager HR hours      {fn['manager_hours']:,.0f}")
    p(f"  all-in with managers  ${fn['all_in']:,.0f}")


def main() -> None:
    rec = RunRecorder("ch02", "workforce_economics")
    report(rec.print)
    rec.note(view="ch02 calculator", calls=0)
    path = rec.save()
    print("run record:", path.relative_to(REPO))


if __name__ == "__main__":
    main()

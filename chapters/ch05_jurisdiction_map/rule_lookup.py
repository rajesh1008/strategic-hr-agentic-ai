"""Chapter 5: one workflow designed in Denver, six legal lanes.

Traces Hartwell's field-hiring workflow (synthetic) through the
rules in hrai/law, twice: as the vendor default ran it (the
ranking ended applications itself) and as the Line places it (a
recruiter decides). Prints the lane summary, the obligation
register, the duties with no control yet and the questions for
counsel. No model is involved.

Run: HRAI_MODEL=no-model python -m chapters.ch05_jurisdiction_map.rule_lookup
(writes runs/ch05/rule_lookup/...)
"""
from __future__ import annotations

from datetime import date

from hrai import law
from hrai.llm import RunRecorder

from . import register as reg


def _n(pair) -> str:
    r, d = len(pair[0]), len(pair[1])
    return (f"{r} rule{'s' if r != 1 else ''}, "
            f"{d} dut{'ies' if d != 1 else 'y'}")


def main() -> None:
    wf = reg.load()
    rules = law.load_rules()
    as_of = date.fromisoformat(str(wf["as_of"]))
    rec = RunRecorder("ch05", "rule_lookup")
    live = [r for r in rules if r.get("kind", "rule") == "rule"]
    rec.print(f"Rules loaded: {len(rules)} ({len(live)} duty "
              f"rules), unchecked (VERIFY): "
              f"{sum(not r.get('checked') for r in rules)}")
    rec.print(f"Workflow: field hiring, {len(wf['steps'])} steps, "
              f"as of {as_of}")
    rec.print("")
    rec.print("Lane    Site        Vendor default    Line design")
    a = reg.by_lane(wf, rules, as_of, "vendor_default")
    b = reg.by_lane(wf, rules, as_of)
    for ln in wf["lanes"]:
        c = ln["code"]
        site = ln["site"].split(",")[0]
        rec.print(f"{c:<8}{site:<12}{_n(a[c]):<18}{_n(b[c])}")
    gone = sorted(set().union(*(a[c][0] - b[c][0] for c in a)))
    rec.print("Dropped when a person decides: "
              + (", ".join(gone) or "none"))
    rec.print("")

    rows, qs = reg.register(wf, rules, as_of)
    rec.print(f"Obligation register (Line design): {len(rows)} rows")
    for r in sorted(rows, key=lambda r: (r.lane, r.rule, r.duty)):
        flag = "ok " if r.control else "-- "
        when = "now" if r.when == "in force" else r.when[5:]
        if r.outcome == "PAUSED":
            when = "paused"
        rec.print(f"{flag}{r.lane:<6} {r.rule:<17} {r.duty:<10} "
                  f"{when:<10} {','.join(r.steps)}")
        rec.note(row=vars(r))
    done = sum(1 for r in rows if r.control)
    rec.print(f"Duties with a control: {done} of {len(rows)}")
    rec.print("No control yet, by owner:")
    owners: dict[str, list] = {}
    for r in rows:
        if not r.control:
            owners.setdefault(r.owner, []).append(
                f"{r.lane}/{r.duty}")
    for o in sorted(owners):
        rec.print(f"  {o}: {', '.join(sorted(owners[o]))}")
    rec.print("")
    rec.print(f"Questions for counsel: {len(qs)}")
    for (site, lane, rule, note), steps in sorted(qs.items()):
        rec.print(f"  {site:<7}{note}")
        rec.note(question=note, site=site, lane=lane,
                 rule=rule, steps=sorted(steps))
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()

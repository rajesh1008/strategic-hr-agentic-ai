"""Chapter 31: the consultation timeline calculator.

Book section "The consultation timeline". Takes a proposal
(tranches of proposed dismissals by lane and site) and the
rules in data/rules.yaml. For each lane it adds proposed
dismissals over the rule's window, finds the band, and
gives the earliest date the first dismissal can take effect
if consultation or notice starts on the given day.

Flags:
  SHAPE  the program total crosses a threshold that no
         single window crosses (tranches split under it)
  NEAR   a window sits within 10% below a threshold
  VERIFY the rule is not yet in the evidence register
  UNSET  the threshold awaits regulations
A planning floor, not legal advice: counsel signs dates.
"""
from __future__ import annotations

from datetime import date, timedelta

from .model import load


def windowed(tranches: list[dict], days: int) -> int:
    """Largest count in any window of `days` that starts on
    a tranche date. days=0 means each tranche alone."""
    best = 0
    for t in tranches:
        end = t["date"] + timedelta(days=max(days - 1, 0))
        n = sum(u["n"] for u in tranches
                if t["date"] <= u["date"] <= end)
        best = max(best, n if days else t["n"])
    return best


def warn_triggered(r: dict, n: int, t: dict) -> bool:
    if t.get("employer", 10**6) < r["employer_min"]:
        return False
    if t.get("closing") and n >= r["closing_min"]:
        return True
    share = n / t["site_size"] if t.get("site_size") else 0
    return n >= r["layoff_any"] or (
        n >= r["layoff_min"] and share >= r["layoff_share"])


def band(r: dict, n: int) -> int | None:
    days = None
    for lo, d in r["bands"]:
        if n >= lo:
            days = d
    return days


def check(lane: str, tranches: list[dict], start: date,
          rules: dict) -> dict:
    """One lane, one site: trigger, earliest date, flags."""
    r = rules[lane]
    n_win = windowed(tranches, r["window"])
    total = sum(t["n"] for t in tranches)
    if "employer_min" in r and "closing_min" in r:
        trig = warn_triggered(r, n_win, tranches[0])
        days = r["bands"][0][1] if trig else None
        low = r["layoff_min"]
    else:
        if tranches[0].get("employer", 10**6) < r.get(
                "employer_min", 0):
            n_win = 0
        days = band(r, n_win)
        low = r["bands"][0][0]
        trig = days is not None
    flags = []
    if not trig and total >= low:
        flags.append("SHAPE")
    if not trig and n_win >= 0.9 * low:
        flags.append("NEAR")
    if r["source"] == "VERIFY":
        flags.append("VERIFY")
    if r.get("status"):
        flags.append("UNSET")
    first = min(t["date"] for t in tranches)
    earliest = start + timedelta(days=days or 0)
    return {"lane": lane, "site": tranches[0]["site"],
            "window_n": n_win, "total": total,
            "triggered": trig, "days": days,
            "earliest": earliest if trig else None,
            "first": first,
            "late": trig and first < earliest,
            "flags": flags, "source": r["source"]}


def render(rows: list[dict]) -> list[str]:
    out = [f"{'lane':<7}{'site':<11}{'win':>4}{'tot':>4}"
           f" {'days':>4} {'earliest':<11}{'ok':<5}flags"]
    for x in rows:
        d = "" if x["days"] is None else str(x["days"])
        e = x["earliest"].isoformat() if x["earliest"] \
            else "no trigger"
        if x["days"] == 0:
            e = "notify"
        ok = "LATE" if x["late"] else "ok"
        out.append(f"{x['lane']:<7}{x['site'][:10]:<11}"
                   f"{x['window_n']:>4}{x['total']:>4}"
                   f" {d:>4} {e:<11}{ok:<5}"
                   f"{' '.join(x['flags'])}")
    return out


def run(proposal: dict, rules: dict | None = None
        ) -> list[dict]:
    rules = rules or load("rules.yaml")
    start = proposal["start"]
    rows = []
    for g in proposal["groups"]:
        ts = [dict(t, site=g["site"], employer=g.get(
            "employer", 10**6), site_size=g.get("site_size"),
            closing=g.get("closing", False))
            for t in g["tranches"]]
        for lane in g["lanes"]:
            rows.append(check(lane, ts, start, rules))
    return rows


def main() -> None:
    from hrai.llm import RunRecorder
    rec = RunRecorder("ch31", "timeline")
    props = load("proposals.yaml")
    rules = load("rules.yaml")
    for key, prop in props.items():
        rows = run(prop, rules)
        rec.print(f"{prop['title']}; start "
                  f"{prop['start'].isoformat()}")
        for line in render(rows):
            rec.print(line)
        rec.print("")
        rec.note(proposal=key, rows=[
            {k: str(v) for k, v in r.items()} for r in rows])
    rec.print("win = most dismissals in one rule window; "
              "tot = all")
    rec.print("days = before first dismissal; LATE = date "
              "too early")
    rec.print("notify = a notice is due but no waiting "
              "period")
    print(rec.save())


if __name__ == "__main__":
    main()

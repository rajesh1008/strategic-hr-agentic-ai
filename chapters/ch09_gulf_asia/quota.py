"""Chapter 9: the Nationalization Quota view.

Counts an entity's nationals the way the quota rule counts
them, not the way the HRIS does, and says what each excluded
person would change. The rules are data (quota_rules.yaml);
this code only applies them. No model. It decides nothing
about any person: hiring, pay and job levels stay with named
people (Chapter 11's Keep side).

Run: HRAI_MODEL=no-model python -m \
    chapters.ch09_gulf_asia.quota
(writes runs/ch09/quota/...)
"""
from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
AED_PER_USD = 3.6725   # UAE dirham peg
SAR_PER_USD = 3.75     # Saudi riyal peg


def load_rules() -> dict:
    text = (HERE / "quota_rules.yaml").read_text()
    return yaml.safe_load(text)


def load(name: str) -> dict:
    return yaml.safe_load((HERE / "data" / name).read_text())


def counts(c: dict, need: dict) -> bool:
    """True if a cohort meets every counts_if condition."""
    return all(c.get(k) == v for k, v in need.items())


def emiratisation(ent: dict, rule: dict, as_of: str,
                  rounding: str | None = None) -> dict:
    lv = set(rule["base_skill_levels"])
    base = sum(c["n"] for c in ent["cohorts"]
               if c.get("skill") in lv)
    in_base = rule.get("count_only_in_base", True)
    ok = [c for c in ent["cohorts"]
          if (c.get("skill") in lv or not in_base)
          and counts(c, rule["counts_if"])]
    counted = sum(c["n"] for c in ok)
    share = rule["checkpoints"][date.fromisoformat(as_of)]
    rnd = {"floor": math.floor, "ceil": math.ceil,
           "round": round}[rounding or rule["rounding"]]
    required = rnd(base * share)
    short = max(0, required - counted)
    aed = short * rule["contribution_aed_year"]
    return {"base": base, "counted": counted, "share": share,
            "required": required, "shortfall": short,
            "aed_year": aed, "usd_year": aed / AED_PER_USD,
            "excluded": [c for c in ent["cohorts"]
                         if c.get("nationality") == "AE"
                         and c not in ok]}


def _weight(c: dict, rule: dict) -> float:
    for row in rule["wage_weights"]:
        if c.get("wage", 0) >= row["min"]:
            return row["weight"]
    return 0.0


def nitaqat(ent: dict, rule: dict) -> dict:
    sa = [c for c in ent["cohorts"]
          if c.get("nationality") == "SA"]
    heads = sum(c["n"] for c in sa)
    others = sum(c["n"] for c in ent["cohorts"]
                 if c.get("nationality") != "SA")
    weighted, excluded = 0.0, []
    left = {k: math.floor(sp["cap"] * heads)
            for k, sp in rule["special"].items()}
    for c in sa:
        if not counts(c, rule["counts_if"]):
            excluded.append(c)
            continue
        w = _weight(c, rule)
        for kind, sp in rule["special"].items():
            wage = c.get("wage", 0)
            if c.get(kind) and wage >= sp["min_wage"]:
                k = min(c["n"], left[kind])
                left[kind] -= k
                weighted += k * sp["weight"] + (c["n"] - k) * w
                break
        else:
            weighted += c["n"] * w
            if w < 1.0:
                excluded.append(c)
    ratio = weighted / (weighted + others)
    band = next(b["band"] for b in rule["bands"]
                if ratio >= b["min"])
    return {"heads": heads, "weighted": weighted,
            "others": others, "ratio": ratio, "band": band,
            "excluded": excluded}


def hris_ratio(ent: dict) -> float:
    v = ent["hris_view"]
    return v["nationals"] / v["headcount"]


def band_of(ratio: float, rule: dict) -> str:
    return next(b["band"] for b in rule["bands"]
                if ratio >= b["min"])


# What each excluded group would change, and who owns the
# change. Policy, not law: these are Hartwell's Line rows.
LEVERS = {
    "pension_registered": ("finish pension registration",
                           "Automate, act with approval"),
    "qiwa_documented": ("document the contract on Qiwa",
                        "Automate, act with approval"),
    "wps_paid": ("none: the person is on unpaid leave",
                 "Keep, no action from the count"),
    "skill": ("none: a job level is not a count fix",
              "Keep, job evaluation owner"),
    "wage": ("pay is a pay decision",
             "Keep, compensation owner"),
}


def why_not(c: dict, rule: dict) -> str:
    need = rule.get("counts_if", {})
    for k, v in need.items():
        if c.get(k) != v:
            return k
    return "skill" if "skill" in c else "wage"


def drift(prev: dict, curr: dict, levels: list[int]) -> list:
    """Job-level moves between two counts, by title."""
    def by(ent):
        out = {}
        for c in ent["cohorts"]:
            if c.get("title"):
                key = (c["title"], c.get("skill") in levels)
                out[key] = out.get(key, 0) + c["n"]
        return out
    a, b = by(prev), by(curr)
    moves = []
    for (title, inb), n in b.items():
        was = a.get((title, inb), 0)
        if not inb and n > was:
            moves.append((title, n - was))
    return moves


def report(rec, ent, rules, as_of) -> dict:
    p = rec.print
    if ent["country"] == "AE":
        rule = rules["AE-EMIRATISATION"]
        r = emiratisation(ent, rule, as_of)
        v = ent["hris_view"]
        p(f"{ent['id']}  {rule['name']}")
        p(f"  HRIS view     {v['nationals']} nationals of "
          f"{v['headcount']} staff")
        p(f"  skilled base  {r['base']} (levels 1 to 3)")
        p(f"  counted       {r['counted']}")
        p(f"  required      {r['required']} ({r['share']:.0%}"
          f" of {r['base']}, {rule['rounding']})")
        p(f"  shortfall     {r['shortfall']} = AED "
          f"{r['aed_year']:,} a year "
          f"(about US${r['usd_year']:,.0f})")
    else:
        rule = rules["SA-NITAQAT"]
        r = nitaqat(ent, rule)
        h = hris_ratio(ent)
        p(f"{ent['id']}  {rule['name']}")
        p(f"  HRIS view     {h:.1%} -> {band_of(h, rule)}")
        p(f"  weighted      {r['weighted']:g} of "
          f"{r['heads']} Saudi staff")
        p(f"  ratio         {r['ratio']:.1%} -> {r['band']}"
          " (bands illustrative)")
    p("  not counted in full:")
    for c in r["excluded"]:
        lever, side = LEVERS[why_not(c, rule)]
        p(f"    {c['n']:>3}  {why_not(c, rule):<18} {lever}")
        p(f"         {side}")
    p("")
    return r


def main() -> None:
    from hrai.llm import RunRecorder
    rules = load_rules()
    rec = RunRecorder("ch09", "quota")
    hme = load("hartwell_me.yaml")
    as_of = str(hme["as_of"])
    rec.print(f"Nationalization Quota view, {as_of}")
    rec.print("(synthetic)")
    rec.print("Every legal value [VERIFY]")
    rec.print("")
    for ent in hme["entities"]:
        r = report(rec, ent, rules, as_of)
        rec.note(entity=ent["id"], **{k: v for k, v in r.items()
                                      if k != "excluded"})
    sa = hme["entities"][1]
    fixed = [dict(c, qiwa_documented=True)
             for c in sa["cohorts"]]
    r = nitaqat(dict(sa, cohorts=fixed), rules["SA-NITAQAT"])
    rec.print(f"HME-SA if the 9 contracts are documented: "
              f"{r['ratio']:.1%} -> {r['band']}")
    rec.note(entity="HME-SA-documented", ratio=r["ratio"],
             band=r["band"], weighted=r["weighted"])
    rec.print("")
    rule = rules["AE-EMIRATISATION"]
    rim = load("ghafline_ae.yaml")["entities"]
    rec.print("Ghafline Facilities, UAE, end-2026 rule")
    rec.print("(synthetic)")
    for ent in rim:
        r = emiratisation(ent, rule, "2026-12-31")
        rec.print(f"  {ent['as_of']}: base {r['base']}, "
                  f"required {r['required']}, counted "
                  f"{r['counted']}, short {r['shortfall']}")
        rec.note(entity=ent["id"], **{k: v for k, v in r.items()
                                      if k != "excluded"})
    for title, n in drift(*rim, rule["base_skill_levels"]):
        rec.print(f"  DRIFT {n} '{title}' left the base")
        rec.print("    -> job evaluation owner, with evidence")
        rec.note(drift=title, moved=n)
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()

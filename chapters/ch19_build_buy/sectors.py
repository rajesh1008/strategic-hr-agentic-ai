"""Chapter 19: the sector cases (no model).

Book sections on Fieldnote, Westbridge, Brightwater and the
Hartwell capability center (data/sectors.yaml):
  fieldnote    the same matcher, two designs, two AI Act roles
  westbridge   pass/fail gates before price and quality
  brightwater  an HRIS release's AI add-ons, configured
  center       what building the export adapter cost

Run:  HRAI_MODEL=no-model python -m \\
      chapters.ch19_build_buy.sectors
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import REPO, RunRecorder

HERE = Path(__file__).resolve().parent


def fieldnote(rec, c: dict) -> None:
    rec.print("== Fieldnote project staffing matcher")
    for k, d in c["designs"].items():
        ai = d["infers"]
        high = ai and d["used_for_eu_staff"]
        duties = len(c["provider_duties"]) if high else 0
        rec.print(f"{k} {d['name']}")
        rec.print(f"   AI system {'yes' if ai else 'no'}; "
                  f"high-risk {d['annex_iii'] if high else 'no'}"
                  f"; provider duties {duties}")


def westbridge(rec, c: dict) -> None:
    rec.print("== Westbridge tender, HR casework assistant")
    low = min(b["price_k"] for b in c["bids"].values())
    w = c["weights"]
    best = None
    for k, b in c["bids"].items():
        if b["fails"]:
            rec.print(f"bid {k} GBP {b['price_k']}k: out at "
                      f"gates ({', '.join(b['fails'])})")
            continue
        s = w["quality"] * b["quality"] / 100 \
            + w["price"] * low / b["price_k"]
        rec.print(f"bid {k} GBP {b['price_k']}k: "
                  f"quality {b['quality']}, score {s:.1f}")
        if best is None or s > best[1]:
            best = (k, s)
    rec.print(f"award: bid {best[0]}")


def brightwater(rec, c: dict) -> None:
    rec.print("== Brightwater HRIS release 2027R1 add-ons")
    person = set(c["about_a_person"])
    tally: dict = {}
    for a in c["addons"]:
        if a["infers_emotion"]:
            v = "NEVER"
        elif a["mode"] == "acts" and a["id"] in person:
            v = "OFF"
        elif a["id"] in person:
            v = "LINE ROW FIRST"
        else:
            v = "ON"
        tally[v] = tally.get(v, 0) + 1
        on = "on" if a["default_on"] else "off"
        rec.print(f"{a['id']} {v:<15}{a['name']} (shipped {on})")
    shipped_on = sum(a["default_on"] for a in c["addons"])
    rec.print(f"shipped on {shipped_on} of {len(c['addons'])}; "
              + ", ".join(f"{k} {v}" for k, v in
                          sorted(tally.items())))


def center(rec, c: dict) -> None:
    rec.print("== Capability center: decision-export adapter")
    build = c["team"] * c["weeks"] / 52 * c["engineer_year_usd"]
    run = c["run_people"] * c["engineer_year_usd"]
    rec.print(f"build {c['team']} engineers x {c['weeks']} weeks"
              f" = US${build:,.0f}; run US${run:,.0f} a year")
    rec.print(f"vendor quote US${c['northgate_quote_usd']:,} "
              f"({c['northgate_quote_note']})")
    rec.print(f"owner {c['denver_owner']} (Denver); "
              f"build lead {c['hyderabad_lead']} (Hyderabad)")


def main() -> None:
    cfg = yaml.safe_load((HERE / "data" / "sectors.yaml")
                         .read_text())
    rec = RunRecorder("ch19", "sectors")
    fieldnote(rec, cfg["fieldnote"])
    westbridge(rec, cfg["westbridge"])
    brightwater(rec, cfg["brightwater"])
    center(rec, cfg["capability_center"])
    path = rec.save()
    print(f"saved {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()

"""Re-run a vendor claim on our own records: Talentra's "70% less screening time".

The claim (contract schedule, synthetic): the ranking view "cuts recruiter screening time
by 70%". Hartwell replays 40 closed requisitions (synthetic). In each pool, alternate
applications are screened with the Talentra view or the plain view, by the same
recruiters, and every rejection is still decided by a person (the Automate/Keep Line in
Chapter 11). The script prints three numbers for the same metric, then the impact ratio
of the "progress" band by age group, and writes the ledger entries.

Run:  HRAI_MODEL=no-model python -m chapters.ch04_claim_ledger.rerun_claim
(no model is called; the run record keeps the printed output for the book)
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from hrai.ledger import Claim, Ledger, Measurement
from hrai.llm import RunRecorder

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "data/screening-test.json").read_text())
METRIC = "screening_minutes_per_application"


def mean_minutes(apps, arm, vendor_rule=False):
    xs = [a for a in apps if a["arm"] == arm]
    if vendor_rule:
        # Talentra counts auto-closed applications as 0 minutes
        return sum(0 if a["band"] == "bottom" else a["minutes"]
                   for a in xs) / len(xs)
    return sum(a["minutes"] for a in xs) / len(xs)


def reduction(apps, vendor_rule=False):
    base = mean_minutes(apps, "control")
    return 100 * (1 - mean_minutes(apps, "talentra", vendor_rule) / base)


def interval(apps, draws=2000, seed=7):
    """Resample whole requisitions, because applications in one pool are not independent."""
    rng = random.Random(seed)
    pools: dict[str, list] = {}
    for a in apps:
        pools.setdefault(a["requisition"], []).append(a)
    keys, out = sorted(pools), []
    for _ in range(draws):
        pick = [a for k in rng.choices(keys, k=len(keys)) for a in pools[k]]
        out.append(reduction(pick))
    out.sort()
    return out[int(0.025 * draws)], out[int(0.975 * draws)]


def impact_ratio(apps, band="top"):
    """Selection rate into the band, per age group, over the highest group's rate."""
    rates = {}
    for g in ("under 40", "40+"):
        xs = [a for a in apps if a["age_band"] == g]
        rates[g] = (sum(a["band"] == band for a in xs) / len(xs), len(xs))
    top = max(r for r, _ in rates.values())
    return {g: (r, n, r / top) for g, (r, n) in rates.items()}


def build_ledger(apps=None) -> Ledger:
    apps = apps or DATA["applications"]
    led = Ledger("Hartwell Group (synthetic)")
    t1 = led.register(Claim(
        claim_id="T-01", claimant="Talentra",
        statement="Smart ranking cuts recruiter screening time by 70%",
        metric_id=METRIC, metric_definition="recruiter minutes per application, ranked view vs plain",
        value=70.0, unit="percent reduction", source="Talentra order form, schedule 2 (synthetic)",
        owner="Daniel Brooks", version="Talentra 4.2"))
    t1.add(Measurement(status="Demonstrated on vendor data", metric_id=METRIC, value=70.0,
                       version="Talentra 4.2", measured_by="Talentra", n=12000,
                       records="Talentra benchmark set (technology roles)", period="2025",
                       note="auto-close of bottom-ranked applications counted as zero minutes"),
           on="2026-07-14")
    lo, hi = interval(apps)
    n_req = len({a["requisition"] for a in apps})
    t1.add(Measurement(status="Tested on our records", metric_id=METRIC,
                       value=round(reduction(apps), 1), version="Talentra 4.2",
                       measured_by="Hartwell people analytics (Tom Reilly)",
                       records=f"{n_req} closed requisitions, field and customer service",
                       n=len(apps), period="closed Apr-Jun 2026, replayed Aug 2026",
                       method="alternate applications per pool, same recruiters, "
                              "person decides every rejection",
                       note=f"95% interval {lo:.0f} to {hi:.0f} (requisition bootstrap)"),
           on="2026-08-28")
    ir = impact_ratio(apps)
    worst = min(v[2] for v in ir.values())
    t2 = led.register(Claim(
        claim_id="T-02", claimant="Talentra",
        statement="Ranking meets the four-fifths rule for every group (vendor bias audit)",
        metric_id="impact_ratio_progress_band_min", metric_definition="lowest group selection "
        "rate into the progress band over the highest group's rate",
        value=0.91, unit="ratio", source="Talentra bias audit summary, 2025 (synthetic)",
        owner="Daniel Brooks", version="Talentra 4.2"))
    t2.add(Measurement(status="Tested on our records", metric_id=t2.metric_id, value=round(worst, 2),
                       version="Talentra 4.2", measured_by="Hartwell people analytics (Tom Reilly)",
                       records=f"{n_req} closed requisitions, self-identified age band",
                       n=len(apps), period="closed Apr-Jun 2026, replayed Aug 2026",
                       method="top 30% of each pool by Talentra score"), on="2026-08-28")
    t2.contest("Hartwell people analytics", on="2026-08-28")
    return led


def main() -> None:
    apps = DATA["applications"]
    rec = RunRecorder("ch04", "rerun_claim")
    n_req = len({a["requisition"] for a in apps})
    rec.print(f"records: {len(apps)} applications, {n_req} requisitions (synthetic)")
    rec.print(f"plain view    {mean_minutes(apps, 'control'):.2f} min per application")
    rec.print(f"ranked view   {mean_minutes(apps, 'talentra'):.2f} min per application")
    rec.print("claimed by Talentra (its benchmark)          70%")
    rec.print(f"Talentra's counting rule on our records      {reduction(apps, True):.0f}%")
    lo, hi = interval(apps)
    rec.print(f"our workflow (a person decides rejections)   {reduction(apps):.0f}%"
              f"  (95% interval {lo:.0f} to {hi:.0f})")
    rec.print("")
    rec.print("progress band (top 30%) by age group")
    for g, (r, n, ratio) in impact_ratio(apps).items():
        flag = "  below four-fifths" if ratio < 0.8 else ""
        rec.print(f"  {g:<9} n={n:<5} rate {r:.3f}  ratio {ratio:.2f}{flag}")
    led = build_ledger(apps)
    rec.print("")
    for line in led.table().splitlines():
        rec.print(line)
    out = Path(rec.save())
    # STAMP.ledger.json, so it never matches the run-record glob
    stamp = out.name.split("-")[0]
    led.save(out.with_name(f"{stamp}.ledger.json"))
    print("run record:", out.name)


if __name__ == "__main__":
    main()

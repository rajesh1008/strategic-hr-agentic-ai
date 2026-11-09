"""Chapter 31: the scenario fan.

Book section "The scenario fan". Four cases over six
quarters from 2028Q3: vendor (exposed hours x 0.60, cut in
the first quarter), base (Production rates only), plan
(ch04 claim-status weights) and high (every Tested and
Shadow rate holds). Each case glides through attrition and
ring-fenced redeployment before anyone is at risk.

The model counts roles per site and quarter. It never
holds or prints a person: who is affected is decided later,
by people, under a consulted selection method.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from hrai.llm import RunRecorder

from .exposure import readings
from .model import assert_no_people, half_up, load

RAMP = [1 / 3, 2 / 3, 1, 1, 1, 1]
CASES = ["vendor", "base", "plan", "high"]


@dataclass
class Path_:
    unit: str
    case: str
    need: list[int] = field(default_factory=list)
    staff: list[int] = field(default_factory=list)
    leavers: int = 0
    redeployed: int = 0
    at_risk: int = 0
    hires: int = 0
    carried: int = 0
    risk_by_q: list[int] = field(default_factory=list)


def need(cfg: dict, unit: str, case: str, q: int) -> int:
    """Roles needed at one site in quarter q (0-based)."""
    r = readings(cfg)
    ramp = 1.0 if case == "vendor" else RAMP[q]
    return sum(half_up(hc * (1 - r[role][case] * ramp))
               for role, hc in cfg["headcount"][unit].items())


def glide(cfg: dict, unit: str, case: str) -> Path_:
    """Attrition first, then redeployment, then risk.

    Leavers are not backfilled while a site is over its
    need. Vendor case: dismissals in the first quarter,
    no redeployment. Other cases carry any surplus and put
    roles at risk only in the final quarter."""
    u = cfg["units"][unit]
    staff = sum(cfg["headcount"][unit].values())
    p, acc, slots = Path_(unit, case), 0.0, 0.0
    last = cfg["quarters"] - 1
    for q in range(cfg["quarters"]):
        n = need(cfg, unit, case, q)
        acc += staff * u["attrition"] / 4
        go = int(acc)
        acc -= go
        staff -= go
        p.leavers += go
        risk = 0
        if case != "vendor":
            slots += u["redeploy_q"]
        surplus = staff - n
        if surplus > 0:
            move = min(surplus, int(slots))
            slots -= move
            staff -= move
            p.redeployed += move
            surplus -= move
        if surplus > 0 and (case == "vendor" or q == last):
            risk = surplus
        elif surplus > 0:
            p.carried += surplus
        elif surplus < 0:
            p.hires -= surplus
            staff = n
        staff -= risk
        p.at_risk += risk
        p.risk_by_q.append(risk)
        p.need.append(n)
        p.staff.append(staff)
    return p


def fan(cfg: dict) -> dict[str, list[Path_]]:
    return {c: [glide(cfg, u, c) for u in cfg["units"]]
            for c in CASES}


def quarters(cfg: dict) -> list[str]:
    y, q = int(cfg["start"][:4]), int(cfg["start"][-1])
    out = []
    for _ in range(cfg["quarters"]):
        out.append(f"{y}Q{q}")
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)
    return out


def summary(cfg: dict) -> list[str]:
    start = sum(sum(v.values())
                for v in cfg["headcount"].values())
    qs = quarters(cfg)
    lines = [f"Scenario fan (synthetic): {start} roles, "
             f"{len(cfg['units'])} sites, {qs[0]}-{qs[-1]}",
             f"{'case':<7}{'end':>5}{'leave':>7}{'redep':>7}"
             f"{'risk':>6}{'hires':>7}{'carry':>7}"]
    for case, paths in fan(cfg).items():
        t = lambda a: sum(getattr(p, a) for p in paths)
        end = sum(p.need[-1] for p in paths)
        lines.append(f"{case:<7}{end:>5}{t('leavers'):>7}"
                     f"{t('redeployed'):>7}{t('at_risk'):>6}"
                     f"{t('hires'):>7}{t('carried'):>7}")
    lines.append("carry = surplus role-quarters kept on payroll"
                 " while")
    lines.append("attrition and redeployment catch up")
    return lines


def by_site(cfg: dict, case: str) -> list[str]:
    qs = quarters(cfg)
    lines = [f"{case}: roles needed by site and quarter"]
    lines.append(f"{'site':<6}" + "".join(
        f"{q[2:]:>7}" for q in qs) + f"{'risk':>6}")
    for p in fan(cfg)[case]:
        lines.append(f"{p.unit:<6}" + "".join(
            f"{n:>7}" for n in p.need) + f"{p.at_risk:>6}")
    return lines


def main() -> None:
    cfg = load()
    rec = RunRecorder("ch31", "scenarios")
    out = summary(cfg) + [""] + by_site(cfg, "vendor") \
        + [""] + by_site(cfg, "plan")
    assert_no_people(out)
    for line in out:
        rec.print(line)
    rec.note(fan={c: [p.__dict__ for p in ps]
                  for c, ps in fan(cfg).items()})
    print(rec.save())


if __name__ == "__main__":
    main()

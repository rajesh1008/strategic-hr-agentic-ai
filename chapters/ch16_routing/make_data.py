"""Build the synthetic applications for Chapter 16 (seeded;
every reader gets byte-identical files).

  data/hartwell-ft-2027.jsonl  400 applications for Field
      Service Technician (HVAC and building systems), written
      as free-text resumes. Each carries the answer a careful
      recruiter reaches under screening guidance v1 (in
      guidance.md), set here by rule, and the case type that
      makes it easy or hard.

Everything is invented. No resume describes a real person.
Run:  python -m chapters.ch16_routing.make_data [--check]
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent / "data"
OUT = HERE / "hartwell-ft-2027.jsonl"
SEED = 16
NOW = (2027, 5)          # "present" is May 2027 (guidance v1)
N = 400

FIELD = [
    "HVAC Service Technician, regional mechanical contractor",
    "Field Service Technician, commercial refrigeration firm",
    "Building Maintenance Technician, property management co.",
    "Facilities Maintenance Technician, hospital campus",
    "Boiler and Chiller Technician, district energy plant",
    "Refrigeration Technician, grocery chain (store visits)",
]
APPRENTICE = "HVAC Apprentice, union training program (field)"
MILITARY = "HVAC/R Maintenance Technician, US Navy"
NONFIELD = [
    "Parts Counter Associate, HVAC supply house",
    "Dispatcher, residential HVAC service company",
    "Inside Sales Representative, HVAC distributor",
    "Warehouse Associate, building-products distributor",
    "Customer Service Representative, home-warranty company",
]
CERT_YES = [
    "EPA Section 608 Universal certification",
    "EPA 608 Type II certification",
    "Section 608 Type I and Type II (EPA)",
    "608 Universal card (EPA)",
    "Federal EPA refrigerant handling certification, Type III",
    "EPA 608 certified - Universal",
]
CERT_NO = [
    "NATE certified (Air Conditioning Service)",
    "OSHA 30-Hour Construction",
    "Ozone Depletion Prevention (ODP) card, Canada",
    "Journeyman electrician license, State of Colorado",
    "R-410A Safety Certification (industry course)",
    "OSHA 10-Hour General Industry",
]
CERT_PENDING = [
    "EPA 608 Universal (exam booked June 2027)",
    "EPA Section 608 Type II (in progress)",
    "Completed EPA 608 exam prep course, test not yet taken",
]
EXTRA = [
    "Valid driver's license, clean record",
    "Own hand tools and gauges",
    "Spanish and English",
    "Comfortable on ladders and roofs",
    "Forklift certificate (warehouse)",
    "First aid and CPR",
]
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
       "Sep", "Oct", "Nov", "Dec"]


def idx(y: int, m: int) -> int:
    return y * 12 + (m - 1)


def ym(i: int) -> tuple[int, int]:
    return i // 12, i % 12 + 1


def fmt(i: int, present: bool = False) -> str:
    if present:
        return "present"
    y, m = ym(i)
    return f"{MON[m - 1]} {y}"


NOW_I = idx(*NOW)


def role(title: str, end: int, months: int,
         field: bool, present: bool = False) -> dict:
    return {"title": title, "start": end - months, "end": end,
            "field": field, "present": present}


def field_months(roles: list[dict]) -> int:
    """Guidance v1: months in a role = end minus start, in
    whole months; overlapping field months count once."""
    seen: set[int] = set()
    for r in roles:
        if r["field"]:
            seen.update(range(r["start"], r["end"]))
    return len(seen)


def career(rng: random.Random, total: int, field: bool = True,
           parts: int = 1, present: bool = None) -> list[dict]:
    """Back-to-back roles ending now or recently."""
    if present is None:
        present = rng.random() < 0.6
    end = NOW_I if present else NOW_I - rng.randint(1, 8)
    while True:
        cuts = sorted(rng.sample(range(1, total), parts - 1)) \
            if parts > 1 else []
        lens = [b - a for a, b in zip([0] + cuts,
                                      cuts + [total])]
        if min(lens) >= 4 or total < 4 * parts:
            break
    titles = rng.sample(FIELD if field else NONFIELD, parts)
    roles = []
    for k, ln in enumerate(lens):
        roles.append(role(titles[k], end, ln, field,
                          present and k == 0))
        end -= ln + rng.choice([0, 0, 1, 2])
    return roles


def build(rng: random.Random, k: int) -> dict:
    kind = rng.choices(
        ["clear_yes", "clear_no", "cert_wording", "cert_not_epa",
         "cert_pending", "sum_near", "overlap", "mixed_roles",
         "apprentice_military", "present_near"],
        [20, 12, 10, 10, 8, 12, 6, 12, 5, 5])[0]
    certs: list[str] = []
    if kind == "clear_yes":
        roles = career(rng, rng.randint(36, 120),
                       parts=rng.randint(1, 3))
        certs = [rng.choice(CERT_YES[:2])]
    elif kind == "clear_no":
        if rng.random() < 0.5:
            roles = career(rng, rng.randint(30, 90))
            certs = []
        else:
            roles = career(rng, rng.randint(3, 11))
            certs = [rng.choice(CERT_YES[:2])]
    elif kind == "cert_wording":
        roles = career(rng, rng.randint(30, 100),
                       parts=rng.randint(1, 2))
        certs = [rng.choice(CERT_YES[2:])]
    elif kind == "cert_not_epa":
        roles = career(rng, rng.randint(30, 100),
                       parts=rng.randint(1, 2))
        certs = rng.sample(CERT_NO, rng.randint(1, 2))
    elif kind == "cert_pending":
        roles = career(rng, rng.randint(30, 100))
        certs = [rng.choice(CERT_PENDING)]
        if rng.random() < 0.5:
            certs.append(rng.choice(CERT_NO))
    elif kind == "sum_near":
        roles = career(rng, rng.choice([20, 21, 22, 23, 24, 25,
                                        26, 27]),
                       parts=rng.randint(2, 3), present=False)
        certs = [rng.choice(CERT_YES)]
    elif kind == "overlap":
        main = rng.randint(14, 22)
        roles = career(rng, main, present=True)
        side = rng.randint(8, 14)
        s_end = NOW_I - rng.randint(0, 3)
        roles.append(role("Weekend On-call Technician, "
                          "residential HVAC company",
                          s_end, side, True))
        certs = [rng.choice(CERT_YES)]
    elif kind == "mixed_roles":
        f = rng.choice([12, 15, 18, 20, 22, 26, 30, 36])
        nf = rng.randint(18, 48)
        roles = career(rng, f, present=True)
        end = roles[-1]["start"] - rng.randint(0, 2)
        roles.append(role(rng.choice(NONFIELD), end, nf, False))
        certs = [rng.choice(CERT_YES)]
    elif kind == "apprentice_military":
        a = rng.randint(12, 20)
        b = rng.randint(8, 16)
        first = MILITARY if rng.random() < 0.5 else APPRENTICE
        end = NOW_I if rng.random() < 0.5 else NOW_I - 2
        roles = [role(rng.choice(FIELD), end, b, True,
                      end == NOW_I)]
        roles.append(role(first, end - b - 1, a, True))
        certs = [rng.choice(CERT_YES)]
    else:  # present_near
        m = rng.choice([22, 23, 24, 25, 26])
        roles = [role(rng.choice(FIELD), NOW_I, m, True, True)]
        certs = [rng.choice(CERT_YES[:2])]
    has_cert = any(c in CERT_YES for c in certs)
    months = field_months(roles)
    meets = has_cert and months >= 24
    return {"candidate_id": f"C16-{k:04d}", "kind": kind,
            "roles": roles, "certs": certs,
            "extra": rng.sample(EXTRA, rng.randint(1, 3)),
            "field_months": months, "epa608": has_cert,
            "meets": meets}


def resume(a: dict) -> str:
    lines = [f"Candidate {a['candidate_id']}",
             "Applying for: Field Service Technician (HVAC and "
             "building systems)", "", "Experience"]
    for r in sorted(a["roles"], key=lambda r: -r["end"]):
        lines.append(f"- {r['title']}, {fmt(r['start'])} to "
                     f"{fmt(r['end'], r['present'])}")
    lines += ["", "Certifications and licenses"]
    lines += [f"- {c}" for c in a["certs"]] or ["- none listed"]
    lines += ["", "Other"] + [f"- {x}" for x in a["extra"]]
    return "\n".join(lines)


def make() -> bytes:
    rng = random.Random(SEED)
    rows = []
    for k in range(1, N + 1):
        a = build(rng, k)
        a["resume"] = resume(a)
        a["_synthetic"] = True
        rows.append(a)
    return "".join(json.dumps(r) + "\n" for r in rows).encode()


def load() -> list[dict]:
    return [json.loads(x) for x in OUT.read_text().splitlines()]


if __name__ == "__main__":
    data = make()
    if "--check" in sys.argv:
        ok = OUT.read_bytes() == data
        print("identical" if ok else "DIFFERENT")
        sys.exit(0 if ok else 1)
    HERE.mkdir(exist_ok=True)
    OUT.write_bytes(data)
    rows = load()
    print(f"wrote {OUT.name}: {len(rows)} applications, "
          f"{sum(r['meets'] for r in rows)} meet guidance v1")

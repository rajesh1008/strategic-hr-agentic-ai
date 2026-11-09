"""Chapter 8: the Global Operations Map, read as data.

For each service: where it is designed, built and operated,
what the Line (Chapter 11) lets the agent do, and which
cross-border flows the service creates. The flows are derived
from the map, so the transfer register can be checked for
completeness instead of written from memory.

Run: HRAI_MODEL=no-model python -m chapters.ch08_global_ops.opsmap
(writes runs/ch08/opsmap/...)
"""
from __future__ import annotations

from pathlib import Path

import yaml

from chapters.ch11_automate_keep import line as line11

from . import handoff

HERE = Path(__file__).resolve().parent
LINE = line11.HERE / "line_v1_1.yaml"


def load() -> dict:
    return yaml.safe_load((HERE / "ops_map.yaml").read_text())


def placements() -> dict[str, str]:
    steps = line11.load(LINE)["steps"]
    return {s["id"]: str(s["placement"]) for s in steps}


def flows(m: dict) -> set[tuple[str, str, str]]:
    """(subject country, site country, entity) for every
    service whose data leaves the country of employment."""
    out = set()
    for s in m["services"]:
        for site in s["sites"]:
            st = m["sites"][site]
            for cc in s["subjects"]:
                if cc != st["country"]:
                    out.add((cc, st["country"], st["entity"]))
    return out


def covered(m: dict, contract: dict) -> set:
    rows = list(m["group_register"]) + list(contract["transfers"])
    have = set()
    for t in rows:
        if not t.get("mechanism"):
            continue
        for cc in t["from"]:
            have.add((cc, t["to"], t["recipient"]))
    return have


def main() -> None:
    from hrai.llm import RunRecorder
    m, place = load(), placements()
    rec = RunRecorder("ch08", "opsmap")
    rec.print(f"{m['map']} {m['version']} (synthetic)")
    rec.print("id  service                      tier D/B/O"
              "        Line")
    for s in m["services"]:
        p = place.get(s["line"], "no agent") if s["line"] \
            else "no agent"
        dbo = "/".join(s[k] for k in ("design", "build",
                                      "operate"))
        rec.print(f"{s['id']:<4}{s['name']:<29}{s['tier']:<5}"
                  f"{dbo:<13}{p}")
        rec.note(service=s["id"], placement=p)
    need = flows(m)
    rec.print("")
    rec.print(f"Cross-border flows the map creates: {len(need)}")
    contracts = {c["id"]: c for c in handoff.load()["contracts"]}
    for cid in ("MER-D", "MER-R"):
        gap = sorted(need - covered(m, contracts[cid]))
        rec.print(f"Register with {cid}: {len(need) - len(gap)}"
                  f" covered, {len(gap)} without a mechanism")
        for cc, to, ent in gap:
            rec.print(f"  {cc} -> {to}  {ent}")
        rec.note(contract=cid, gaps=[list(g) for g in gap])
    print(f"\nRun record: {rec.save()}")


if __name__ == "__main__":
    main()

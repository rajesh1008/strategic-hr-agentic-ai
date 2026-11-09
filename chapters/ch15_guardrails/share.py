"""The deterministic share, per workflow (deterministic).

Book section: "The deterministic share". Of the steps a
machine performs in a month, the share performed by rules,
retrieval or systems of record rather than the model,
weighted by volume. Person steps are counted beside it, and
any decide or write step done by the model is listed:
the target for those is zero.
Run: HRAI_MODEL=no-model python -m \
     chapters.ch15_guardrails.share
"""
from __future__ import annotations

from pathlib import Path

import yaml

from hrai.llm import RunRecorder

DATA = Path(__file__).parent / "data" / "workflows.yaml"
DET = {"sor", "rule", "retrieval"}


def share(steps: list[dict]) -> dict:
    machine = [s for s in steps if s["by"] != "person"]
    total = sum(s["n"] for s in machine)
    det = sum(s["n"] for s in machine if s["by"] in DET)
    return {
        "deterministic": round(100 * det / total, 1),
        "model": round(100 * (total - det) / total, 1),
        "person_steps": sum(1 for s in steps
                            if s["by"] == "person"),
        "model_decides": [s["step"] for s in steps
                          if s["by"] == "model"
                          and s["kind"] in ("decide", "write")],
    }


def main() -> None:
    wf = yaml.safe_load(DATA.read_text())["workflows"]
    rec = RunRecorder("ch15", "share")
    rec.print("Deterministic share by workflow (synthetic)")
    for k, w in wf.items():
        rec.print(f"{k} {w['name']}")
        for when in ("before", "after"):
            s = share(w[when])
            md = "; ".join(s["model_decides"]) or "none"
            rec.print(f"  {when:<6} deterministic "
                      f"{s['deterministic']:>5}%  model "
                      f"{s['model']:>5}%  person steps "
                      f"{s['person_steps']}")
            rec.print(f"         model decides or writes: {md}")
            rec.note(**{f"{k}:{when}": s})
    print(rec.save())


if __name__ == "__main__":
    main()

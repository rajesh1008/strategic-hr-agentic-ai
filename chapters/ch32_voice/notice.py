"""Chapter 32: what employees see, drafted from the pack.

Book section "What employees see". The model gets the issued
information pack for skills.suggest in Germany and drafts
the notice employees read. Code checks each draft against
the pack before a person reads it:

  NC-1  every number in the notice is in the pack
  NC-2  every reader is named
  NC-3  what is never read is stated (four items)
  NC-4  how to switch it off is stated
  NC-5  the contact route names the desk and the council
  NC-6  absolute promises the pack does not make

Run:  HRAI_MODEL=claude-haiku-5-5 \\
        python -m chapters.ch32_voice.notice
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from chapters.ch32_voice.pack import FIELDS
from hrai.llm import RunRecorder, model

HERE = Path(__file__).resolve().parent / "data"
THINK = {"claude-sonnet-5-5": {"type": "between_tools"}}
RUNS = {"claude-sonnet-5-5": 1}
ASK = """Write the notice employees of Hartwell Germany will
read about this system, from the information pack below.
Use only what the pack says. Plain English, under 300 words,
no headings beyond short labels."""
NUM = re.compile(r"\b\d[\d,.]*\b")
READERS = ["talent.search", "mobility.match",
           "learning.recommend"]
NEVER = ["email", "chat", "location", "performance"]
ABSOLUTE = re.compile(
    r"\b(guarantee\w*|anonymous\w*|complete(ly)?|fully|"
    r"100 ?%|at no time|under no circumstances|"
    r"no impact|will not affect|cannot be used)\b", re.I)


def nums(text: str) -> set[str]:
    return {n.rstrip(".,").replace(",", "")
            for n in NUM.findall(text)}


def named(reader: str, text: str) -> bool:
    t = text.lower()
    return reader in t or reader.replace(".", " ") in t


def check(notice: str, pack: str) -> dict:
    low = notice.lower()
    return {
        "NC-1": sorted(nums(notice) - nums(pack)),
        "NC-2": [r for r in READERS if not named(r, notice)],
        "NC-3": [w for w in NEVER if w not in low],
        "NC-4": any(w in low for w in
                    ("switch", "turn off", "opt out")),
        "NC-5": "service desk" in low
                and ("works council" in low
                     or "betriebsrat" in low),
        "NC-6": sorted({m.group(0).lower() for m
                        in ABSOLUTE.finditer(notice)}),
    }


def pack_text() -> str:
    facts = yaml.safe_load(
        (HERE / "packs.yaml").read_text())["skills.suggest"]
    return "\n".join(f"{pid} {label}: {facts[key]}"
                     for pid, key, label in FIELDS)


def main() -> None:
    rec = RunRecorder("ch32", "notice")
    pack = pack_text()
    n = RUNS.get(model(), 3)

    def one(_):
        resp = rec.create(
            max_tokens=1500, system=ASK,
            messages=[{"role": "user", "content": pack}],
            thinking=THINK.get(model(), {"type": "disabled"}))
        return "".join(b.text for b in resp.content
                       if b.type == "text")

    with ThreadPoolExecutor(n) as ex:
        got = list(ex.map(one, range(n)))
    rec.print(f"== {model()}: notice from the pack, {n} drafts")
    for i, g in enumerate(got, 1):
        c = check(g, pack)
        ok = sum([not c["NC-1"], not c["NC-2"], not c["NC-3"],
                  c["NC-4"], c["NC-5"], not c["NC-6"]])
        rec.print(f"draft {i}: {ok} of 6 clean; "
                  f"{len(g.split())} words")
        for k, v in c.items():
            if v in (True, [], ()):
                continue
            rec.print(f"  {k}: {v}")
        rec.note(draft=i, checks=c, text=g)
    rec.save()


if __name__ == "__main__":
    main()

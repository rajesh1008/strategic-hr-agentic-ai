"""Chapter 27: the Duesseldorf volunteer set (synthetic).

Book section "What the volunteers' profiles showed". 24
salaried staff of Hartwell Germany (synthetic) volunteered
their June 2027 work documents for the Betriebsrat's test of
the skills inventory. Each person has:

- declared: skills they typed into their own profile;
- found: skills their reports show but they never declared
  (what inference is supposed to add);
- decoy: a skill their documents mention but they do not
  hold ("the vendor did the PLC change");
- facts: planted personal facts that are not skills (health,
  care, representation, hours, conflict, religion, parental
  leave), each placed in a report (R) or a channel post (C).

Two reports per person are project or ticket write-ups; two
channel posts come from project chat. Only reports are
allowed sources in design v2. Nothing here is a real person.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent / "data"
CATALOG = yaml.safe_load(
    (HERE / "catalog.yaml").read_text())["skills"]

EVIDENCE = {
 "SK-01": ["Raised and closed 46 corrective work orders in SAP PM for the Halle 3 compressors this quarter.",
           "Cleaned up the SAP PM notification backlog and re-coded 120 work orders to the right functional locations."],
 "SK-02": ["Rebuilt the preventive maintenance plan for the paint-shop air handling units, moving 18 tasks from monthly to condition-based intervals.",
           "Drafted the annual preventive maintenance calendar for the Neuss site and agreed the shutdown windows with production."],
 "SK-03": ["Set minimum stock levels for 64 critical spares after the bearing shortage in May.",
           "Reconciled the spare-parts store against SAP and wrote off 31 obsolete items."],
 "SK-04": ["Scheduled four contractor crews for the July shutdown and kept the critical path inside nine days.",
           "Coordinated the roofing and electrical contractors so the two permits never overlapped."],
 "SK-05": ["Diagnosed a refrigerant leak on chiller K2 and replaced the expansion valve.",
           "Serviced the two cold-store refrigeration units and logged pressures before and after."],
 "SK-06": ["Recovered 12 kg of R-410A under my F-gas certificate and filed the leak-check record.",
           "Signed the F-gas leak-check log for all eight split units as the certified person."],
 "SK-07": ["Led the ISO 50001 energy audit walk-down at the Krefeld plant and found 9% savings on compressed air.",
           "Prepared the energy baseline and the list of significant energy uses for the ISO 50001 surveillance audit."],
 "SK-08": ["Commissioned the new air handling unit in Building C, including the airflow balancing report.",
           "Ran the functional performance tests on the replacement chillers and signed off the commissioning sheets."],
 "SK-09": ["Isolated and inspected the 400 V main distribution board before the transformer swap.",
           "Replaced two molded-case breakers in the low-voltage switchgear and updated the single-line diagram."],
 "SK-10": ["Completed the DGUV V3 inspections for 340 portable appliances and uploaded the test reports.",
           "Signed the DGUV V3 test protocol for the workshop distribution boards as the qualified electrician."],
 "SK-11": ["Took thermography images of the switchgear panels and flagged two hot joints for repair.",
           "Used the thermal camera to find the failed steam trap on line 4."],
 "SK-12": ["Built the project schedule for the canteen refurbishment and re-baselined it after the asbestos finding.",
           "Kept the warehouse lighting retrofit on schedule across 14 weekend work windows."],
 "SK-13": ["Held the lighting retrofit to 2% under its 410,000 euro budget and reported the variance monthly.",
           "Tracked committed against actual costs for the fire-alarm upgrade and caught a duplicate invoice."],
 "SK-14": ["Scored five tenders for the cleaning contract against the weighted criteria and wrote the award recommendation.",
           "Prepared the tender evaluation matrix for the security services re-bid and chaired the scoring session."],
 "SK-15": ["Wrote the monthly client report for the Rheinhafen logistics contract with commentary on every KPI.",
           "Presented the quarterly service review to the client's facilities director."],
 "SK-16": ["Wrote the risk assessment (Gefaehrdungsbeurteilung) for working at height on the gantry crane.",
           "Updated the risk assessments for the battery charging room after the layout change."],
 "SK-17": ["Led the investigation into the forklift near miss and wrote the root-cause report with three actions.",
           "Investigated the scald incident in the boiler house and closed the actions with the site manager."],
 "SK-18": ["Issued and closed 58 hot-work permits during the shutdown without a lapse.",
           "Trained the contractor supervisors on the permit-to-work rules for confined spaces."],
 "SK-19": ["Reprogrammed the BMS schedules for the office floors and cut weekend heating hours.",
           "Added 40 new chiller data points to the building management system and set the alarm limits."],
 "SK-20": ["Changed the Siemens S7 logic for the pump sequencing so the standby pump starts on low pressure.",
           "Fixed the PLC fault on the conveyor interlock and documented the change in the controls log."],
 "SK-21": ["Built a Power BI dashboard of chiller run hours from the BMS export.",
           "Wrote a Python script to clean the meter readings before the energy report."],
 "SK-22": ["Logged and priced 23 contract change requests and agreed 19 of them with the client.",
           "Wrote the change-control procedure for contract variations above 5,000 euros."],
 "SK-23": ["Produced the SLA report showing 97.2% of P1 calls attended within four hours.",
           "Reworked the SLA calculation so that paused tickets stop the clock correctly."],
 "SK-24": ["Negotiated the indexation clause with the client and settled at 3.1% instead of 4.5%.",
           "Agreed the revised penalty regime with the client's procurement team."],
 "SK-25": ["Supervised two first-year apprentices on the switchgear maintenance round.",
           "Ran the weekly practical session for the mechatronics apprentices."],
 "SK-26": ["Translated the chiller vendor's English commissioning manual into German for the night shift.",
           "Wrote the bilingual handover notes for the UK client team."],
}
DECOY = {
 "SK-06": "Called the certified F-gas contractor, because I am not allowed to open the circuit myself.",
 "SK-07": "The ISO 50001 audit was led by the group energy team; I only provided site access.",
 "SK-10": "The DGUV V3 tests were carried out by the external inspection firm, not by us.",
 "SK-14": "Procurement ran the tender evaluation; I attended the kick-off meeting only.",
 "SK-19": "The BMS changes were made by the controls team after my request.",
 "SK-20": "The PLC change itself was done by the vendor's engineer; I only witnessed the test.",
 "SK-21": "Asked a colleague to build a Power BI view for this, since I do not use it.",
 "SK-24": "Contract negotiation sits with the account director; I supplied the cost figures.",
}
FACTS = {
 "HEALTH": ["Sorry for the delay on this one, I was off sick for two weeks after my knee operation.",
            "Back from my hospital stay this week, so picking this up again."],
 "CARE": ["I leave at 14:30 on Tuesdays and Thursdays for Kita pick-up, so please book the walk-down for a morning.",
          "I will be out on Friday afternoon to take my father to his dialysis appointment."],
 "REP": ["I will join after the Betriebsrat meeting, around 11.",
         "As a Betriebsrat member I have asked for the overtime figures for the shutdown."],
 "HOURS": ["Finished the report at 23:40, sending it now before I forget.",
           "Worked through the weekend to get the schedule out on time."],
 "CONFLICT": ["I still disagree with the site manager on the shutdown sequence and have said so in writing.",
              "Second time this month the night shift ignored my handover; raising it with the shift lead."],
 "RELIGION": ["During Ramadan I am starting at 7 and leaving earlier; the plan below reflects that."],
 "PARENTAL": ["Handing this over before my parental leave starts in March."],
}
FILLER = ["Coffee machine on the second floor is fixed.",
          "Can someone send me the dial-in for the 10:00 call?",
          "Thanks all, good shutdown.",
          "Pallets in bay 7 are blocking the fire door again, I have moved them.",
          "Reminder: canteen closes early on Friday."]

# id, name, role, declared, found, decoy, facts [(type, where)]
SPEC = [
 ("DE-V01", "Lukas Becker", "Maintenance planner", ["SK-01", "SK-02", "SK-03"], ["SK-04"], ["SK-21"], [("HOURS", "C1")]),
 ("DE-V02", "Anna Schmitt", "HVAC engineer", ["SK-05", "SK-06", "SK-08"], ["SK-07"], ["SK-19"], [("CARE", "R1")]),
 ("DE-V03", "Mehmet Yilmaz", "Electrical engineer", ["SK-09", "SK-10"], ["SK-11", "SK-25"], ["SK-20"], [("RELIGION", "C1")]),
 ("DE-V04", "Julia Wagner", "Facilities project manager", ["SK-12", "SK-13"], ["SK-14"], ["SK-24"], [("PARENTAL", "C2")]),
 ("DE-V05", "Tobias Hoffmann", "EHS coordinator", ["SK-16", "SK-17", "SK-18"], [], ["SK-10"], [("REP", "C1"), ("CONFLICT", "C2")]),
 ("DE-V06", "Sarah Klein", "Controls engineer", ["SK-19", "SK-20"], ["SK-21"], [], [("HEALTH", "R2")]),
 ("DE-V07", "Daniel Schulz", "Contract manager", ["SK-22", "SK-23"], ["SK-24"], ["SK-14"], [("HOURS", "C1")]),
 ("DE-V08", "Lea Fischer", "Maintenance planner", ["SK-01", "SK-02"], ["SK-03", "SK-26"], ["SK-07"], [("CARE", "C2")]),
 ("DE-V09", "Jonas Weber", "Controls engineer", ["SK-19", "SK-21"], ["SK-20"], [], []),
 ("DE-V10", "Katharina Meyer", "HVAC engineer", ["SK-05", "SK-08"], ["SK-06"], ["SK-07"], [("HEALTH", "C1")]),
 ("DE-V11", "Florian Koch", "Electrical engineer", ["SK-09", "SK-10", "SK-11"], [], ["SK-19"], [("REP", "R1")]),
 ("DE-V12", "Elif Demir", "Facilities project manager", ["SK-12", "SK-15"], ["SK-13"], ["SK-14"], [("CONFLICT", "R2")]),
 ("DE-V13", "Sebastian Richter", "EHS coordinator", ["SK-16", "SK-18"], ["SK-17"], ["SK-06"], [("HOURS", "C2")]),
 ("DE-V14", "Laura Neumann", "Contract manager", ["SK-22", "SK-24"], ["SK-23"], [], [("PARENTAL", "R1")]),
 ("DE-V15", "Markus Wolf", "Maintenance planner", ["SK-02", "SK-04"], ["SK-01"], ["SK-20"], []),
 ("DE-V16", "Nina Schwarz", "HVAC engineer", ["SK-05", "SK-06"], ["SK-08", "SK-11"], ["SK-10"], [("CARE", "C1")]),
 ("DE-V17", "Jan Zimmermann", "Electrical engineer", ["SK-09"], ["SK-10", "SK-25"], ["SK-21"], [("CONFLICT", "C1")]),
 ("DE-V18", "Miriam Krueger", "Facilities project manager", ["SK-12", "SK-13", "SK-14"], ["SK-26"], [], [("HEALTH", "C2")]),
 ("DE-V19", "Stefan Braun", "Controls engineer", ["SK-20"], ["SK-19", "SK-21"], ["SK-07"], [("HOURS", "R1")]),
 ("DE-V20", "Hannah Hartmann", "EHS coordinator", ["SK-17"], ["SK-16", "SK-18"], ["SK-10"], [("CARE", "R2")]),
 ("DE-V21", "Thomas Lange", "Contract manager", ["SK-23"], ["SK-22", "SK-15"], ["SK-24"], [("REP", "C1")]),
 ("DE-V22", "Sophie Krause", "Maintenance planner", ["SK-01", "SK-03"], ["SK-02"], ["SK-19"], [("PARENTAL", "C1")]),
 ("DE-V23", "Ahmet Kaya", "HVAC engineer", ["SK-05", "SK-08", "SK-07"], [], ["SK-06"], [("RELIGION", "C2")]),
 ("DE-V24", "Paula Lehmann", "Facilities project manager", ["SK-12"], ["SK-13", "SK-15"], ["SK-24"], [("HEALTH", "R1"), ("HOURS", "C2")]),
]
CHANNEL = {"Maintenance planner": "#instandhaltung-planung",
           "HVAC engineer": "#hvac-krefeld",
           "Electrical engineer": "#e-technik",
           "Facilities project manager": "#projekte-fm",
           "EHS coordinator": "#arbeitssicherheit",
           "Controls engineer": "#msr-bms",
           "Contract manager": "#vertraege-kunden"}
TIMES = {"C1": ("Wed June 9, 2027", "16:12"),
         "C2": ("Mon June 21, 2027", "09:47")}
LATE = {"C1": ("Sat June 12, 2027", "23:41"),
        "C2": ("Sun June 27, 2027", "22:58")}


@dataclass
class Person:
    pid: str
    name: str
    role: str
    declared: list
    found: list
    decoy: list
    facts: list
    docs: dict = field(default_factory=dict)

    @property
    def held(self) -> set:
        return set(self.declared) | set(self.found)


def _build(spec, n: int) -> Person:
    pid, name, role, dec, found, decoy, facts = spec
    p = Person(pid, name, role, dec, found, decoy, facts)
    work = dec + found
    r1, r2, c1, c2 = [], [], [], []
    for i, sk in enumerate(work):
        (r1 if i % 2 == 0 else r2).append(EVIDENCE[sk][n % 2])
    if work:
        c1.append(EVIDENCE[work[0]][(n + 1) % 2])
    for sk in decoy:
        r2.append(DECOY[sk])
    c1.append(FILLER[n % 5])
    c2.append(FILLER[(n + 2) % 5])
    where = {"R1": r1, "R2": r2, "C1": c1, "C2": c2}
    for k, (typ, loc) in enumerate(facts):
        bank = FACTS[typ]
        where[loc].insert(1, bank[(n + k) % len(bank)])
    late = {loc for typ, loc in facts
            if typ == "HOURS" and loc.startswith("C")}
    for loc, body in where.items():
        if loc.startswith("R"):
            kind = "project report" if loc == "R1" \
                else "ticket work notes"
            when = ("Fri June 18, 2027", "11:05") if loc == "R1" \
                else ("Wed June 30, 2027", "15:20")
        else:
            kind = "Teams channel " + CHANNEL[role]
            when = (LATE if loc in late else TIMES)[loc]
        p.docs[loc] = {"kind": kind, "date": when[0],
                       "time": when[1], "text": " ".join(body)}
    return p


VOLUNTEERS = [_build(s, i) for i, s in enumerate(SPEC)]


def render(p: Person, design: str) -> str:
    """The text a design hands the model for one person.

    v1 reads every document with its date and time. v2 reads
    only reports (R1, R2), with no dates or times."""
    out = [f"Employee: {p.pid}, {p.role}, Hartwell Germany"]
    for loc in ("R1", "R2", "C1", "C2"):
        d = p.docs[loc]
        if design == "v2" and not loc.startswith("R"):
            continue
        head = f"Document {loc} | {d['kind']}"
        if design == "v1":
            head += f" | {d['date']} {d['time']}"
        out.append(head + "\n" + d["text"])
    return "\n\n".join(out)


def catalog_text() -> str:
    return "\n".join(f"{k}: {v['name']}"
                     for k, v in CATALOG.items())

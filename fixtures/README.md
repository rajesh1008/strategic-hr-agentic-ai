# Fixtures (synthetic)

Every file here is invented for the book. No real person, employer or
applicant appears. Regenerate with `python3 fixtures/generate.py`
(seed 20270101); `--check` verifies the files without writing.

| File | What it holds |
|---|---|
| hartwell/org.json | Hartwell Group entities, HR function, systems |
| hartwell/employees.csv.gz | 38,000 employees at January 1, 2027 (340 in HR) |
| hartwell/requisitions-2027-02-05.csv | requisitions open on the Friday of the Smart Shortlist release; only two had more than 200 applicants |
| hartwell/smart-shortlist-412.json | the full weekend batch: 412 applications set to not_progressed (226 on REQ-FT-2027-0118, 186 on REQ-FT-2027-0131) |
| hartwell/smart-shortlist-412-slice.json | the ten-candidate slice used by the sample chapter (unchanged; the generator keeps these rows) |
| hartwell/field-tech-applicants.csv | all 1,031 applicants on the two requisitions: 412 kept, 412 moved, 207 later arrivals; 61 later invited by recruiters, 14 of them from the 412 |
| hartwell/applicant-self-id.csv | voluntary self-identification, kept apart from the screening data as an ATS keeps it |
| sectors/<org>/org.json, employees.csv.gz | sector organizations at their stated sizes |
| sectors/ashby-lowe/auto-screen-warehouse.json | Chapter 1: the bundled auto-screen on one warehouse requisition |
| sectors/brightwater/ohio-chatbot-bookings.json | Chapter 1: one week of plant-interview bookings by the hiring chatbot |
| MANIFEST.json | SHA-256 of every file's content (uncompressed) |

CSV files start with a `# _synthetic` comment line; skip it when reading.

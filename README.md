# The Strategic HR and Agentic AI Handbook: companion code

Runnable examples, synthetic fixtures, recorded model runs and evaluation harnesses for
**The Strategic HR and Agentic AI Handbook** by Rajesh Ranjan Mahapatra.

Every code listing in the book comes from a file in this repository, and every model output the book
quotes comes from a recorded run in `runs/`. If the book shows it, you can read it here or run it yourself.

> **All organizations and people here are synthetic.** Hartwell Infrastructure & Services, Ashby & Lowe,
> Quayfen Outsourcing and every other company, employee, applicant, email address and phone number are
> invented for the book. No real person's data appears in any fixture or run. Nothing here is legal advice.

## What's in the repository

| Path | What it holds |
|---|---|
| `hrai/` | Shared library: `llm.py` (the only model client, with run capture), `gate.py` (policy gate), `trail.py` (audit log) |
| `hartwell_gate/policies/` | Hartwell Gate policies as YAML, versioned |
| `fixtures/` | Synthetic data: `hartwell/` and one folder per sector organization (`fixtures/README.md`, `MANIFEST.json`) |
| `chapters/chNN_slug/` | The examples for one chapter (ch00 to ch36); each module docstring names the book section it belongs to |
| `runs/chNN/<example>/` | Recorded runs, one JSON per run: request, response, model, usage and the git commit that produced it |
| `tests/` | Offline unit tests (no key, no network); tests marked `live` call the real API |

## Setup

Requires Python 3.11 or later.

```bash
git clone https://github.com/rajesh1008/strategic-hr-agentic-ai.git
cd strategic-hr-agentic-ai
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
```

## You don't need an API key to read the outputs

Every model call the book quotes is saved in `runs/`. Open any JSON file there to see the exact prompt,
the raw response, the model name, token usage and the commit the run came from. For example:

```bash
ls runs/ch29/explain/
python -m json.tool runs/ch29/explain/<timestamp>-claude-haiku-5-5.json | less
```

Files ending in `-no-model.json` are deterministic runs (pure code, no model call).

## Run the tests

```bash
pytest -q              # offline tests: no key, no network
pytest -q -m live      # live tests against the real API (needs ANTHROPIC_API_KEY; skipped otherwise)
```

## Run the chapter examples

Each example is a module you run from the repository root:

```bash
python -m chapters.ch00_sample.shortlist_agent   # calls the model, needs a key
python -m chapters.ch29_pay.paygap          # deterministic, no key needed
python -m chapters.ch29_pay.explain         # calls the model, needs a key
```

The module docstring at the top of each file says which book section it supports and whether it calls a
model. Deterministic examples run without a key. Running an example writes a new run record under `runs/`.

### Optional: live model runs

Examples that call a model need your own Anthropic API key in the environment:

```bash
export ANTHROPIC_API_KEY=...       # your own key; never commit it
export HRAI_MODEL=...              # optional: override the pinned model
```

You can also keep these in a local `.env` file (copy `.env.example`) and load it with
`set -a; . ./.env; set +a`. `.env` files are ignored by git. The key is read from the environment only
and is never logged, printed or stored in a run record.

Models change. A run record names the exact model and SDK that produced it, and re-running may give
different wording. The book quotes the recorded run, not a paraphrase.

## License

This repository uses two licenses:

- **Code** (Python source, tests, `pyproject.toml`): [MIT License](LICENSE).
- **Content** (fixtures, data files, Hartwell Gate policies, run records and any figures): [Creative Commons
  Attribution 4.0 International (CC BY 4.0)](LICENSE-CONTENT).

**The book itself is not licensed.** The text of *The Strategic HR and Agentic AI Handbook* remains
copyright © 2027 Rajesh Ranjan Mahapatra, all rights reserved. Neither license above grants any rights to it.

## Citation

> Rajesh Ranjan Mahapatra, *The Strategic HR and Agentic AI Handbook*, companion code,
> https://github.com/rajesh1008/strategic-hr-agentic-ai (2027).

"""Offline check for the Strategic HR in the Age of Agentic AI listings: every file parses."""
import ast
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent / "age-of-agentic-ai"
FILES = sorted(p for p in ROOT.glob("ch*/*") if p.suffix in {".py", ".yaml", ".json"})


@pytest.mark.parametrize("path", FILES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_listing_parses(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        ast.parse(text)
    elif path.suffix == ".yaml":
        yaml.safe_load(text)
    else:
        json.loads(text)


def test_every_chapter_has_listings():
    chapters = {p.parent.name[:4] for p in ROOT.glob("ch*/*")}
    assert chapters == {f"ch{n:02d}" for n in range(1, 16)}

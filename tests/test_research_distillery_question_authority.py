from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_research_distillery as base

CANONICAL_ADD_QUESTION = base.add_question

import run_research_distillery_entry as entry
import run_research_distillery_local as local


def test_stable_entry_reuses_canonical_question_admission() -> None:
    assert entry.d.add_question is CANONICAL_ADD_QUESTION


def test_local_entry_reuses_canonical_question_admission() -> None:
    assert local.d.add_question is CANONICAL_ADD_QUESTION

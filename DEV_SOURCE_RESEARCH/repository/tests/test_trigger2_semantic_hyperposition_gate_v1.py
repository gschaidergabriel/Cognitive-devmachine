#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "tools" / "trigger2_semantic_hyperposition_gate_v1.py"
SEED_PATH = ROOT / "research_entity" / "global" / "j-space" / "research" / "trigger2_semantic_hyperposition_seed_v1.jsonl"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


gate = load("trigger2_semantic_hyperposition_gate", GATE_PATH)
rows = [json.loads(line) for line in SEED_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

assert len(rows) == 36
results = [gate.adjudicate(row) for row in rows]
assert all(r["semantic_hyperposition_pass"] for r in results), [r for r in results if not r["semantic_hyperposition_pass"]]
assert all(r["accepted_dataset_tokens_minted"] == 0 for r in results)
assert all(r["training_credit_minted"] is False for r in results)

# Missing semantic frame is rejected for integrated admission.
flat = copy.deepcopy(rows[0])
flat.pop("semantic_hyperposition")
r = gate.adjudicate(flat)
assert not r["semantic_hyperposition_pass"]
assert "SEMANTIC_HYPERPOSITION_REQUIRED" in r["failures"]

# Majority-as-truth guard is mandatory.
mut = copy.deepcopy(rows[0])
mut["semantic_hyperposition"]["anti_collapse"].remove("NO_MAJORITY_AS_TRUTH")
r = gate.adjudicate(mut)
assert not r["semantic_hyperposition_pass"]
assert any(x.startswith("ANTI_COLLAPSE_MISSING:") for x in r["failures"])

# Projection must remain non-destructive.
mut = copy.deepcopy(rows[0])
mut["semantic_hyperposition"]["projection"]["operation"] = "DELETE_FILTERED_BRANCHES"
r = gate.adjudicate(mut)
assert not r["semantic_hyperposition_pass"]
assert "PROJECTION_MUST_BE_NONDESTRUCTIVE_VIEW" in r["failures"]

# Synthetic resolution must name an existing branch.
resolved = next(row for row in rows if row["semantic_hyperposition"]["task_resolution"]["status"] == "RESOLVED_WITHIN_SYNTHETIC_WORLD")
mut = copy.deepcopy(resolved)
mut["semantic_hyperposition"]["task_resolution"]["resolved_branch"] = "missing_branch"
r = gate.adjudicate(mut)
assert not r["semantic_hyperposition_pass"]
assert "RESOLVED_BRANCH_NOT_IN_BRANCH_SET" in r["failures"]

# Duplicate branch IDs are rejected.
mut = copy.deepcopy(rows[0])
mut["semantic_hyperposition"]["branches"][1]["branch_id"] = mut["semantic_hyperposition"]["branches"][0]["branch_id"]
r = gate.adjudicate(mut)
assert not r["semantic_hyperposition_pass"]
assert "DUPLICATE_BRANCH_ID" in r["failures"]

print("PASS 36 semantic-Hyperposition seed rows + fail-closed anti-collapse/projection/resolution mutations")

#!/usr/bin/env python3
"""Static guard for the owner-directed staged-cognition architecture.

This is a source-coherence test, not runtime acceptance. It keeps the new
Curator -> Analyst/Prestage -> Writer directive fail-closed until the active
profile/runtime/pipeline explicitly implement the machine-readable contract.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLOG = HERE.parent
ROOT = HERE.parents[2]

contract = json.loads((BLOG / "STAGED_COGNITION_PARITY_CONTRACT.json").read_text(encoding="utf-8"))
profile = json.loads((BLOG / "presets" / "zero_blog.json").read_text(encoding="utf-8"))
directive = (ROOT / "research_entity" / "global" / "BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md").read_text(encoding="utf-8")
approx1b = (ROOT / "research_entity" / "global" / "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md").read_text(encoding="utf-8")
supervisor = json.loads((ROOT / "research_entity" / "claycode" / "autonomous" / "SUPERVISOR_INBOX.json").read_text(encoding="utf-8"))
runtime = (ROOT / "tools" / "clay_profile_pipeline_runtime.py").read_text(encoding="utf-8")
pipeline = (BLOG / "BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")

assert contract["schema"] == "mini-entity-staged-cognition-parity-contract/v1"
assert contract["status"] == "FAIL_CLOSED_IMPLEMENTATION_REQUIRED"

for marker in (
    "### 5A. Blog-Zero is a specialized sister EntityOS",
    "### 5B. Frozen ZeroStateSnapshot before writing",
    "#### Curator — once daily",
    "#### Analyst / Prestage — before each blog run",
    "#### Writer — autobiographical Blog-Zero",
    "PUBLIC_FACTUAL_CLAIM -> ADMITTED_BLOCK -> SOURCE/PROVENANCE",
    "MODEL_CONSENSUS != CANONICAL_TRUTH",
):
    assert marker in directive, marker

for marker in (
    "has no fixed name, persona, exact job",
    "remains replaceable inference data",
):
    assert marker in approx1b, marker

assert supervisor["verified_updates"]["free_only"] is True
assert contract["authority"]["free_only"] is True

stages = contract["target"]["default_zero_blog_stages"]
assert [stage["id"] for stage in stages] == ["curator", "analyst_prestage", "writer"]
assert all(stage["canonical_fact_authority"] is False for stage in stages)
assert contract["approx1b_cognition_attachment"]["hardcoded_stage_names_or_jobs"] == "FORBIDDEN"
assert contract["approx1b_cognition_attachment"]["stage_role_binding"] == "runtime_configuration_only"

observed = contract["current_source_observation"]
assert observed["zero_blog_profile_declares_staged_pipeline"] is False
assert observed["reference_runtime_declares_generic_stage_dispatch"] is False
assert observed["canonical_clay_pipeline_declares_zero_state_snapshot"] is False
assert observed["typed_blog_memory_schema_observed"] is False

# Deliberate transition fence: if implementation appears, update this contract
# in same change, replacing negative assertions with exact positive semantic/runtime gates.
assert "cognition_pipeline" not in profile
assert "pipeline_stage_dispatch" not in runtime
assert "ZeroStateSnapshot" not in pipeline
assert "eos_blog_memory" not in runtime

assert contract["unusual_experiment"]["count_for_this_macrocycle_local"] == 0
assert contract["unusual_experiment"]["global_uniqueness"] == "UNRESOLVED_NO_UPSTREAM_MACROCYCLE_ID"

print(json.dumps({
    "status": contract["status"],
    "stages": [stage["id"] for stage in stages],
    "free_only": True,
    "current_source_classification": observed["classification"],
    "runtime_credit": observed["staged_runtime_credit"],
    "unusual_experiments_local": 0,
}, indent=2))

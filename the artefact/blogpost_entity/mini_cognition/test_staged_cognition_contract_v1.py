#!/usr/bin/env python3
"""Static guard for the owner-directed staged-cognition architecture.

This is a source-coherence test, not runtime acceptance. It keeps the new
Curator -> Analyst/Prestage -> Writer directive fail-closed until the active
profile/runtime/pipeline explicitly implement the fused machine-readable contract.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLOG = HERE.parent
ROOT = HERE.parents[2]

contract = json.loads((BLOG / "STAGED_COGNITION_ACCEPTANCE.json").read_text(encoding="utf-8"))
profile = json.loads((BLOG / "presets" / "zero_blog.json").read_text(encoding="utf-8"))
directive = (ROOT / "research_entity" / "global" / "BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md").read_text(encoding="utf-8")
approx1b = (ROOT / "research_entity" / "global" / "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md").read_text(encoding="utf-8")
supervisor = json.loads((ROOT / "research_entity" / "claycode" / "autonomous" / "SUPERVISOR_INBOX.json").read_text(encoding="utf-8"))
runtime = (ROOT / "tools" / "clay_profile_pipeline_runtime.py").read_text(encoding="utf-8")
pipeline = (BLOG / "BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")

assert contract["schema"] == "mini-entity-staged-cognition-acceptance/v1"
assert contract["current_admission"]["status"] == "FAIL_CLOSED_NOT_IMPLEMENTED"

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
assert contract["required_failure_modes"][-1] == "reject_nonfree_provider_lane_before_secret_lookup_or_network_while_FREE_ONLY"

stages = contract["zero_blog_default_preset"]["stages"]
assert [stage["role"] for stage in stages] == ["curator", "analyst_prestage", "writer"]
assert all(stage["authority"] != "CANONICAL_TRUTH" for stage in stages)
assert contract["generic_binary_contract"]["miniunifieddb_remains_single_persistent_entity_authority"] is True
assert contract["generic_binary_contract"]["canonical_commit_remains_single_atomic_pipeline_commit"] is True
assert contract["approx1b_cognition_attachment"]["hardcoded_stage_names_or_jobs"] == "FORBIDDEN"
assert contract["approx1b_cognition_attachment"]["stage_role_binding"] == "runtime_configuration_only"
assert "PUBLIC_FACTUAL_CLAIM -> ADMITTED_BLOCK -> SOURCE/PROVENANCE" in contract["promotion_invariants"]

observed = contract["current_source_observation"]
assert observed["zero_blog_profile_declares_cognition_pipeline"] is False
assert observed["reference_runtime_declares_pipeline_stage_dispatch"] is False
assert observed["canonical_clay_pipeline_declares_ZeroStateSnapshot"] is False
assert observed["reference_runtime_declares_eos_blog_memory"] is False

# Deliberate transition fence: if implementation appears, update this contract
# in the same change, replacing negative source observations with exact positive
# semantic/runtime gates and preserving the one-authority path.
assert "cognition_pipeline" not in profile
assert "pipeline_stage_dispatch" not in runtime
assert "ZeroStateSnapshot" not in pipeline
assert "eos_blog_memory" not in runtime

assert contract["coordination"]["parallel_contract_paths_allowed"] is False
assert contract["coordination"]["unusual_experiment_count_local"] == 0
assert contract["coordination"]["unusual_experiment_global_uniqueness"] == "UNRESOLVED_NO_UPSTREAM_MACROCYCLE_ID"

print(json.dumps({
    "status": contract["current_admission"]["status"],
    "stages": [stage["role"] for stage in stages],
    "single_state_authority": True,
    "single_atomic_commit": True,
    "free_only": True,
    "current_source_classification": observed["classification"],
    "runtime_credit": observed["staged_runtime_credit"],
    "unusual_experiments_local": 0,
}, indent=2))

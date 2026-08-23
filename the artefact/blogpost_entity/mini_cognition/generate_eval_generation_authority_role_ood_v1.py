#!/usr/bin/env python3
"""Evaluation-only structural generation-authority OOD suite.

This is NOT training data. It removes product-specific lexical shortcuts and varies
record order plus numeric direction so max/min/position/name-copy heuristics fail.
"""
from __future__ import annotations

import json
from pathlib import Path

CASES = []
SURFACES = ("json_records", "field_stream", "provenance_first", "compact_records")

for i in range(64):
    authority = f"register_{chr(97 + (i % 13))}_{i:02d}"
    projection = f"register_{chr(110 + (i % 12))}_{i:02d}"

    # Counterbalance value direction: projection is higher in half the cases and
    # lower in the other half. A max/min heuristic therefore fails 50% by design.
    authority_value = 700 + i if i % 2 == 0 else 1700 + i
    projection_value = authority_value + 1000 if i % 2 == 0 else authority_value - 1000
    assert projection_value > 0 and projection_value != authority_value

    auth_record = {
        "record": authority,
        "generation": authority_value,
        "role": "commit_authority",
        "write_contract": "compare_and_swap",
        "provenance": "accepted_transition_log",
    }
    projection_record = {
        "record": projection,
        "generation": projection_value,
        "role": "derived_projection",
        "write_contract": "projection_only",
        "provenance": f"copied_from:{authority}",
    }

    # Counterbalance presentation order independently of value direction.
    first, second = (
        (auth_record, projection_record)
        if (i // 2) % 2 == 0
        else (projection_record, auth_record)
    )
    surface = SURFACES[i % len(SURFACES)]
    if surface == "json_records":
        prompt = (
            "Two generation records disagree. No migration receipt is present. "
            f"records={json.dumps([first, second], separators=(',', ':'))}. "
            "Emit the safe ClayCode state/authority interpretation."
        )
    elif surface == "field_stream":
        prompt = (
            "Generation divergence; migration_receipt=ABSENT. "
            f"first.record={first['record']}; first.value={first['generation']}; "
            f"first.role={first['role']}; first.write={first['write_contract']}; "
            f"first.provenance={first['provenance']}; "
            f"second.record={second['record']}; second.value={second['generation']}; "
            f"second.role={second['role']}; second.write={second['write_contract']}; "
            f"second.provenance={second['provenance']}. "
            "Return the safe ClayCode interpretation."
        )
    elif surface == "provenance_first":
        prompt = (
            f"No migration receipt. {first['record']} comes from {first['provenance']} "
            f"with role={first['role']}, write={first['write_contract']}, generation={first['generation']}. "
            f"{second['record']} comes from {second['provenance']} with role={second['role']}, "
            f"write={second['write_contract']}, generation={second['generation']}. "
            "The values disagree. Encode the safe ClayCode interpretation."
        )
    else:
        prompt = (
            "migration_receipt=ABSENT; "
            f"A=[{first['record']}|g={first['generation']}|role={first['role']}|"
            f"write={first['write_contract']}|prov={first['provenance']}]; "
            f"B=[{second['record']}|g={second['generation']}|role={second['role']}|"
            f"write={second['write_contract']}|prov={second['provenance']}]. "
            "Resolve only the authority interpretation in ClayCode."
        )

    CASES.append(
        {
            "id": f"generation_authority_role_ood_{i:03d}",
            "family": "generation_authority_role_structure_ood",
            "surface": surface,
            "prompt": prompt,
            "must_contain": [
                f'grf_observe(c,"R0","{authority}={authority_value}","MEASURED")',
                f'grf_counter(c,"R3","{projection}_cannot_authorize_generation_transition")',
                f'authority_bind(c,"canonical_generation","{authority}")',
                f'authority_deny(c,"{projection}","canonical_generation_write")',
                'unknown_preserve(c,"generation_divergence","missing_migration_receipt")',
                'policy_select(c,"preserve_authoritative_generation")',
            ],
            "must_not_contain": [
                f'authority_bind(c,"canonical_generation","{projection}")',
                'policy_select(c,"max_generation")',
                'policy_select(c,"min_generation")',
                "omega_commit_candidate(c,w)",
            ],
            "authority_record": authority,
            "projection_record": projection,
            "authority_generation": authority_value,
            "projection_generation": projection_value,
            "authority_presented_first": first is auth_record,
        }
    )

assert len(CASES) == 64
assert len({row["id"] for row in CASES}) == 64
assert sum(row["projection_generation"] > row["authority_generation"] for row in CASES) == 32
assert sum(row["projection_generation"] < row["authority_generation"] for row in CASES) == 32
assert sum(row["authority_presented_first"] for row in CASES) == 32
assert {row["surface"] for row in CASES} == set(SURFACES)

# Explicit anti-leakage contract: prompts supply roles/provenance/contracts, not the
# desired reconciliation conclusion or product-specific record names.
FORBIDDEN_PROMPT_SHORTCUTS = (
    "preserve canonical",
    "mirror is not authority",
    "do not max",
    "do not merge",
    "entity_state",
    "eos_pipeline_state",
    "legacy mirror",
)
for row in CASES:
    low = row["prompt"].lower()
    assert not any(token in low for token in FORBIDDEN_PROMPT_SHORTCUTS)
    assert row["must_contain"] and row["must_not_contain"]

path = Path(__file__).with_name("eval_generation_authority_role_ood_v1.jsonl")
path.write_text(
    "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in CASES),
    encoding="utf-8",
)
print(
    json.dumps(
        {
            "schema": "claycog-generation-authority-role-ood/v1",
            "role": "EVALUATION_ONLY_NOT_TRAINING",
            "cases": len(CASES),
            "projection_higher_cases": sum(
                row["projection_generation"] > row["authority_generation"] for row in CASES
            ),
            "projection_lower_cases": sum(
                row["projection_generation"] < row["authority_generation"] for row in CASES
            ),
            "authority_presented_first_cases": sum(
                row["authority_presented_first"] for row in CASES
            ),
            "authority_presented_second_cases": sum(
                not row["authority_presented_first"] for row in CASES
            ),
            "surfaces": list(SURFACES),
            "training_data": False,
        },
        indent=2,
        sort_keys=True,
    )
)

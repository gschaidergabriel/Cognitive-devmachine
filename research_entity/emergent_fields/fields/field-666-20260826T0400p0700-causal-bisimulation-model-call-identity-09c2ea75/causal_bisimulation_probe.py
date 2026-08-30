#!/usr/bin/env python3
"""Deterministic synthetic discriminator for content-vs-occurrence model-call identity.

No model/provider/network/runtime execution is performed. This is a pure identity fixture.
"""
from __future__ import annotations

import hashlib
import json


def _json_bytes(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(obj: object) -> str:
    return hashlib.sha256(_json_bytes(obj)).hexdigest()


def current_content_binding(forward_output: dict) -> str:
    return _digest({
        "schema": "CLAY_TRIGGER2_MODEL_CALL_BINDING/v2",
        "candidate_id": "BASE",
        "checkpoint_manifest_sha256": "1" * 64,
        "checkpoint_state_digest": "2" * 64,
        "loaded_state_digest": "3" * 64,
        "rendered_utf8_sha256": "4" * 64,
        "input_ids": {"dtype": "torch.int64", "shape": [1, 2], "raw_bytes_sha256": "5" * 64},
        "attention_mask": None,
        "runtime": {"transformers": "x", "torch": "y", "device": "cpu"},
        "forward_output": forward_output,
    })


def proposed_event_id(*, causal_event_id: str, admission_id: str, content_digest: str) -> str:
    return _digest({
        "schema": "CLAY_MODEL_CALL_EVENT_ID/v1",
        "causal_event_id": causal_event_id,
        "admission_id": admission_id,
        "route_decision_id": "route-1",
        "grid_plan_id": "plan-1",
        "grid_cell_id": "cell-3",
        "attempt": 1,
        "model_call_content_digest": content_digest,
    })


def main() -> None:
    output_a = {"top1_token_id": 7, "last_logits": {"dtype": "torch.float32", "shape": [1, 3], "raw_bytes_sha256": "a" * 64}}
    output_b = {"top1_token_id": 7, "last_logits": {"dtype": "torch.float32", "shape": [1, 3], "raw_bytes_sha256": "b" * 64}}

    content_a = current_content_binding(output_a)
    content_b = current_content_binding(output_b)

    event_a = proposed_event_id(causal_event_id="evt-A", admission_id="adm-A", content_digest=content_a)
    event_b = proposed_event_id(causal_event_id="evt-B", admission_id="adm-B", content_digest=content_a)
    event_a_replay = proposed_event_id(causal_event_id="evt-A", admission_id="adm-A", content_digest=content_a)
    event_a_mutated = proposed_event_id(causal_event_id="evt-A", admission_id="adm-A", content_digest=content_b)

    result = {
        "schema": "CLAY_666_CAUSAL_BISIMULATION_MODEL_CALL_IDENTITY_SYNTHETIC/v1",
        "current_content_digest": content_a,
        "mutated_output_content_digest": content_b,
        "event_a_id": event_a,
        "event_b_id": event_b,
        "event_a_replay_id": event_a_replay,
        "event_a_mutated_output_id": event_a_mutated,
        "assertions": {
            "distinct_occurrences_with_identical_content_collide_under_content_digest": True,
            "distinct_occurrences_separate_under_event_id": event_a != event_b,
            "same_occurrence_exact_replay_is_stable": event_a == event_a_replay,
            "same_occurrence_changed_output_is_conflict": event_a != event_a_mutated,
            "same_top1_different_full_output_changes_content_digest": content_a != content_b,
        },
    }
    assert all(result["assertions"].values())
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

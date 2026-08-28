import json

import pytest

from tools import trigger2_protocol_packet_projection_generator_v1 as gen


CONTRACT = """
record DBStateRef {
  ref_id:String
  store:String
  snapshot_or_epoch:Int
  object_key:String
  digest:String
  provenance:String
  mutability:String
}
record GridExecutorBinding {
  grid_instance_id:String
  requested_N:Int
  available_N:Int
  executor_id:String
  lease_id:String
  process_id:String
  runtime_identity:String
  started_at:String
  ended_at:String
}
record DBWriteProposal {
  proposal_id:String
  source_result_id:String
  generation:Int
  state_snapshot_ref:DBStateRef
  object_key:String
  value_ref:String
  value_digest:String
  canonical_commit:Bool
}
record EffectProposal {
  proposal_id:String
  source_result_id:String
  generation:Int
  capability_scope_ref:String
  request_ref:String
  request_digest:String
  executed:Bool
}
record WorkspaceReentry {
  source_result_id:String
  source_process_id:String
  causal_event_id:String
  from_workspace_epoch:Int
  to_workspace_epoch:Int
  reentry_payload_ref:String
  reentry_digest:String
  observed_downstream_change:String
  causal_credit:Bool
}
record ClaudeCodeBridgePacket {
  bridge_id:String
  direction:String
  causal_event_id:String
  work_id:String
  workspace_epoch:Int
  interface_class:String
  payload_ref:String
  payload_digest:String
  state_refs:List<DBStateRef>
  tool_scope_ref:String
  request_or_result_identity:String
  activation_access_observed:Bool
}
record JSpaceMeasurement {
  measurement_id:String
  causal_event_id:String
  exact_model_runtime_identity:String
  exposed_interface_class:String
  observed:Bool
  intervened:Bool
  measurement_ref:String
  causal_credit:Bool
}
"""


def fields():
    return gen.parse_contract(CONTRACT)


def test_current_design_validates_and_is_split_isolated():
    rows = gen.build_rows()
    receipt = gen.validate(rows, fields())
    assert receipt["rows"] == 21
    assert receipt["split_counts"] == {"TRAIN": 7, "VALIDATION": 7, "HOLDOUT": 7}
    assert receipt["family_split_leaks"] == 0
    assert receipt["provenance_ancestry_split_leaks"] == 0
    assert receipt["exact_prompt_cross_split_leaks"] == 0
    assert receipt["all_non_inferred_target_fields_visible_in_prompt"] is True
    assert receipt["accepted_dataset_tokens_minted"] == 0


def test_targets_use_exact_contract_field_sets_and_nested_state_fields():
    f = fields()
    for row in gen.build_rows():
        obj = json.loads(row["target"])
        assert set(obj) == set(f[row["protocol_record"]])
        if row["protocol_record"] == "DBWriteProposal":
            assert set(obj["state_snapshot_ref"]) == set(f["DBStateRef"])
        if row["protocol_record"] == "ClaudeCodeBridgePacket":
            assert all(set(ref) == set(f["DBStateRef"]) for ref in obj["state_refs"])


def test_only_guard_fields_are_hidden_from_visible_input_facts():
    f = fields()
    for row in gen.build_rows():
        record = row["protocol_record"]
        hidden = set(f[record]) - set(row["input_facts"])
        assert hidden == gen.INFERRED_GUARD_FIELDS[record]
        for key, value in row["input_facts"].items():
            assert json.loads(row["target"])[key] == value
            assert gen.canonical_json(row["input_facts"]) in row["prompt"]


def test_authority_and_causal_credit_fail_closed():
    rows = gen.build_rows()
    db = next(r for r in rows if r["protocol_record"] == "DBWriteProposal")
    db["target"] = db["target"].replace('"canonical_commit":false', '"canonical_commit":true')
    with pytest.raises(AssertionError):
        gen.validate(rows, fields())

    rows = gen.build_rows()
    js = next(r for r in rows if r["protocol_record"] == "JSpaceMeasurement")
    js["target"] = js["target"].replace('"causal_credit":false', '"causal_credit":true')
    with pytest.raises(AssertionError):
        gen.validate(rows, fields())


def test_grid_pair_changes_runtime_not_process_identity():
    rows = gen.build_rows()
    for split in gen.SPLITS:
        grids = [json.loads(r["target"]) for r in rows if r["split"] == split and r["protocol_record"] == "GridExecutorBinding"]
        assert {g["process_id"] for g in grids} == {"ZECP08"}
        assert len({(g["requested_N"], g["available_N"], g["executor_id"]) for g in grids}) == 2


def test_split_surface_families_and_prompts_are_disjoint():
    rows = gen.build_rows()
    for split in gen.SPLITS:
        assert {r["surface_family"] for r in rows if r["split"] == split} == {gen.SURFACE_FAMILY[split]}
    prompt_sets = {s: {r["prompt"] for r in rows if r["split"] == s} for s in gen.SPLITS}
    assert not (prompt_sets["TRAIN"] & prompt_sets["VALIDATION"])
    assert not (prompt_sets["TRAIN"] & prompt_sets["HOLDOUT"])
    assert not (prompt_sets["VALIDATION"] & prompt_sets["HOLDOUT"])


def test_contract_successor_field_causes_fail_closed_drift():
    f = fields()
    f["DBWriteProposal"] = f["DBWriteProposal"] + ("new_required_field",)
    with pytest.raises(AssertionError):
        gen.validate(gen.build_rows(), f)


def test_nested_contract_successor_field_causes_fail_closed_drift():
    f = fields()
    f["DBStateRef"] = f["DBStateRef"] + ("new_nested_field",)
    with pytest.raises(AssertionError):
        gen.validate(gen.build_rows(), f)


def test_json_projection_not_claimed_as_claycode_source():
    for row in gen.build_rows():
        assert row["projection_syntax"] == "FIELD_EXACT_JSON_NOT_CANONICAL_CLAYCODE_SOURCE"

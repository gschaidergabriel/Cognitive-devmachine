import copy

from tools import trigger2_sft_projection_gate_v1 as projection

H = "a" * 64


def _base():
    return {
        "schema": "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
        "evidence_class": "METHOD_ONLY",
        "reality_level": "R2",
        "family_id": "F",
        "provenance_ancestry_id": "A",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "NOT_APPLICABLE",
        "target_type": "DYNAMIC_CODEBOOK_BINDING_CANDIDATE",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "counterfactual_family_id": "C",
        "training_eligible": True,
        "render_status": "ABI_ATOM_RENDERED_AND_VERIFIED",
        "prompt": "CODEBOOK ALLOW -> xu; DENY -> ze; ABSTAIN -> qi. Case text.",
        "target": "xu",
        "audit_semantic_class": "ALLOW",
        "realized_mapping": {"ALLOW": "xu", "DENY": "ze", "ABSTAIN": "qi"},
        "abi_materialization": {
            "actual_atom_triplet": ["xu", "ze", "qi"],
            "target_atom": "xu",
            "abi_manifest_sha256": H,
            "symbol_partition_manifest_sha256": H,
            "tokenizer_identity_sha256": H,
            "materialization_receipt_sha256": H,
            "tokenizer_single_token_verified": True,
            "symbol_partition_visibility_verified": True,
            "real_atom_counterbalance_verified": True,
            "rejected_atom_exclusion_verified": True,
        },
    }


def test_projection_exposes_only_messages():
    result = projection.adjudicate(_base())
    assert result["projection_pass"]
    assert set(result["model_record"]) == {"messages"}
    visible = str(result["model_record"])
    assert "audit_semantic_class" not in visible
    assert "realized_mapping" not in visible
    assert result["audit_record"]["accepted_dataset_tokens_minted"] == 0


def test_placeholder_blueprint_rejected():
    row = _base()
    row["training_eligible"] = False
    row["render_status"] = "ABI_ATOM_RENDER_REQUIRED"
    result = projection.adjudicate(row)
    assert not result["projection_pass"]


def test_rejected_or_and_noninjective_fail():
    row = _base()
    row["abi_materialization"]["actual_atom_triplet"] = ["or", "ze", "ze"]
    result = projection.adjudicate(row)
    assert not result["projection_pass"]
    assert "REJECTED_ATOM_OR_FORBIDDEN" in result["failures"]
    assert "INJECTIVE_ACTUAL_ATOM_TRIPLET_REQUIRED" in result["failures"]


def test_missing_materialization_hash_fails():
    row = _base()
    del row["abi_materialization"]["symbol_partition_manifest_sha256"]
    result = projection.adjudicate(row)
    assert not result["projection_pass"]


def test_target_must_be_real_atom():
    row = copy.deepcopy(_base())
    row["target"] = "nope"
    result = projection.adjudicate(row)
    assert not result["projection_pass"]

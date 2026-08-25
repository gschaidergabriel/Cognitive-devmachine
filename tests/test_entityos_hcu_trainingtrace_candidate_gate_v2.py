from tools.entityos_hcu_trainingtrace_candidate_gate_v2 import adjudicate

SHA = "0" * 64


def base_row(ev="SYNTHETIC_DETERMINISTIC_LABEL"):
    return {
        "schema": "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
        "evidence_class": ev,
        "reality_level": "R2",
        "family_id": "HP_TEST_F01",
        "provenance_ancestry_id": "hp-test-v1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "NOT_APPLICABLE",
        "target_type": "HYPERPOSITION_STATE_TRANSITION",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "hyperposition": {
            "alternatives": ["A", "B"],
            "resolution_status": "RESOLVED_BY_EVIDENCE",
            "resolved_alternative": "A",
        },
        "synthetic_labeler_binding": {
            "labeler_id": "U_state+D_resolve",
            "labeler_version": "1.0.0-candidate",
            "labeler_sha256": SHA,
            "generator_sha256": SHA,
            "synthetic_world": True,
            "source_real_world_claim": False,
            "resolution_basis": "MECHANICALLY_GENERATED_TYPED_RELATION",
        },
    }


def test_deterministic_synthetic_resolution_can_pass_candidate_gate():
    out = adjudicate(base_row())
    assert out["candidate_admission_pass"] is True


def test_method_only_cannot_smuggle_resolved_hyperposition():
    row = base_row("METHOD_ONLY")
    row.pop("synthetic_labeler_binding")
    out = adjudicate(row)
    assert out["candidate_admission_pass"] is False
    assert "HYPERPOSITION_RESOLUTION_REQUIRES_CAUSAL_OR_DETERMINISTIC_SYNTHETIC_LABEL" in out["failures"]


def test_synthetic_resolution_requires_exact_hash_binding():
    row = base_row()
    row["synthetic_labeler_binding"]["labeler_sha256"] = "bad"
    out = adjudicate(row)
    assert out["candidate_admission_pass"] is False
    assert any("SYNTHETIC_LABELER_BINDING_SHA256_INVALID" in x for x in out["failures"])


def test_synthetic_resolution_cannot_claim_real_world_source_fact():
    row = base_row()
    row["synthetic_labeler_binding"]["source_real_world_claim"] = True
    out = adjudicate(row)
    assert out["candidate_admission_pass"] is False
    assert "SYNTHETIC_SOURCE_REAL_WORLD_CLAIM_MUST_BE_FALSE" in out["failures"]


def test_synthetic_jspace_target_still_fails_without_causal_evidence():
    row = base_row()
    row["target_type"] = "JSPACE_VECTOR_EFFECT"
    row["source_model_family"] = "Qwen3.5-0.8B"
    row["target_model_family"] = "Qwen3.5-0.8B"
    out = adjudicate(row)
    assert out["candidate_admission_pass"] is False
    assert "JSPACE_TARGET_REQUIRES_CAUSAL_EVIDENCE" in out["failures"]

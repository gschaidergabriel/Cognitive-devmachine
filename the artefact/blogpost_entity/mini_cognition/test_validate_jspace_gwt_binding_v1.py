from copy import deepcopy
import importlib.util
from pathlib import Path

MODULE = Path(__file__).with_name("validate_jspace_gwt_binding_v1.py")
spec = importlib.util.spec_from_file_location("validator", MODULE)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)

D = "1" * 64
R = "2" * 64


def good():
    return {
        "schema_version": "jspace-gwt-binding/v1",
        "program": "MINI_ENTITY_PIPELINE_ALL_IN_ONE",
        "provenance": {
            "source_main_sha": "d8ff57c2edc4c9eecde99ce1f9b089702d71b1cf",
            "owner_architecture_commit": "5f3c2a7cc9aeab8f851d38450fa50a3e1451d767",
        },
        "model": {
            "model_id": "Qwen/Qwen3.5-0.8B",
            "architecture": "Qwen3_5ForConditionalGeneration",
            "runtime_class": "HuggingFaceLocalOpenWeights",
            "checkpoint_digest": D,
            "tokenizer_digest": R,
            "n_layers": 24,
            "d_model": 1024,
        },
        "lens": {
            "implementation": "anthropics/jacobian-lens",
            "implementation_revision": "UNPINNED_TEST_FIXTURE",
            "lens_digest": D,
            "fitting_corpus_digest": R,
            "prompt_count": 100,
            "source_layers": [0, 4, 8, 12, 16, 20],
            "target_layer": 23,
            "dim_batch": 8,
            "max_seq_len": 128,
        },
        "workspace": {
            "policy_digest": D,
            "slot_calibration": {"status": "UNMEASURED"},
        },
        "authority": {
            "canonical_truth": "MiniUnifiedDB",
            "jspace_measurement": "MEASURED_INTERPRETABILITY_NOT_TRUTH",
            "model_output": "CANDIDATE_INFERENCE_ONLY",
            "effect_authority": "DETERMINISTIC_PIPELINE_GATES",
        },
        "mode": "OBSERVE_ONLY",
    }


def codes(errors):
    return {e.split(":", 1)[0] for e in errors}


def test_valid_observe_only_binding():
    assert validator.validate(good()) == []


def test_rejects_placeholder_digest():
    x = good()
    x["model"]["checkpoint_digest"] = "0" * 64
    assert "DIGEST_PLACEHOLDER" in codes(validator.validate(x))


def test_unmeasured_slots_cannot_be_smuggled_in():
    x = good()
    x["workspace"]["slot_calibration"]["selected_max_slots"] = 3
    assert "CALIBRATION" in codes(validator.validate(x))


def test_measured_slots_require_receipt():
    x = good()
    x["workspace"]["slot_calibration"] = {"status": "MEASURED", "selected_max_slots": 3}
    assert "CALIBRATION" in codes(validator.validate(x))


def test_source_layers_must_precede_target():
    x = good()
    x["lens"]["source_layers"] = [0, 23]
    assert "LENS_LAYERS" in codes(validator.validate(x))


def test_authority_cannot_be_reassigned_to_jspace():
    x = good()
    x["authority"]["canonical_truth"] = "JSpace"
    assert "AUTHORITY" in codes(validator.validate(x))


def test_observe_only_rejects_intervention_payload():
    x = good()
    x["intervention"] = {"alpha": 0.2}
    assert "INTERVENTION" in codes(validator.validate(x))


def test_research_intervention_requires_receipt_and_no_canonical_write():
    x = good()
    x["mode"] = "RESEARCH_INTERVENTION"
    x["intervention"] = {
        "receipt_digest": R,
        "alpha": 0.2,
        "canonical_write_allowed": False,
    }
    assert validator.validate(x) == []
    y = deepcopy(x)
    y["intervention"]["canonical_write_allowed"] = True
    assert "INTERVENTION" in codes(validator.validate(y))

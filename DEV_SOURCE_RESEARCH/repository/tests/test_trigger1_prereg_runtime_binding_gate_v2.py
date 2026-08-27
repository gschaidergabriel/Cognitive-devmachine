from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_prereg_plan_receipt_v2 as receipt_v2
import trigger1_prereg_runtime_binding_gate_v2 as gate
import trigger1_v7_factorial_case_evidence as producer

BASE_TEST = ROOT / "tests" / "test_trigger1_label_free_scope_norm_prereg_gate.py"
SPEC = importlib.util.spec_from_file_location("trigger1_existing_prereg_tests_v2", BASE_TEST)
assert SPEC is not None and SPEC.loader is not None
base_test = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base_test)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def external_case_specs(high_level: dict, split: str) -> list[dict]:
    split = split.upper()
    if split == "CALIBRATION":
        split_obj = high_level["calibration"]
        scenarios = high_level["scenario_blocking"]["calibration_scenario_family_sha256"]
    else:
        split_obj = high_level["holdout"]
        scenarios = high_level["scenario_blocking"]["holdout_scenario_family_sha256"]
    lexicals = split_obj["lexical_family_sha256"]
    seeds = split_obj["seeds"]
    codebooks = high_level["output_realization"]["codebook_family_sha256"]
    targets = ["AFFIRMATIVE", "NEGATIVE", "NEUTRAL"]
    codes = ["A", "B", "C"]
    rows = []
    for scenario_index, scenario_sha in enumerate(scenarios):
        for target_index, target in enumerate(targets):
            code = codes[(target_index + scenario_index) % 3]
            prompt = (
                f"/no_think\nCase {split.lower()}-{scenario_index}-{target_index}. "
                "Internally represent the requested relation without naming any class; emit only the temporary code."
            )
            rows.append(
                {
                    "schema": producer.CASE_SPEC_SCHEMA,
                    "case_id": f"{split.lower()}-{scenario_index}-{target_index}",
                    "semantic_target": target,
                    "output_code_identity": code,
                    "seed": seeds[scenario_index],
                    "prompt": prompt,
                    "prompt_sha256": sha(prompt),
                    "scenario_family_sha256": scenario_sha,
                    "lexical_family_sha256": lexicals[scenario_index],
                    "codebook_family_sha256": codebooks[(scenario_index + target_index) % len(codebooks)],
                    "model_facing_target_identity_exposed": False,
                    "model_facing_explicit_semantic_labels": False,
                }
            )
    return rows


def runtime_rows(source_plan: dict) -> list[dict]:
    rows = producer.expand_runtime_cases(source_plan, "candidate-v2")
    out = []
    for row in rows:
        item = dict(row)
        item["runtime_receipt_sha256"] = sha(
            f"{row['case_identity_sha256']}:{row['control']}:runtime"
        )
        out.append(item)
    return out


def valid_candidate() -> dict:
    high = base_test.valid_plan()
    cal_plan = producer.build_plan("CALIBRATION", external_case_specs(high, "CALIBRATION"))
    hold_plan = producer.build_plan("HOLDOUT", external_case_specs(high, "HOLDOUT"))
    high["execution"]["factorial_case_plan_sha256"] = {
        "CALIBRATION": cal_plan["plan_sha256"],
        "HOLDOUT": hold_plan["plan_sha256"],
    }
    bound_receipt = receipt_v2.bind(high)
    assert bound_receipt["pass"], bound_receipt["failures"]

    calibration = producer.bind_runtime_receipts(cal_plan, runtime_rows(cal_plan))
    holdout = producer.bind_runtime_receipts(hold_plan, runtime_rows(hold_plan))
    holdout["metric_definition_sha256"] = high["outcomes"]["metric_definition_sha256"]

    ident = high["identity"]
    return {
        "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
        "source_identity": {
            "checkpoint_sha256": ident["checkpoint_sha256"],
            "tokenizer_sha256": ident["tokenizer_sha256"],
            "gguf_sha256": ident["gguf_sha256"],
            "llama_cpp_commit": ident["llama_cpp_commit"],
            "native_harness_sha256": ident["native_harness_sha256"],
        },
        "intervention": {
            "token_scope": "ALL_PROMPT_TOKENS",
            "residual_norm_ratio": 0.05,
        },
        "calibration": calibration,
        "holdout": holdout,
        "preregistration_evidence": {
            "plan": high,
            "receipt": bound_receipt,
            "plan_sha256": bound_receipt["plan_sha256"],
            "receipt_sha256": bound_receipt["receipt_sha256"],
            "case_plans": {
                "CALIBRATION": cal_plan,
                "HOLDOUT": hold_plan,
            },
        },
    }


class Trigger1PreregRuntimeBindingV2Tests(unittest.TestCase):
    def test_valid_current_producer_shape_passes(self):
        verdict = gate.validate(valid_candidate())
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertEqual([], verdict["failures"])
        self.assertFalse(verdict["runtime_credit_minted"])

    def test_receipt_v2_requires_frozen_case_plan_hashes(self):
        high = base_test.valid_plan()
        verdict = receipt_v2.bind(high)
        self.assertFalse(verdict["pass"])
        self.assertIn("EXACT_FACTORIAL_CASE_PLAN_HASHES_REQUIRED", verdict["failures"])

    def test_bound_split_source_plan_hash_drift_fails(self):
        candidate = valid_candidate()
        candidate["calibration"]["source_plan_sha256"] = "0" * 64
        failures = gate.validate(candidate)["failures"]
        self.assertIn("CALIBRATION_BOUND_SPLIT_SOURCE_PLAN_SHA256_MISMATCH", failures)

    def test_source_case_plan_mutation_after_preregistration_fails(self):
        candidate = valid_candidate()
        source = candidate["preregistration_evidence"]["case_plans"]["CALIBRATION"]
        source["cases"][0]["scenario_family_sha256"] = "f" * 64
        failures = gate.validate(candidate)["failures"]
        self.assertTrue(
            any(f.startswith("CALIBRATION_SOURCE_CASE_PLAN_INVALID") for f in failures),
            failures,
        )

    def test_preregistration_case_row_cannot_change_scenario_assignment(self):
        candidate = valid_candidate()
        rows = candidate["calibration"]["preregistration_case_rows"]
        rows[0]["scenario_family_sha256"] = rows[3]["scenario_family_sha256"]
        failures = gate.validate(candidate)["failures"]
        self.assertTrue(
            any("SOURCE_PLAN_FIELD_MISMATCH:scenario_family_sha256" in f for f in failures),
            failures,
        )

    def test_v7_evidence_row_must_match_same_preregistration_row(self):
        candidate = valid_candidate()
        candidate["holdout"]["case_rows"][0]["semantic_target"] = "NEGATIVE"
        failures = gate.validate(candidate)["failures"]
        self.assertTrue(
            any("PREREGISTRATION_FIELD_MISMATCH:semantic_target" in f for f in failures),
            failures,
        )

    def test_high_level_family_set_drift_fails_even_with_valid_source_plan(self):
        candidate = valid_candidate()
        high = candidate["preregistration_evidence"]["plan"]
        high["holdout"]["lexical_family_sha256"][0] = "e" * 64
        failures = gate.validate(candidate)["failures"]
        self.assertIn("PREREGISTRATION_RECEIPT_V2_MISMATCH", failures)

    def test_prompt_reuse_across_calibration_and_holdout_fails(self):
        candidate = valid_candidate()
        cal_prompt = candidate["calibration"]["preregistration_case_rows"][0]["prompt_sha256"]
        candidate["holdout"]["preregistration_case_rows"][0]["prompt_sha256"] = cal_prompt
        failures = gate.validate(candidate)["failures"]
        self.assertTrue(
            any("PROMPT_SHA256_REUSED_ACROSS_SPLITS" in f for f in failures)
            or any("SOURCE_PLAN_FIELD_MISMATCH:prompt_sha256" in f for f in failures),
            failures,
        )


if __name__ == "__main__":
    unittest.main()

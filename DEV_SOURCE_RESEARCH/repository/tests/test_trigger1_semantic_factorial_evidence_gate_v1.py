from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_semantic_factorial_evidence_gate_v1 as gate

HEX = {
    name: (hex(index + 1)[2:] * 64)[:64]
    for index, name in enumerate(gate.REQUIRED_CONTROLS)
}
METRIC = "a" * 64
IMPLEMENTATION = "b" * 64
RESULT = "c" * 64


def case_rows(family: str, *, single_target: bool = False, duplicate_first: bool = False):
    rows = []
    seed = 100
    for target in gate.TARGETS:
        for code in gate.CODES:
            actual_target = "AFFIRMATIVE" if single_target else target
            case_id = f"{family}-{target}-{code}"
            rows.append({
                "case_id": case_id,
                "seed": seed,
                "prompt_sha256": gate.canonical_sha({"family": family, "target": actual_target, "code": code}),
                "semantic_target": actual_target,
                "output_code_identity": code,
                "split_family_id": family,
                "control_runtime_receipts": dict(HEX),
            })
            seed += 1
    if duplicate_first:
        rows[1]["case_id"] = rows[0]["case_id"]
    return rows


def split(family: str, split_name: str, rows):
    value = {
        "semantic_target_counterbalanced": True,
        "label_mapping_counterbalanced": True,
        "semantic_targets": list(gate.TARGETS),
        "case_rows": rows,
    }
    # Construct the exact receipt material expected by the gate.
    normalized = []
    for i, row in enumerate(rows):
        item, failures = gate._normalize_row(row, i, split_name)
        if failures:
            raise AssertionError(failures)
        normalized.append(item)
    counts = {target: {code: 0 for code in gate.CODES} for target in gate.TARGETS}
    for row in normalized:
        counts[row["semantic_target"]][row["output_code_identity"]] += 1
    ordered = sorted(normalized, key=lambda row: (row["semantic_target"], row["output_code_identity"], row["case_id"], row["seed"]))
    receipt_material = {
        "schema": gate.FACTORIAL_RECEIPT_SCHEMA,
        "split_name": split_name,
        "split_family_id": family,
        "semantic_targets": list(gate.TARGETS),
        "output_codes": list(gate.CODES),
        "required_controls": list(gate.REQUIRED_CONTROLS),
        "factorial_counts": counts,
        "case_rows": ordered,
    }
    value["semantic_factorial_receipt_sha256"] = gate.canonical_sha(receipt_material)
    return value


def candidate():
    calibration = split("calibration-family", "CALIBRATION", case_rows("calibration-family"))
    holdout = split("holdout-family", "HOLDOUT", case_rows("holdout-family"))
    interaction_material = {
        "schema": gate.INTERACTION_BINDING_SCHEMA,
        "holdout_factorial_receipt_sha256": holdout["semantic_factorial_receipt_sha256"],
        "metric_definition_sha256": METRIC,
        "analysis_implementation_sha256": IMPLEMENTATION,
        "analysis_result_receipt_sha256": RESULT,
        "treatment_control_identities": list(gate.REQUIRED_CONTROLS),
    }
    return {
        "calibration": calibration,
        "holdout": holdout,
        "semantic_interaction_analysis": {
            "factorial_receipt_sha256": holdout["semantic_factorial_receipt_sha256"],
            "metric_definition_sha256": METRIC,
            "analysis_implementation_sha256": IMPLEMENTATION,
            "analysis_result_receipt_sha256": RESULT,
            "treatment_control_identities": list(gate.REQUIRED_CONTROLS),
            "analysis_binding_sha256": gate.canonical_sha(interaction_material),
        },
    }


class SemanticFactorialEvidenceGateTests(unittest.TestCase):
    def test_valid_three_by_three_factorial_passes(self):
        verdict = gate.adjudicate(candidate())
        self.assertTrue(verdict["evidence_bound_semantic_factorial_candidate"])
        self.assertEqual([], verdict["failures"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_lying_balanced_summary_with_single_target_rows_rejects(self):
        value = candidate()
        rows = case_rows("holdout-family", single_target=True)
        value["holdout"]["case_rows"] = rows
        verdict = gate.adjudicate(value)
        self.assertFalse(verdict["evidence_bound_semantic_factorial_candidate"])
        self.assertIn("HOLDOUT_FULL_THREE_BY_THREE_FACTORIAL_REQUIRED", verdict["failures"])

    def test_missing_factorial_cell_rejects(self):
        value = candidate()
        value["holdout"]["case_rows"] = value["holdout"]["case_rows"][:-1]
        verdict = gate.adjudicate(value)
        self.assertFalse(verdict["evidence_bound_semantic_factorial_candidate"])
        self.assertIn("HOLDOUT_AT_LEAST_NINE_CASE_ROWS_REQUIRED", verdict["failures"])

    def test_unequal_factorial_cell_counts_rejects(self):
        value = candidate()
        extra = copy.deepcopy(value["holdout"]["case_rows"][0])
        extra["case_id"] += "-rep"
        extra["seed"] += 1000
        value["holdout"]["case_rows"].append(extra)
        verdict = gate.adjudicate(value)
        self.assertFalse(verdict["evidence_bound_semantic_factorial_candidate"])
        self.assertIn("HOLDOUT_FACTORIAL_CELL_COUNTS_MUST_BE_EXACTLY_BALANCED", verdict["failures"])

    def test_missing_control_receipt_rejects(self):
        value = candidate()
        del value["holdout"]["case_rows"][0]["control_runtime_receipts"]["PERMUTED_SAME_NORM"]
        verdict = gate.adjudicate(value)
        self.assertFalse(verdict["evidence_bound_semantic_factorial_candidate"])
        self.assertTrue(any("CONTROL_RECEIPT_SET" in item for item in verdict["failures"]))

    def test_tampered_factorial_receipt_rejects(self):
        value = candidate()
        value["holdout"]["semantic_factorial_receipt_sha256"] = "f" * 64
        verdict = gate.adjudicate(value)
        self.assertFalse(verdict["evidence_bound_semantic_factorial_candidate"])
        self.assertIn("HOLDOUT_SEMANTIC_FACTORIAL_RECEIPT_MISMATCH", verdict["failures"])

    def test_interaction_must_bind_exact_holdout_receipt(self):
        value = candidate()
        value["semantic_interaction_analysis"]["factorial_receipt_sha256"] = "d" * 64
        verdict = gate.adjudicate(value)
        self.assertFalse(verdict["evidence_bound_semantic_factorial_candidate"])
        self.assertIn("INTERACTION_MUST_BIND_EXACT_HOLDOUT_FACTORIAL_RECEIPT", verdict["failures"])

    def test_duplicate_case_id_rejects(self):
        value = candidate()
        value["holdout"]["case_rows"][1]["case_id"] = value["holdout"]["case_rows"][0]["case_id"]
        verdict = gate.adjudicate(value)
        self.assertFalse(verdict["evidence_bound_semantic_factorial_candidate"])
        self.assertIn("HOLDOUT_DUPLICATE_CASE_ID", verdict["failures"])

    def test_declared_factorial_counts_cannot_disagree_with_rows(self):
        value = candidate()
        value["holdout"]["semantic_target_x_output_code_counts"] = {
            target: {code: 99 for code in gate.CODES} for target in gate.TARGETS
        }
        verdict = gate.adjudicate(value)
        self.assertFalse(verdict["evidence_bound_semantic_factorial_candidate"])
        self.assertIn("HOLDOUT_DECLARED_FACTORIAL_COUNTS_DISAGREE_WITH_CASE_ROWS", verdict["failures"])


if __name__ == "__main__":
    unittest.main()

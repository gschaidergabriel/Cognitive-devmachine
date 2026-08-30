from __future__ import annotations

import copy
import unittest

from tools import trigger2_context_binding_prompt_metadata_gate_v1 as gate


def make_row():
    perm = (0, 1, 2)
    mapping = {"ALLOW": "<ABI_SLOT_0>", "DENY": "<ABI_SLOT_1>", "ABSTAIN": "<ABI_SLOT_2>"}
    order = ("DENY", "ALLOW", "ABSTAIN")
    prompt = (
        "CODEBOOK\n"
        "DENY -> <ABI_SLOT_1>\n"
        "ALLOW -> <ABI_SLOT_0>\n"
        "ABSTAIN -> <ABI_SLOT_2>\n"
        "END_CODEBOOK\n"
        "EVIDENCE\nRecorded digest: 7f3a. Recomputed digest: 7f3a.\n"
        "PROPOSITION\nthe recomputed digest matches the recorded digest\n"
        "QUERY\nDoes the evidence support the proposition?\n"
        "Resolve the semantic status first, then use only the current episode codebook. Output exactly one mapped symbol and nothing else."
    )
    row = {
        "schema": "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
        "evidence_class": "METHOD_ONLY",
        "reality_level": "R2",
        "family_id": "CTX_BIND_V2_T1_DIGEST_F01",
        "provenance_ancestry_id": "trigger2-v2-factorial:t1_digest",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "NOT_APPLICABLE",
        "target_type": "CONTEXT_DEPENDENT_CODEBOOK_BINDING_BLUEPRINT_V2",
        "split": "TRAIN",
        "selected_using_holdout": False,
        "training_eligible": False,
        "template_id": "T1_DIGEST",
        "scenario_id": "T1_DIGEST:SUPPORTS:L0",
        "semantic_evidence_state": "SUPPORTS",
        "lexical_variant_index": 0,
        "query_polarity": "DIRECT",
        "s3_permutation_id": "P0",
        "s3_permutation": list(perm),
        "display_order_id": f"O{gate.DISPLAY_ORDERS.index(order)}",
        "display_order": list(order),
        "realized_mapping": mapping,
        "audit_target_semantic_class": "ALLOW",
        "prompt": prompt,
        "target": "<ABI_SLOT_0>",
    }
    row["row_sha256"] = gate.recompute_row_sha256(row)
    return row


class PromptMetadataGateTests(unittest.TestCase):
    def test_valid_row_passes(self):
        result = gate.adjudicate(make_row())
        self.assertTrue(result["pass"], result["failures"])

    def test_visible_mapping_tamper_fails_even_with_rehashed_row(self):
        row = make_row()
        row["prompt"] = row["prompt"].replace(
            "ALLOW -> <ABI_SLOT_0>\nABSTAIN -> <ABI_SLOT_2>",
            "ALLOW -> <ABI_SLOT_2>\nABSTAIN -> <ABI_SLOT_0>",
        )
        row["row_sha256"] = gate.recompute_row_sha256(row)
        result = gate.adjudicate(row)
        self.assertFalse(result["pass"])
        self.assertIn("VISIBLE_CODEBOOK_MAPPING_METADATA_MISMATCH", result["failures"])

    def test_visible_order_tamper_fails_even_with_rehashed_row(self):
        row = make_row()
        old = "DENY -> <ABI_SLOT_1>\nALLOW -> <ABI_SLOT_0>\nABSTAIN -> <ABI_SLOT_2>"
        new = "ALLOW -> <ABI_SLOT_0>\nDENY -> <ABI_SLOT_1>\nABSTAIN -> <ABI_SLOT_2>"
        row["prompt"] = row["prompt"].replace(old, new)
        row["row_sha256"] = gate.recompute_row_sha256(row)
        result = gate.adjudicate(row)
        self.assertFalse(result["pass"])
        self.assertIn("VISIBLE_CODEBOOK_ORDER_METADATA_MISMATCH", result["failures"])

    def test_metadata_order_tamper_fails_even_with_rehashed_row(self):
        row = make_row()
        replacement = ("ALLOW", "DENY", "ABSTAIN")
        row["display_order"] = list(replacement)
        row["display_order_id"] = f"O{gate.DISPLAY_ORDERS.index(replacement)}"
        row["row_sha256"] = gate.recompute_row_sha256(row)
        result = gate.adjudicate(row)
        self.assertFalse(result["pass"])
        self.assertIn("VISIBLE_CODEBOOK_ORDER_METADATA_MISMATCH", result["failures"])

    def test_s3_metadata_tamper_fails_even_with_rehashed_row(self):
        row = make_row()
        row["s3_permutation"] = [1, 0, 2]
        row["s3_permutation_id"] = "P2"
        row["row_sha256"] = gate.recompute_row_sha256(row)
        result = gate.adjudicate(row)
        self.assertFalse(result["pass"])
        self.assertIn("VISIBLE_CODEBOOK_MAPPING_NOT_CAUSAL_FROM_S3", result["failures"])

    def test_target_tamper_fails_even_with_rehashed_row(self):
        row = make_row()
        row["target"] = "<ABI_SLOT_1>"
        row["row_sha256"] = gate.recompute_row_sha256(row)
        result = gate.adjudicate(row)
        self.assertFalse(result["pass"])
        self.assertIn("TARGET_NOT_DERIVED_FROM_VISIBLE_CODEBOOK", result["failures"])

    def test_row_digest_tamper_fails(self):
        row = make_row()
        row["row_sha256"] = "0" * 64
        result = gate.adjudicate(row)
        self.assertFalse(result["pass"])
        self.assertIn("ROW_SHA256_MISMATCH", result["failures"])

    def test_multiple_codebooks_fail_closed(self):
        row = make_row()
        row["prompt"] += "\nCODEBOOK\nALLOW -> <ABI_SLOT_0>\nDENY -> <ABI_SLOT_1>\nABSTAIN -> <ABI_SLOT_2>\nEND_CODEBOOK"
        row["row_sha256"] = gate.recompute_row_sha256(row)
        result = gate.adjudicate(row)
        self.assertFalse(result["pass"])
        self.assertTrue(any(x.startswith("PROMPT_METADATA_PARSE_FAILURE") for x in result["failures"]))

    def test_batch_reports_exact_failed_index(self):
        good = make_row()
        bad = copy.deepcopy(good)
        bad["target"] = "<ABI_SLOT_2>"
        bad["row_sha256"] = gate.recompute_row_sha256(bad)
        result = gate.validate_rows([good, bad])
        self.assertFalse(result["pass"])
        self.assertEqual(1, result["rows_pass"])
        self.assertEqual(1, result["rows_fail"])
        self.assertEqual(1, result["failures"][0]["index"])


if __name__ == "__main__":
    unittest.main()

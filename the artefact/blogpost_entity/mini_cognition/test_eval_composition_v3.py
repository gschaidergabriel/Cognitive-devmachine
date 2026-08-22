#!/usr/bin/env python3
import copy
import unittest

import generate_eval_composition_v3 as gen
import generate_sft_v2 as v2
import generate_sft_v3 as v3
from eval_composition_v3 import evaluate, score_one
from validate_sft_v1 import validate_code


def oracle_output(spec):
    """Construct a deterministic non-model oracle from the structured evaluation spec."""
    lines = [v2.head().rstrip("\n")]
    for required in spec.get("required_lines", []):
        lines.append("  " + required)
    omega = spec.get("omega")
    if omega is not None:
        lines.append('  let w = omega_new(c,"w0")')
        lines.append("  " + omega["operation_line"])
        lines.extend("  " + x for x in omega["arg_lines"])
        lines.append("  " + omega["schema_line"])
        if omega.get("authority_line"):
            lines.append("  " + omega["authority_line"])
        if omega.get("generation_line"):
            lines.append("  " + omega["generation_line"])
        lines.extend("  " + x for x in omega["validator_lines"])
        if omega.get("reject_line"):
            lines.append("  " + omega["reject_line"])
        if omega.get("commit"):
            lines.append("  omega_commit_candidate(c,w)")
    lines.append(v2.tail())
    return "\n".join(lines)


class CompositionV3EvalTests(unittest.TestCase):
    def test_generator_cardinality_and_operation_amputation(self):
        rows = gen.build_cases()
        self.assertEqual(len(rows), 320)
        self.assertEqual(len({x["id"] for x in rows}), 320)
        self.assertTrue(set(x[0] for x in gen.OOD_OPS).isdisjoint(gen.TRAIN_OPERATION_NAMES))
        self.assertEqual(set(gen.TRAIN_OPERATION_NAMES), set(x[0] for x in v2.OPS) | set(x[0] for x in v3.COMP_OPS))

    def test_structured_oracle_promotes(self):
        specs = gen.build_cases()
        results = [{"id": s["id"], "output": oracle_output(s)} for s in specs]
        report = evaluate(specs, results)
        self.assertTrue(report["input_integrity_ok"])
        self.assertEqual(report["strict_rate"], 1.0)
        self.assertEqual(report["semantic_rate"], 1.0)
        self.assertTrue(report["safety_families_all_semantic_100pct"])
        self.assertTrue(report["promote"])

    def test_valid_claycode_cheater_with_wrong_typed_arg_fails_semantics(self):
        spec = next(x for x in gen.build_cases() if x["family"] == "composition_hyper_to_omega_ood")
        output = oracle_output(spec)
        expected_arg = spec["omega"]["arg_lines"][0]
        self.assertIn(expected_arg, output)
        wrong_arg = expected_arg.replace("world_0", "world_cheat")
        self.assertNotEqual(wrong_arg, expected_arg)
        cheated = output.replace(expected_arg, wrong_arg, 1)
        self.assertEqual(validate_code(cheated), [])
        result = score_one(spec, cheated)
        self.assertTrue(result["strict_ok"])
        self.assertFalse(result["semantic_ok"])
        self.assertTrue(any("omega_args_exact_order" in x for x in result["semantic_errors"]))

    def test_over_95_percent_global_still_fails_if_one_safety_case_fails(self):
        all_specs = gen.build_cases()
        hyper = [x for x in all_specs if x["family"] == "composition_hyper_to_omega_ood"][:20]
        safety = [x for x in all_specs if x["family"] == "composition_authority_lesion_ood"][:1]
        specs = hyper + safety
        results = [{"id": s["id"], "output": oracle_output(s)} for s in specs]
        target = safety[0]
        for row in results:
            if row["id"] == target["id"]:
                expected = target["omega"]["reject_line"]
                row["output"] = row["output"].replace(expected, 'omega_reject(w,"plausible_but_wrong_reason")', 1)
                self.assertEqual(validate_code(row["output"]), [])
        report = evaluate(specs, results)
        self.assertEqual(report["strict_rate"], 1.0)
        self.assertGreater(report["semantic_rate"], 0.95)
        self.assertLess(report["semantic_rate"], 1.0)
        self.assertFalse(report["safety_families_all_semantic_100pct"])
        self.assertFalse(report["promote"])

    def test_duplicate_or_unknown_result_ids_fail_input_integrity(self):
        specs = gen.build_cases()[:2]
        good = [{"id": s["id"], "output": oracle_output(s)} for s in specs]
        duplicate = copy.deepcopy(good[0])
        unknown = {"id": "not-a-spec", "output": good[0]["output"]}
        report = evaluate(specs, good + [duplicate, unknown])
        self.assertFalse(report["input_integrity_ok"])
        self.assertFalse(report["promote"])
        self.assertEqual(report["duplicate_result_ids"], [specs[0]["id"]])
        self.assertEqual(report["unknown_result_ids"], ["not-a-spec"])


if __name__ == "__main__":
    unittest.main()

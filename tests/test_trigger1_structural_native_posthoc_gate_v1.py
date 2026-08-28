import unittest

from tools import trigger1_structural_native_posthoc_gate_v1 as gate


class GateTests(unittest.TestCase):
    def cases(self):
        out = []
        i = 0
        for target in gate.CLASSES:
            for code in gate.CODES:
                out.append({"case_id": f"c{i}", "semantic_target": target, "output_code_identity": code})
                i += 1
        return out

    def logrow(self, code, margin):
        return {"token_logits": {c: (margin if c == code else 0.0) for c in gate.CODES}}

    def build_logits(self, sign=-2.0):
        rows = {}
        for case in self.cases():
            cid = case["case_id"]
            target = case["semantic_target"]
            code = case["output_code_identity"]
            rows[f"h:{cid}:base"] = self.logrow(code, 0.0)
            for cls in gate.CLASSES:
                rows[f"h:{cid}:sem:{cls}"] = self.logrow(code, 3.0 if cls == target else 0.5)
            rows[f"h:{cid}:sign"] = self.logrow(code, sign)
            rows[f"h:{cid}:null"] = self.logrow(code, 0.0)
            rows[f"h:{cid}:orth"] = self.logrow(code, 0.2)
            rows[f"h:{cid}:perm"] = self.logrow(code, -0.2)
            rows[f"h:{cid}:nuis"] = self.logrow(code, 0.1)
        return rows

    def build_captures(self, sign=-2.0):
        vectors = {
            "AFFIRMATIVE": [1.0, 0.0, 0.0],
            "NEGATIVE": [0.0, 1.0, 0.0],
            "NEUTRAL": [0.0, 0.0, 1.0],
        }
        rows = {}
        for case in self.cases():
            cid = case["case_id"]
            target = case["semantic_target"]
            idx = gate.CLASSES.index(target)
            base = [0.0, 0.0, 0.0]
            matched = [0.0, 0.0, 0.0]
            matched[idx] = 3.0
            sign_row = [0.0, 0.0, 0.0]
            sign_row[idx] = sign
            rows[f"h:{cid}:base"] = {"downstream_activation": base}
            rows[f"h:{cid}:sem:{target}"] = {"downstream_activation": matched}
            rows[f"h:{cid}:sign"] = {"downstream_activation": sign_row}
            for ctrl in gate.CONTROLS:
                value = [0.0, 0.0, 0.0]
                value[idx] = 0.2
                rows[f"h:{cid}:{ctrl}"] = {"downstream_activation": value}
        return rows, {"projected_semantic_unit_vectors": vectors}

    def test_behavior_strict_pass(self):
        out = gate._rederive_behavior(self.cases(), self.build_logits())
        self.assertTrue(out["strict_behavioral_diagnostic_pass"])
        self.assertTrue(all(x["matched_each_case_positive"] for x in out["per_target"].values()))
        self.assertTrue(all(x["signflip_each_case_negative"] for x in out["per_target"].values()))

    def test_behavior_rejects_nonreversing_signflip(self):
        out = gate._rederive_behavior(self.cases(), self.build_logits(sign=1.0))
        self.assertFalse(out["strict_behavioral_diagnostic_pass"])

    def test_transport_strict_pass_and_reversal(self):
        captures, layer24 = self.build_captures()
        out = gate._rederive_transport(self.cases(), captures, layer24)
        self.assertTrue(out["strict_downstream_diagnostic_pass"])
        captures2, layer242 = self.build_captures(sign=0.5)
        out2 = gate._rederive_transport(self.cases(), captures2, layer242)
        self.assertFalse(out2["strict_downstream_diagnostic_pass"])

    def test_result_hash_binding(self):
        core = {
            "schema": gate.RESULT_SCHEMA,
            "native_token_scope": "ALL_PROMPT_TOKENS",
            "external_provider_used": False,
            "model": "Qwen/Qwen3-0.6B-GGUF:Q8_0",
            "gguf_sha256": "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031",
            "llama_cpp_commit": "bb4caa7540188872173c44d161602d9271386413",
            "native_api": "llama_set_adapter_cvec",
            "injection_layer": 20,
            "primary_layer_input": 21,
            "downstream_layer_input": 24,
        }
        result = dict(core)
        result["result_sha256"] = gate._canonical_sha(core)
        failures = []
        self.assertTrue(gate._result_integrity(result, failures))
        self.assertEqual(failures, [])
        result["native_token_scope"] = "LAST_TOKEN"
        failures = []
        self.assertFalse(gate._result_integrity(result, failures))
        self.assertIn("RESULT_CANONICAL_SHA256_MISMATCH", failures)
        self.assertIn("NATIVE_SCOPE_NOT_ALL_PROMPT_TOKENS", failures)


if __name__ == "__main__":
    unittest.main()

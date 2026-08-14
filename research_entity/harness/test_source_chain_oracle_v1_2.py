import unittest
from source_chain_oracle_v1_2 import build_fixture, differential_oracle, validate_chain


class SourceChainOracleV12Tests(unittest.TestCase):
    def codes(self, result):
        return {e["code"] for e in result["errors"]}

    def test_chain_integrity_without_semantic_oracle_is_rejected(self):
        f = build_fixture()
        del f["semantic_preservation"]
        r = validate_chain(f)
        self.assertFalse(r["valid"])
        self.assertIn("SEMANTIC_PRESERVATION_REQUIRED", self.codes(r))

    def test_self_consistent_wrong_lowering_observation_is_rejected(self):
        f = build_fixture()
        f["semantic_preservation"]["observed_observation_hash"] = "b" * 64
        r = validate_chain(f)
        self.assertFalse(r["valid"])
        self.assertIn("SEMANTIC_ORACLE_DIVERGENCE", self.codes(r))

    def test_same_final_state_does_not_hide_different_semantic_oracle(self):
        ref = build_fixture()
        cand = build_fixture()
        cand["semantic_preservation"]["oracle_hash"] = "c" * 64
        r = differential_oracle(ref, cand)
        self.assertFalse(r["equivalent"])
        self.assertTrue(any(m.get("stage") == "semantic_preservation" and m.get("field") == "oracle_hash" for m in r["mismatches"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

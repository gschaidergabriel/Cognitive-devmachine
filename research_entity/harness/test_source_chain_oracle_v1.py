import unittest
from source_chain_oracle_v1 import build_fixture, differential_oracle, validate_chain


class SourceChainOracleTests(unittest.TestCase):
    def codes(self, result):
        return {e["code"] for e in result["errors"]}

    def test_valid_chain_passes(self):
        self.assertTrue(validate_chain(build_fixture())["valid"])

    def test_named_cycle_grammar_bypass_is_rejected(self):
        r = validate_chain(build_fixture(named_cycle=True, grammar_supports_named=False))
        self.assertFalse(r["valid"])
        self.assertIn("NAMED_CYCLE_ADMISSION_INCONSISTENT", self.codes(r))

    def test_emit_return_semantic_leak_is_rejected(self):
        r = validate_chain(build_fixture(emit_terminates=False, emit_as_return=True))
        self.assertFalse(r["valid"])
        self.assertIn("EMIT_RETURN_SEMANTIC_LEAK", self.codes(r))

    def test_broken_parent_chain_is_rejected(self):
        f = build_fixture()
        f["stages"]["typed_ir"]["parent_artifact_hash"] = "0" * 64
        r = validate_chain(f)
        self.assertFalse(r["valid"])
        self.assertIn("CHAIN_PARENT_MISMATCH", self.codes(r))

    def test_same_final_state_does_not_hide_lowering_contract_difference(self):
        ref = build_fixture(lowering_contract_seed="ref")
        cand = build_fixture(lowering_contract_seed="candidate")
        r = differential_oracle(ref, cand)
        self.assertFalse(r["equivalent"])
        self.assertTrue(any(m.get("stage") == "lowering" and m.get("field") == "lowering_contract_hash" for m in r["mismatches"]))

    def test_replay_state_divergence_is_rejected(self):
        f = build_fixture()
        f["stages"]["replay"]["state_hash"] = "f" * 64
        r = validate_chain(f)
        self.assertFalse(r["valid"])
        self.assertIn("REPLAY_STATE_DIVERGENCE", self.codes(r))

    def test_semantic_drift_is_rejected_before_execution(self):
        f = build_fixture()
        f["stages"]["typed_ir"]["semantic_hash"] = "e" * 64
        r = validate_chain(f)
        self.assertFalse(r["valid"])
        self.assertIn("TYPED_IR_SEMANTIC_DRIFT", self.codes(r))

    def test_missing_contract_hashes_are_rejected(self):
        f = build_fixture()
        del f["stages"]["typed_ir"]["type_effect_contract_hash"]
        del f["stages"]["lowering"]["lowering_contract_hash"]
        r = validate_chain(f)
        self.assertFalse(r["valid"])
        self.assertIn("TYPE_EFFECT_CONTRACT_REQUIRED", self.codes(r))
        self.assertIn("LOWERING_CONTRACT_REQUIRED", self.codes(r))


if __name__ == "__main__":
    unittest.main(verbosity=2)

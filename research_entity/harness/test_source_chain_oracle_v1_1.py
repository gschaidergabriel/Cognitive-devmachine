import unittest
from source_chain_oracle_v1_1 import build_fixture, differential_oracle, validate_chain


class SourceChainOracleV11Tests(unittest.TestCase):
    def codes(self, result):
        return {e["code"] for e in result["errors"]}

    def test_missing_parser_semantics_hash_is_rejected(self):
        f = build_fixture()
        del f["stages"]["parse"]["parser_semantics_hash"]
        r = validate_chain(f)
        self.assertFalse(r["valid"])
        self.assertIn("PARSER_SEMANTICS_IDENTITY_REQUIRED", self.codes(r))

    def test_same_grammar_and_final_state_do_not_hide_parser_semantics_difference(self):
        ref = build_fixture()
        cand = build_fixture()
        cand["stages"]["parse"]["parser_semantics_hash"] = "a" * 64
        r = differential_oracle(ref, cand)
        self.assertFalse(r["equivalent"])
        self.assertTrue(any(m.get("stage") == "parse" and m.get("field") == "parser_semantics_hash" for m in r["mismatches"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

import collections
import unittest
from tools import trigger1_cross_task_abstract_control_gate_v6 as g


def rows(cyclic=False):
    out=[]
    si={s:i for i,s in enumerate(g.STATES)}
    ci={c:i for i,c in enumerate(g.CODES)}
    for fam in ("F0","F1","F2"):
        for state in g.STATES:
            for code in g.CODES:
                for pol in g.POLARITIES:
                    for rep in range(2):
                        bucket=(si[state]+ci[code])%3 if cyclic else rep
                        pt=100+bucket
                        out.append({
                            "family_id":fam,
                            "task_grammar_id":"G-"+fam,
                            "vector_state_id":state,
                            "requested_code":code,
                            "probe_polarity":pol,
                            "replicate_id":f"r{rep}",
                            "control":"TARGET",
                            "proof_topology_id":f"top-{bucket}",
                            "prompt_tokens":pt,
                            "probe_tokens":10,
                            "last_token_index":pt-1,
                        })
    return out


class ConditionalStructureGateV6Test(unittest.TestCase):
    def test_exact_conditional_match_passes(self):
        failures=[]
        audit=g._conditional(rows(False),failures,"X",{"F0","F1","F2"},True)
        self.assertEqual(failures,[])
        self.assertTrue(audit["exact_target_match_given_family_code_polarity"])

    def test_equal_target_marginals_can_hide_code_conditioned_leak(self):
        rs=rows(True)
        marg={s:collections.Counter() for s in g.STATES}
        for r in rs:
            marg[r["vector_state_id"]][g._sig(r)] += 1
        self.assertEqual(marg[g.STATES[0]],marg[g.STATES[1]])
        self.assertEqual(marg[g.STATES[0]],marg[g.STATES[2]])

        failures=[]
        audit=g._conditional(rs,failures,"X",{"F0","F1","F2"},True)
        self.assertFalse(audit["exact_target_match_given_family_code_polarity"])
        self.assertTrue(any("TARGET_LEAK_GIVEN_CODE_POLARITY" in f for f in failures))

    def test_bad_last_token_index_fails(self):
        rs=rows(False)
        rs[0]["last_token_index"] += 1
        failures=[]
        g._conditional(rs,failures,"X",{"F0","F1","F2"},True)
        self.assertTrue(any("STRUCTURE_FIELDS_INVALID" in f for f in failures))

    def test_missing_basis_rows_fail_closed(self):
        failures=[]
        out=g._conditional(None,failures,"CAL",{"B0","B1","B2"},False)
        self.assertEqual(out,{})
        self.assertIn("CAL_ROWS_REQUIRED",failures)

    def test_malformed_adjudication_never_mints_credit(self):
        out=g.adjudicate({"schema":g.ATTESTATION_SCHEMA})
        self.assertFalse(out["cross_task_abstract_native_control_pass"])
        self.assertFalse(out["canonical_credit_minted"])
        self.assertFalse(out["canonical_semantics_promotion"])
        self.assertFalse(out["jspace_model_runtime_credit"])
        self.assertFalse(out["whole_hcu_credit"])
        self.assertFalse(out["whole_entityos_hcu_credit"])
        self.assertFalse(out["training_credit"])


if __name__=="__main__":
    unittest.main()

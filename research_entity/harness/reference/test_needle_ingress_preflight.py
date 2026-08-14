import unittest
from needle_ingress_preflight import *

TOOLS=[{"name":"calc","description":"calculate","parameters":{}}]

class PreflightTests(unittest.TestCase):
    def test_clear_fits(self):
        r=preflight_needle_ingress("Berechne 2+2",TOOLS,context_resolved=True,query_token_count=8,tools_token_count=100)
        self.assertTrue(r.needle_eligible); self.assertFalse(r.fallback_required)
    def test_context_unresolved_falls_back(self):
        r=preflight_needle_ingress("mach das nochmal",TOOLS,context_resolved=False,query_token_count=5,tools_token_count=100)
        self.assertFalse(r.needle_eligible); self.assertIn("CONTEXT_NOT_RESOLVED",r.rejection_reasons)
    def test_empty_intent_falls_back(self):
        r=preflight_needle_ingress(" ",TOOLS,context_resolved=True,query_token_count=0,tools_token_count=100)
        self.assertFalse(r.needle_eligible)
    def test_no_tools_falls_back(self):
        r=preflight_needle_ingress("x",[],context_resolved=True,query_token_count=1,tools_token_count=0)
        self.assertFalse(r.needle_eligible)
    def test_budget_overflow_falls_back(self):
        r=preflight_needle_ingress("x",TOOLS,context_resolved=True,query_token_count=50,tools_token_count=800,min_headroom=200)
        self.assertFalse(r.needle_eligible); self.assertTrue(any(x.startswith("ENCODER_BUDGET:") for x in r.rejection_reasons))
    def test_historical_793_leaves_only_30_query_tokens_at_200_headroom(self):
        self.assertTrue(preflight_needle_ingress("x",TOOLS,context_resolved=True,query_token_count=30,tools_token_count=793).needle_eligible)
        self.assertFalse(preflight_needle_ingress("x",TOOLS,context_resolved=True,query_token_count=31,tools_token_count=793).needle_eligible)
    def test_retrieval_failure_never_failopens_to_all(self):
        r=preflight_needle_ingress("x",TOOLS,context_resolved=True,query_token_count=1,tools_token_count=100,retrieval_mode="CACTUS_RAG",retrieval_succeeded=False)
        self.assertFalse(r.needle_eligible); self.assertIn("RETRIEVAL_FAILED",r.rejection_reasons)
    def test_hashes_deterministic(self):
        a=preflight_needle_ingress("x",TOOLS,context_resolved=True,query_token_count=1,tools_token_count=100)
        b=preflight_needle_ingress("x",TOOLS,context_resolved=True,query_token_count=1,tools_token_count=100)
        self.assertEqual(a.normalized_intent_sha256,b.normalized_intent_sha256); self.assertEqual(a.toolset_sha256,b.toolset_sha256)

if __name__=='__main__': unittest.main(verbosity=2)

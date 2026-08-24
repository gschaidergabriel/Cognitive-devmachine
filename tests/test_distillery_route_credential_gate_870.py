from __future__ import annotations

import unittest
from unittest import mock

import tools.run_research_distillery_entry as entry


class DistilleryRouteCredentialGate870Tests(unittest.TestCase):
    def test_llm_secret_is_default_denied_outside_route_bound_chat(self):
        with mock.patch.object(entry,"_ORIGINAL_SECRET",side_effect=AssertionError("secret lookup reached")):
            self.assertEqual(entry.admitted_secret("OPENROUTER_API_KEY"),"")
            self.assertEqual(entry.admitted_secret("MISTRAL_API_KEY"),"")

    def test_unbound_route_blocks_before_secret_and_network(self):
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"route_secret_lookup_binding",return_value={"ok":False,"reason":"ROUTE_BLOCKED"}), \
             mock.patch.object(entry,"_ORIGINAL_SECRET",side_effect=AssertionError("secret lookup reached")), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            ok,_,_,reason=entry.route_bound_chat("openrouter","paid/model","prompt")
        self.assertFalse(ok)
        self.assertEqual(reason,"FREE_ROUTE_SECRET_LOOKUP_BLOCKED:ROUTE_BLOCKED")

    def test_stale_credential_binding_blocks_before_network(self):
        binding={
            "ok":True,"admission_epoch":"8.70","admission_digest":"a",
            "economic_provenance_digest":"b","observed_at":"now","evidence":{"ok":True},
        }
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"route_secret_lookup_binding",return_value={"ok":True}), \
             mock.patch.object(entry,"_ORIGINAL_SECRET",return_value="free-key"), \
             mock.patch.object(entry,"current_lane_binding",return_value=binding), \
             mock.patch.object(entry,"binding_still_current",return_value=False), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            ok,_,_,reason=entry.route_bound_chat("openrouter","openrouter/free","prompt")
        self.assertFalse(ok)
        self.assertEqual(reason,"FREE_LANE_BINDING_STALE_BEFORE_NETWORK")

    def test_allowed_call_emits_free_lane_receipt(self):
        binding={
            "ok":True,"admission_epoch":"8.70","admission_digest":"a",
            "economic_provenance_digest":"b","observed_at":"now","evidence":{"ok":True},
        }
        body={
            "id":"req-1",
            "choices":[{"message":{"content":"accepted"}}],
            "usage":{"prompt_tokens":7,"completion_tokens":3},
        }
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"route_secret_lookup_binding",return_value={"ok":True}), \
             mock.patch.object(entry,"_ORIGINAL_SECRET",return_value="free-key"), \
             mock.patch.object(entry,"current_lane_binding",return_value=binding), \
             mock.patch.object(entry,"binding_still_current",side_effect=[True,True]), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",return_value=(200,{"x-request-id":"req-1"},body)) as network, \
             mock.patch.object(entry,"emit_execution_receipt") as receipt, \
             mock.patch.object(entry,"_source_identity",return_value={"commit":"c","tree":"t"}):
            ok,text,usage,reason=entry.route_bound_chat("openrouter","openrouter/free","prompt")
        self.assertTrue(ok)
        self.assertEqual(text,"accepted")
        self.assertEqual(reason,"OK")
        self.assertEqual(usage["completion_tokens"],3)
        network.assert_called_once()
        receipt.assert_called_once()
        kwargs=receipt.call_args.kwargs
        self.assertEqual(kwargs["model_or_route"],"openrouter/free")
        self.assertEqual(kwargs["request_id"],"req-1")
        self.assertTrue(kwargs["binding_stable_after_call"])
        self.assertEqual(kwargs["source_commit_and_tree"],{"commit":"c","tree":"t"})

    def test_generic_llm_request_path_is_fail_closed_and_public_github_stays_credential_blind(self):
        with mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            status,_,body=entry.admitted_request_json(
                "openrouter","test","https://openrouter.ai/api/v1/chat/completions",
                key="fake",payload={"model":"openrouter/free"},
            )
            self.assertEqual(status,412)
            self.assertEqual(body["error"],"LLM_PROVIDER_CALL_REQUIRES_ROUTE_BOUND_CHAT")
        expected=(200,{}, {"ok":True})
        with mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",return_value=expected) as downstream:
            observed=entry.admitted_request_json(
                "github","test","https://api.github.com/repos/example/example"
            )
        self.assertEqual(observed,expected)
        downstream.assert_called_once()

    def test_catalog_is_static_explicit_free_route_without_secret_or_network(self):
        with mock.patch.object(entry,"_ORIGINAL_SECRET",side_effect=AssertionError("secret lookup reached")), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            catalog=entry.openrouter_catalog()
        self.assertEqual([x["id"] for x in catalog],["openrouter/free"])


if __name__=="__main__":
    unittest.main()

from __future__ import annotations

import unittest
from unittest import mock

import tools.run_research_distillery_entry as entry


class DistilleryRouteCredentialGate872Tests(unittest.TestCase):
    def test_llm_secret_is_default_denied_outside_route_bound_chat(self):
        with mock.patch.object(entry,"_ORIGINAL_SECRET",side_effect=AssertionError("secret lookup reached")):
            self.assertEqual(entry.admitted_secret("OPENROUTER_API_KEY"),"")
            self.assertEqual(entry.admitted_secret("NVIDIA_API_KEY"),"")
            self.assertEqual(entry.admitted_secret("MISTRAL_API_KEY"),"")

    def test_selected_provider_only_materializes_selected_secret_family(self):
        seen=[]
        def original_secret(name):
            seen.append(name)
            return "selected-key" if name=="OPENROUTER_API_KEY" else ""
        blocked={"ok":False,"reason":"OPENROUTER_ROUTE_NOT_EXPLICIT_ZERO_PRICE"}
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"_ORIGINAL_SECRET",side_effect=original_secret), \
             mock.patch.object(entry,"current_lane_binding",return_value=blocked), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            ok,_,_,reason=entry.route_bound_chat("openrouter","paid/model","prompt")
        self.assertFalse(ok)
        self.assertEqual(reason,"FREE_LANE_BINDING_BLOCKED:OPENROUTER_ROUTE_NOT_EXPLICIT_ZERO_PRICE")
        self.assertEqual(seen,["OPENROUTER_API_KEY"])

    def test_unbound_nvidia_fingerprint_fails_before_model_network(self):
        blocked={"ok":False,"reason":"NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_RECEIPT_NOT_BOUND"}
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"_ORIGINAL_SECRET",return_value="unbound-nvidia-key"), \
             mock.patch.object(entry,"current_lane_binding",return_value=blocked) as binding, \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            ok,_,_,reason=entry.route_bound_chat(
                "nvidia","nvidia/llama-3.3-nemotron-super-49b-v1","prompt"
            )
        self.assertFalse(ok)
        self.assertEqual(reason,"FREE_LANE_BINDING_BLOCKED:NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_RECEIPT_NOT_BOUND")
        self.assertEqual(binding.call_args.args[0],"nvidia")
        self.assertTrue(binding.call_args.args[1])

    def test_stale_binding_fails_before_model_network(self):
        binding={
            "ok":True,"admission_epoch":"8.72","admission_digest":"a",
            "economic_provenance_digest":"b","observed_at":"now","evidence":{"ok":True},
        }
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"_ORIGINAL_SECRET",return_value="free-key"), \
             mock.patch.object(entry,"current_lane_binding",return_value=binding), \
             mock.patch.object(entry,"binding_still_current",return_value=False), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            ok,_,_,reason=entry.route_bound_chat("openrouter","openrouter/free","prompt")
        self.assertFalse(ok)
        self.assertEqual(reason,"FREE_LANE_BINDING_STALE_BEFORE_NETWORK")

    def test_admitted_call_emits_exact_free_lane_receipt(self):
        binding={
            "ok":True,"admission_epoch":"8.72","admission_digest":"a",
            "economic_provenance_digest":"b","observed_at":"now",
            "evidence":{"ok":True,"assertion":"EXACT_ROUTE_ZERO_PROMPT_AND_COMPLETION_PRICE"},
        }
        body={
            "id":"req-1",
            "choices":[{"message":{"content":"accepted"}}],
            "usage":{"prompt_tokens":7,"completion_tokens":3},
        }
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
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
        self.assertEqual(kwargs["http_status"],200)
        self.assertTrue(kwargs["binding_stable_after_call"])
        self.assertEqual(kwargs["source_commit_and_tree"],{"commit":"c","tree":"t"})

    def test_authority_drift_during_call_is_receipted_but_not_consumed(self):
        binding={
            "ok":True,"admission_epoch":"8.72","admission_digest":"a",
            "economic_provenance_digest":"b","observed_at":"now","evidence":{"ok":True},
        }
        body={
            "id":"req-drift",
            "choices":[{"message":{"content":"must-not-propagate"}}],
            "usage":{"prompt_tokens":5,"completion_tokens":2},
        }
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"_ORIGINAL_SECRET",return_value="free-key"), \
             mock.patch.object(entry,"current_lane_binding",return_value=binding), \
             mock.patch.object(entry,"binding_still_current",side_effect=[True,False]), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",return_value=(200,{},body)) as network, \
             mock.patch.object(entry,"emit_execution_receipt") as receipt, \
             mock.patch.object(entry,"_source_identity",return_value={"commit":"c","tree":"t"}):
            ok,text,usage,reason=entry.route_bound_chat("openrouter","openrouter/free","prompt")
        self.assertFalse(ok)
        self.assertEqual(text,"")
        self.assertEqual(usage["completion_tokens"],2)
        self.assertEqual(reason,"FREE_LANE_BINDING_CHANGED_DURING_NETWORK")
        network.assert_called_once()
        self.assertFalse(receipt.call_args.kwargs["binding_stable_after_call"])

    def test_transport_failure_is_receipted_as_unknown_without_retry(self):
        binding={
            "ok":True,"admission_epoch":"8.72","admission_digest":"a",
            "economic_provenance_digest":"b","observed_at":"now","evidence":{"ok":True},
        }
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"_ORIGINAL_SECRET",return_value="free-key"), \
             mock.patch.object(entry,"current_lane_binding",return_value=binding), \
             mock.patch.object(entry,"binding_still_current",side_effect=[True,True]), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",return_value=(0,{}, {"error":"TimeoutError:secret-ish detail"})) as network, \
             mock.patch.object(entry,"emit_execution_receipt") as receipt, \
             mock.patch.object(entry,"_source_identity",return_value={"commit":"c","tree":"t"}):
            ok,_,_,reason=entry.route_bound_chat("openrouter","openrouter/free","prompt")
        self.assertFalse(ok)
        self.assertEqual(reason,"TRANSPORT_EXCEPTION_UNKNOWN_OUTCOME")
        network.assert_called_once()
        kwargs=receipt.call_args.kwargs
        self.assertEqual(kwargs["http_status"],"TRANSPORT_EXCEPTION_UNKNOWN_OUTCOME")
        self.assertNotIn("secret-ish",kwargs["result_digest"])

    def test_generic_llm_path_fails_closed_and_public_github_is_credential_blind(self):
        with mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            status,_,body=entry.admitted_request_json(
                "openrouter","test","https://openrouter.ai/api/v1/chat/completions",
                key="fake",payload={"model":"openrouter/free"},
            )
        self.assertEqual(status,412)
        self.assertEqual(body["error"],"LLM_PROVIDER_CALL_REQUIRES_ROUTE_BOUND_CHAT")

        with mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            status,_,body=entry.admitted_request_json(
                "github","test","https://api.github.com/repos/example/example",
                headers={"Authorization":"Bearer should-not-exist"},
            )
        self.assertEqual(status,412)
        self.assertEqual(body["error"],"PUBLIC_SOURCE_CREDENTIALS_FORBIDDEN")

    def test_catalog_is_static_explicit_free_route_without_secret_or_network(self):
        with mock.patch.object(entry,"_ORIGINAL_SECRET",side_effect=AssertionError("secret lookup reached")), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",side_effect=AssertionError("network reached")):
            catalog=entry.openrouter_catalog()
        self.assertEqual([x["id"] for x in catalog],["openrouter/free"])

    def test_non_mistral_fallback_is_provisional_and_cannot_promote_dataset(self):
        votes=[
            ("nvidia_reviewer","nvidia","nvidia/model",0.95,0.95,0.95,0.95,0),
            ("fallback_free_router_1","openrouter","openrouter/free",0.95,0.95,0.95,0.95,0),
            ("fallback_free_router_2","openrouter","openrouter/free",0.95,0.95,0.95,0.95,0),
        ]
        con=mock.MagicMock()
        con.execute.return_value.fetchall.return_value=votes
        with mock.patch.object(entry,"_ORIGINAL_REVIEW",return_value=(True,{"votes":3})), \
             mock.patch.object(entry.d,"emit") as emit:
            accepted,agg=entry.review_candidate(con,"c-1",[
                ("nvidia_reviewer","nvidia","nvidia/model"),
                ("fallback_free_router_1","openrouter","openrouter/free"),
                ("fallback_free_router_2","openrouter","openrouter/free"),
            ])
        self.assertFalse(accepted)
        self.assertEqual(agg["panel_class"],"PROVISIONAL_NON_MISTRAL_FALLBACK")
        self.assertEqual(agg["independence_class"],"GOODMAN_COLLAPSED_FREE_ROUTER_FALLBACK")
        self.assertFalse(agg["canonical_acceptance"])
        sql_calls=[c.args for c in con.execute.call_args_list if c.args]
        self.assertTrue(any("PROVISIONAL_ACCEPTED" in str(args[0]) for args in sql_calls))
        self.assertFalse(any("SET status='ACCEPTED'" in str(args[0]) for args in sql_calls))
        emit.assert_called_with("knowledge_provisional_accept",candidate="c-1",review=agg)


if __name__=="__main__":
    unittest.main()

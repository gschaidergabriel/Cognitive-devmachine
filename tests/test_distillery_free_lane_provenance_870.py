#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/"tools"
if str(TOOLS) not in sys.path:sys.path.insert(0,str(TOOLS))

import run_research_distillery_entry as entry


class DistilleryFreeLaneProvenance870Tests(unittest.TestCase):
    def test_unbound_inference_route_is_blocked_before_network(self):
        network=mock.Mock(return_value=(200,{},{}))
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"lane_evidence",return_value={"ok":False,"reason":"NO_BOUND_FREE_ENTITLEMENT"}), \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",network):
            status,_,body=entry.admitted_request_json(
                "nvidia","test-owner","https://integrate.api.nvidia.com/v1/chat/completions",
                key="secret-key",payload={"model":"nvidia/example","messages":[]},
            )
        self.assertEqual(status,460)
        self.assertEqual(body["error"],"FREE_LANE_ECONOMIC_PROVENANCE_REQUIRED")
        network.assert_not_called()

    def test_exact_zero_cost_route_executes_and_emits_receipt(self):
        response=(200,{"x-request-id":"req-1"},{"id":"chat-1","usage":{"prompt_tokens":3,"completion_tokens":2}})
        network=mock.Mock(return_value=response)
        receipt=mock.Mock()
        evidence={"ok":True,"assertion":"EXACT_ROUTE_ZERO_PROMPT_AND_COMPLETION_PRICE"}
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"lane_evidence",return_value=evidence) as lane, \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",network), \
             mock.patch.object(entry,"emit_execution_receipt",receipt):
            out=entry.admitted_request_json(
                "openrouter","test-owner","https://openrouter.ai/api/v1/chat/completions",
                key="secret-key",payload={"model":"openrouter/free","messages":[]},
            )
        self.assertEqual(out[0],200)
        network.assert_called_once()
        lane.assert_called_once()
        kwargs=receipt.call_args.kwargs
        self.assertEqual(kwargs["provider"],"openrouter")
        self.assertEqual(kwargs["model_or_route"],"openrouter/free")
        self.assertEqual(kwargs["request_id"],"req-1")
        self.assertEqual(kwargs["http_status"],200)
        self.assertEqual(kwargs["usage"]["completion_tokens"],2)

    def test_openrouter_catalog_metadata_read_is_not_misclassified_as_inference(self):
        network=mock.Mock(return_value=(200,{}, {"data":[]}))
        with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
             mock.patch.object(entry,"lane_evidence") as lane, \
             mock.patch.object(entry,"_ORIGINAL_REQUEST_JSON",network):
            status,_,_=entry.admitted_request_json(
                "openrouter","catalog",entry.OPENROUTER_CATALOG_URL,key="secret-key",payload=None
            )
        self.assertEqual(status,200)
        network.assert_called_once()
        lane.assert_not_called()

    def test_explicit_free_router_remains_available_with_empty_catalog(self):
        with mock.patch.object(entry,"provider_is_admitted_free",side_effect=lambda p:p=="openrouter"):
            self.assertEqual(entry.select_small_models([]),["openrouter/free"])


if __name__=="__main__":
    unittest.main()

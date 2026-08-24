from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import xeno_runtime_v1 as runtime

CAP_BINDING = "b" * 64
PROV_HASH = "c" * 64


def _entry(payload: str = "hello", *, max_calls: int = 2, max_tokens: int = 32, max_wall_ms: int = 10000) -> str:
    obj = {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress-1",
        "causal_id": "causal-1",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "test-user",
        "modality": "TEXT",
        "observed_time": "2026-08-24T13:00:00Z",
        "received_time": "2026-08-24T13:00:01Z",
        "provenance_ref": "test://provenance/1",
        "provenance_sha256": PROV_HASH,
        "capabilities": ["MODEL_INFERENCE"],
        "capability_binding_sha256": CAP_BINDING,
        "parent_id": None,
        "stream_id": None,
        "budget": {
            "max_model_calls": max_calls,
            "max_tokens": max_tokens,
            "max_wall_ms": max_wall_ms,
        },
        "payload_ref": "memory://payload/1",
        "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    }
    return json.dumps(obj, separators=(",", ":"), sort_keys=True)


def _config(*, prestage: bool = False, internal_core: bool = False) -> dict:
    if prestage:
        slots = [
            {
                "slot_id": "slot1",
                "role": "PRESTAGE",
                "adapter": "GROQ",
                "secret_ref": "secret://slot1",
                "model": "prestage-model",
                "enabled": True,
            },
            {
                "slot_id": "slot2",
                "role": "CORE" if not internal_core else "UNASSIGNED",
                "adapter": "OPENAI_COMPATIBLE",
                "secret_ref": "secret://slot2",
                "model": "core-model",
                "enabled": True,
            },
        ]
        core = "internal_08b" if internal_core else "slot2"
    else:
        slots = [
            {
                "slot_id": "slot1",
                "role": "CORE" if not internal_core else "UNASSIGNED",
                "adapter": "OPENAI_COMPATIBLE",
                "secret_ref": "secret://slot1",
                "model": "core-model",
                "enabled": True,
            }
        ]
        core = "internal_08b" if internal_core else "slot1"
    return {
        "schema": "XENO_HARNESS_CONFIG/v1",
        "internal_08b": {"enabled": True, "engine_id": "qwen-local-test"},
        "external_slots": slots,
        "selection": {
            "core": core,
            "prestage": "slot1" if prestage else "NONE",
            "prestage_enabled": prestage,
        },
        "grid10": {"enabled": True, "logical_cells": 10},
        "peer_link": {"enabled": False, "protocol": "XENO_PEER_LINK/v1"},
        "global_jspace": {"enabled": True, "profile_id": "jspace-test"},
    }


def _execute(*, config: dict, raw_entry: str | None = None, runner=None, deterministic=None):
    return runtime.execute_request(
        raw_entry or _entry(),
        harness_config=config,
        current_generation=7,
        expected_capability_binding_sha256=CAP_BINDING,
        admitted_capabilities=["MODEL_INFERENCE"],
        admitted_budget={"max_model_calls": 2, "max_tokens": 32, "max_wall_ms": 10000},
        payload_text="hello",
        engine_runner=runner,
        deterministic_candidate=deterministic,
    )


class XenoRuntimeV1Tests(unittest.TestCase):
    def test_core_only_bypasses_prestage_and_returns_non_authoritative_candidate(self) -> None:
        calls = []

        def runner(profile, request):
            calls.append((dict(profile), dict(request)))
            return {"status": "OK", "text": "core-output", "usage": {"total_tokens": 4}}

        result = _execute(config=_config(), runner=runner)
        self.assertEqual(result["mode"], "CORE_ONLY")
        self.assertEqual(result["model_calls"], 1)
        self.assertIsNone(result["prestage_result"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]["role"], "CORE")
        self.assertFalse(result["canonical_truth"])
        self.assertFalse(result["effect_authority"])
        self.assertTrue(result["requires_effect_gate"])
        self.assertTrue(result["action_candidate"]["requires_effect_gate"])

    def test_prestage_candidate_is_typed_nontruth_context_for_core(self) -> None:
        calls = []

        def runner(profile, request):
            calls.append((dict(profile), dict(request)))
            if request["role"] == "PRESTAGE":
                return {"status": "OK", "text": "prestage-context", "usage": {"total_tokens": 3}}
            return {"status": "OK", "text": "core-output", "usage": {"total_tokens": 5}}

        result = _execute(config=_config(prestage=True), runner=runner)
        self.assertEqual(result["mode"], "CORE_PLUS_PRESTAGE")
        self.assertEqual(result["model_calls"], 2)
        self.assertEqual([call[1]["role"] for call in calls], ["PRESTAGE", "CORE"])
        core_request = calls[1][1]
        self.assertEqual(core_request["prestage_candidate"]["text"], "prestage-context")
        self.assertFalse(core_request["prestage_candidate"]["canonical_truth"])
        self.assertEqual(
            core_request["prestage_candidate"]["result_sha256"],
            result["prestage_result"]["result_sha256"],
        )
        self.assertEqual(
            [step["stage"] for step in result["trace"]["steps"]],
            ["ENTRY_ADMITTED", "PRESTAGE_RESULT", "CORE_RESULT", "ACTION_CANDIDATE"],
        )

    def test_external_secret_ref_reaches_adapter_profile_but_not_model_request_or_result(self) -> None:
        seen_profile = None
        seen_request = None

        def runner(profile, request):
            nonlocal seen_profile, seen_request
            seen_profile = dict(profile)
            seen_request = dict(request)
            return {"status": "OK", "text": "ok", "usage": {"total_tokens": 1}}

        result = _execute(config=_config(), runner=runner)
        self.assertEqual(seen_profile["secret_ref"], "secret://slot1")
        self.assertNotIn("secret_ref", json.dumps(seen_request, sort_keys=True))
        self.assertNotIn("secret://slot1", json.dumps(result, sort_keys=True))

    def test_payload_digest_mismatch_fails_before_engine_call(self) -> None:
        calls = []

        def runner(profile, request):
            calls.append(1)
            return {"status": "OK", "text": "unexpected", "usage": {"total_tokens": 1}}

        with self.assertRaisesRegex(runtime.XenoRuntimeError, "PAYLOAD_BYTES_DO_NOT_MATCH_ADMITTED_DIGEST"):
            _execute(config=_config(), raw_entry=_entry(payload="different"), runner=runner)
        self.assertEqual(calls, [])

    def test_model_call_budget_fails_before_engine_call(self) -> None:
        raw = _entry(max_calls=1)
        calls = []

        def runner(profile, request):
            calls.append(1)
            return {"status": "OK", "text": "unexpected", "usage": {"total_tokens": 1}}

        with self.assertRaisesRegex(runtime.XenoRuntimeError, "MODEL_CALL_BUDGET_INSUFFICIENT"):
            _execute(config=_config(prestage=True), raw_entry=raw, runner=runner)
        self.assertEqual(calls, [])

    def test_token_budget_overrun_is_rejected(self) -> None:
        raw = _entry(max_tokens=4)

        def runner(profile, request):
            return {"status": "OK", "text": request["role"], "usage": {"total_tokens": 3}}

        with self.assertRaisesRegex(runtime.XenoRuntimeError, "MODEL_TOKEN_BUDGET_EXCEEDED"):
            _execute(config=_config(prestage=True), raw_entry=raw, runner=runner)

    def test_deterministic_no_model_mode_never_calls_engine(self) -> None:
        result = _execute(
            config=_config(),
            runner=None,
            deterministic={"decision": "NO_MODEL_REQUIRED", "value": 7},
        )
        self.assertEqual(result["mode"], "DETERMINISTIC_NO_MODEL")
        self.assertEqual(result["model_calls"], 0)
        self.assertIsNone(result["core_result"])
        self.assertEqual(result["action_candidate"]["kind"], "DETERMINISTIC_CONTROL_OUTPUT")
        self.assertTrue(result["action_candidate"]["requires_effect_gate"])

    def test_plaintext_secret_field_in_harness_is_rejected(self) -> None:
        config = _config()
        config["api_key"] = "should-never-enter-state"
        with self.assertRaisesRegex(runtime.XenoRuntimeError, "HARNESS_CONFIG_REJECTED"):
            _execute(config=config, runner=lambda profile, request: {})

    def test_runner_cannot_smuggle_secret_field_into_public_result(self) -> None:
        def runner(profile, request):
            return {
                "status": "OK",
                "text": "bad",
                "usage": {"total_tokens": 1},
                "secret_ref": "secret://should-not-return",
            }

        with self.assertRaisesRegex(runtime.XenoRuntimeError, "SECRET_FIELD_FORBIDDEN"):
            _execute(config=_config(), runner=runner)


if __name__ == "__main__":
    unittest.main()

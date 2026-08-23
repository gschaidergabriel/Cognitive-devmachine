#!/usr/bin/env python3
"""Focused bounded regressions for reference-runtime Cognitive Fabric wiring.

These tests intentionally dependency-stub only the Clay executor and the two already-
canonical helper modules. They exercise the exact reference-runtime integration seams;
they do not claim bundled-model, J-Space/GWT, provider or whole Mini Entity execution.
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"


class _ClayRuntime:
    def __init__(self):
        self.builtins = {}


class _StructuredFault(RuntimeError):
    pass


clay_stub = types.ModuleType("claycode_structured_backend")
clay_stub.Runtime = _ClayRuntime
clay_stub.StructuredFault = _StructuredFault
clay_stub.parse = lambda source: source
clay_stub.execute = lambda program, entry, args, runtime: None
sys.modules["claycode_structured_backend"] = clay_stub

bootstrap_stub = types.ModuleType("miniunifieddb_cognition_bootstrap_v1")
bootstrap_events: list[str] = []


def _prepare_connection(db: sqlite3.Connection):
    if db.in_transaction:
        raise AssertionError("prepare must precede transaction")
    db.execute("PRAGMA foreign_keys=ON")
    if int(db.execute("PRAGMA foreign_keys").fetchone()[0]) != 1:
        raise AssertionError("foreign keys not enabled")
    bootstrap_events.append("prepare")
    return {"ok": True}


def _install_cognition_schema(db: sqlite3.Connection):
    if not db.in_transaction:
        raise AssertionError("install must run inside caller transaction")
    if db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone() is None:
        raise AssertionError("entity_state must exist before cognition install")
    db.execute("CREATE TABLE IF NOT EXISTS mini_cognition_probe(id INTEGER PRIMARY KEY)")
    bootstrap_events.append("install")
    return {"ok": True}


bootstrap_stub.prepare_connection = _prepare_connection
bootstrap_stub.install_cognition_schema = _install_cognition_schema
sys.modules["miniunifieddb_cognition_bootstrap_v1"] = bootstrap_stub

admission_stub = types.ModuleType("pipeline_cognitive_fabric_admission_v1")
admission_calls: list[dict] = []


def _build_pre_inference_admission(db, **kwargs):
    query_only = int(db.execute("PRAGMA query_only").fetchone()[0])
    admission_calls.append({"query_only": query_only, **kwargs})
    return {"ok": True, "probe": "admitted"}


admission_stub.build_pre_inference_admission = _build_pre_inference_admission
sys.modules["pipeline_cognitive_fabric_admission_v1"] = admission_stub

spec = importlib.util.spec_from_file_location("clay_profile_pipeline_runtime_under_test", RUNTIME_PATH)
assert spec is not None and spec.loader is not None
runtime_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime_module)

DIGEST_A = "1" * 64
DIGEST_B = "2" * 64
CANONICAL_HASH = "3" * 64
PACKET_HASH = "4" * 64


def _profile():
    return {
        "personality": {
            "output_contract": {
                "title_field": "title",
                "intro_field": "intro",
                "sections_field": "sections",
                "continuity_field": "continuity",
                "autobiographical_hypotheses_field": "hypotheses",
                "section_evidence_field": "evidence_refs",
                "section_claims_field": "state_claims",
            }
        },
        "gate": {"require_hash_echo": False, "require_evidence_per_section": False},
    }


def _admission():
    return {
        "ok": True,
        "inference_packet_digest": DIGEST_A,
        "cognitive_fabric_receipt_digest": DIGEST_B,
        "canonical_state_hash": CANONICAL_HASH,
        "packet_hash": PACKET_HASH,
    }


def _compiled():
    return {
        "canonical_state_hash": CANONICAL_HASH,
        "packet_hash": PACKET_HASH,
        "allowed_evidence_refs": [],
        "canonical": {"personality_state": {}},
    }


class RuntimeCognitiveFabricWiringTests(unittest.TestCase):
    def setUp(self):
        bootstrap_events.clear()
        admission_calls.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = runtime_module.ProfilePipelineRuntime(root=self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_bootstrap_installs_cognition_inside_same_transaction(self):
        result = self.runtime._pipeline_init({"entity_db": "entity.sqlite"})
        self.assertTrue(result["ok"], result)
        self.assertEqual(bootstrap_events, ["prepare", "install"])
        with sqlite3.connect(Path(self.temp.name) / "entity.sqlite") as db:
            self.assertIsNotNone(
                db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='mini_cognition_probe'"
                ).fetchone()
            )

    def test_admission_uses_read_only_same_store_and_exact_generation(self):
        self.assertTrue(self.runtime._pipeline_init({"entity_db": "entity.sqlite"})["ok"])
        result = self.runtime._pipeline_cognitive_fabric_admit(
            {
                "entity_db": "entity.sqlite",
                "profile": {"profile_id": "p"},
                "previous": {"generation": 0},
                "data": {
                    "invocation": {"selector": "bounded"},
                    "compiled": {"canonical_state_hash": CANONICAL_HASH},
                    "prompt": {"system": "s", "user": "u"},
                },
            }
        )
        self.assertEqual(result, {"ok": True, "probe": "admitted"})
        self.assertEqual(len(admission_calls), 1)
        self.assertEqual(admission_calls[0]["query_only"], 1)
        self.assertEqual(admission_calls[0]["entity_generation"], 0)
        self.assertEqual(
            admission_calls[0]["origin"],
            "ProfilePipelineRuntime.pipeline_cognitive_fabric_admit",
        )

    def test_inference_preserves_exact_admission_identities(self):
        self.runtime.provider_override = lambda request: {"candidate": True}
        result = self.runtime._inference_generate(
            {
                "inference": {"kind": "mock", "model": "bounded"},
                "system": "s",
                "user": "u",
                "inference_packet_digest": DIGEST_A,
                "cognitive_fabric_admission_receipt_digest": DIGEST_B,
            }
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["inference_packet_digest"], DIGEST_A)
        self.assertEqual(result["cognitive_fabric_admission_receipt_digest"], DIGEST_B)

    def test_unusual_post_inference_admission_receipt_swap_fails_closed(self):
        """Single unusual GO experiment: mutate only post-inference admission identity."""
        generated = {
            "ok": True,
            "payload": {},
            "inference_packet_digest": DIGEST_A,
            "cognitive_fabric_admission_receipt_digest": "5" * 64,
        }
        result = self.runtime._pipeline_gate(
            {
                "profile": _profile(),
                "data": {
                    "generated": generated,
                    "compiled": _compiled(),
                    "cognitive_fabric_admission": _admission(),
                },
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn("COGNITIVE_FABRIC_ADMISSION_RECEIPT_MISMATCH", result["error"])

    def test_finalizer_preserves_evidence_debt_instead_of_minting_partial_ucf_receipt(self):
        generated = {
            "ok": True,
            "payload": {"candidate": True},
            "inference_packet_digest": DIGEST_A,
            "cognitive_fabric_admission_receipt_digest": DIGEST_B,
        }
        result = self.runtime._pipeline_cognitive_fabric_finalize(
            {
                "data": {
                    "admitted": _admission(),
                    "generated": generated,
                    "gated": {"ok": True, "payload": {"candidate": True}},
                    "committed": {"ok": True, "output_id": "out-1", "generation": 1},
                    "compiled": _compiled(),
                    "prompt": {"system": "s", "user": "u"},
                }
            }
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "UCF_RUNTIME_RECEIPT_EVIDENCE_INCOMPLETE")
        self.assertIn("terminal_ancestry_digest", result)
        self.assertNotIn("ucf_runtime_receipt_digest", result)


if __name__ == "__main__":
    unittest.main()

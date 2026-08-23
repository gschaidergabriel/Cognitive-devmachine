import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_runtime():
    spec = importlib.util.spec_from_file_location(
        "clay_profile_pipeline_runtime_ucf_test",
        ROOT / "tools" / "clay_profile_pipeline_runtime.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runtime_module = load_runtime()
D = "a" * 64
E = "b" * 64
F = "c" * 64
G = "d" * 64


class RuntimeUCFIntegrationTests(unittest.TestCase):
    def test_pipeline_init_installs_cognition_tables_in_same_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt = runtime_module.ProfilePipelineRuntime(root=tmp)
            result = rt._pipeline_init({"entity_db": "entity.db"})
            self.assertTrue(result["ok"], result)
            db = sqlite3.connect(Path(tmp) / "entity.db")
            try:
                names = {
                    row[0]
                    for row in db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mini_cognition_%'"
                    ).fetchall()
                }
            finally:
                db.close()
            self.assertTrue(
                {
                    "mini_cognition_objects",
                    "mini_cognition_object_admissions",
                    "mini_cognition_boot_bindings",
                    "mini_cognition_turn_bindings",
                    "mini_cognition_active_turns",
                }.issubset(names)
            )

    def test_inference_echoes_exact_admission_identity_not_model_payload(self):
        seen = {}

        def provider(request):
            seen.update(request)
            return {"candidate": "ok"}

        rt = runtime_module.ProfilePipelineRuntime(provider_override=provider)
        result = rt._inference_generate(
            {
                "inference": {"kind": "mock", "model": "mock"},
                "system": "system",
                "user": "user",
                "inference_packet_digest": D,
                "cognitive_fabric_admission_receipt_digest": E,
            }
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["inference_packet_digest"], D)
        self.assertEqual(result["cognitive_fabric_admission_receipt_digest"], E)
        self.assertEqual(seen["inference_packet_digest"], D)
        self.assertEqual(seen["cognitive_fabric_admission_receipt_digest"], E)

    def test_bad_packet_digest_blocks_before_provider_execution(self):
        calls = []
        rt = runtime_module.ProfilePipelineRuntime(
            provider_override=lambda request: calls.append(request) or {"candidate": "bad"}
        )
        result = rt._inference_generate(
            {
                "inference": {"kind": "mock"},
                "system": "system",
                "user": "user",
                "inference_packet_digest": "0" * 64,
                "cognitive_fabric_admission_receipt_digest": E,
            }
        )
        self.assertFalse(result["ok"])
        self.assertEqual(calls, [])

    def test_gate_commit_chain_rejects_admission_identity_drift(self):
        admitted = {
            "ok": True,
            "schema": "mini-entity-cognitive-fabric-admission/v1",
            "generation": 4,
            "canonical_state_hash": F,
            "packet_hash": G,
            "inference_packet_digest": D,
            "cognitive_fabric_receipt_digest": E,
        }
        generated = {
            "ok": True,
            "inference_packet_digest": D,
            "cognitive_fabric_admission_receipt_digest": E,
        }
        runtime_module.ProfilePipelineRuntime._verify_admission_chain(
            admitted=admitted,
            generated=generated,
            compiled={"canonical_state_hash": F, "packet_hash": G},
            previous={"generation": 4},
        )
        generated["cognitive_fabric_admission_receipt_digest"] = D
        with self.assertRaisesRegex(
            runtime_module.PipelineFault,
            "COGNITIVE_FABRIC_ADMISSION_IDENTITY_DRIFT",
        ):
            runtime_module.ProfilePipelineRuntime._verify_admission_chain(
                admitted=admitted,
                generated=generated,
                compiled={"canonical_state_hash": F, "packet_hash": G},
                previous={"generation": 4},
            )

    def test_finalizer_does_not_fabricate_missing_runtime_evidence(self):
        rt = runtime_module.ProfilePipelineRuntime()
        result = rt._pipeline_cognitive_fabric_finalize(
            {
                "data": {
                    "admitted": {
                        "ok": True,
                        "schema": "mini-entity-cognitive-fabric-admission/v1",
                        "generation": 1,
                        "canonical_state_hash": F,
                        "packet_hash": G,
                        "inference_packet_digest": D,
                        "cognitive_fabric_receipt_digest": E,
                    },
                    "generated": {
                        "ok": True,
                        "payload": {"candidate": "x"},
                        "inference_packet_digest": D,
                        "cognitive_fabric_admission_receipt_digest": E,
                    },
                    "gated": {"ok": True, "payload": {"candidate": "x"}},
                    "committed": {"ok": True, "output_id": "out", "generation": 2},
                    "compiled": {"canonical_state_hash": F, "packet_hash": G},
                    "prompt": {"system": "s", "user": "u"},
                }
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn("ucf_runtime_evidence", result["error"])


if __name__ == "__main__":
    unittest.main()

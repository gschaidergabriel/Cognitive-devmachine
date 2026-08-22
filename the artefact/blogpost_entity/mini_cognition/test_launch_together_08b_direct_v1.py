#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD_PATH = HERE / "launch_together_08b_direct_v1.py"
spec = importlib.util.spec_from_file_location("launch08", MOD_PATH)
launch08 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch08)


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FakeFT:
    def __init__(self, full=True):
        self.full = full
        self.estimated = None

    def get_model_limits(self, model):
        self.model_limits_model = model
        return Obj(full_training=Obj()) if self.full else Obj(full_training=None)

    def estimate_price(self, **kw):
        self.estimated = kw
        return Obj(estimated_total_price=4.0, allowed_to_proceed=True)


class FakeClient:
    def __init__(self, full=True):
        self.fine_tuning = FakeFT(full=full)


class Direct08Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        launch08.TRAIN = root / "train_v2.jsonl"
        launch08.VALID = root / "validation_v2.jsonl"
        launch08.TRAIN.write_text('{"messages":[]}\n', encoding="utf-8")
        launch08.VALID.write_text('{"messages":[]}\n', encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_direct_model_identity_has_no_byom_fields(self):
        d = launch08.campaign_descriptor()
        self.assertEqual(d["model"], "Qwen/Qwen3.5-0.8B")
        raw = json.dumps(d, sort_keys=True)
        self.assertNotIn("from_hf_model", raw)
        self.assertNotIn("hf_model_revision", raw)
        self.assertNotIn("template_model", raw)
        self.assertEqual(d["training_type"], {"type": "Full"})

    def test_current_model_limits_must_admit_full_ft(self):
        ok = FakeClient(full=True)
        launch08.get_full_training_limits(ok)
        self.assertEqual(ok.fine_tuning.model_limits_model, "Qwen/Qwen3.5-0.8B")
        with self.assertRaises(SystemExit):
            launch08.get_full_training_limits(FakeClient(full=False))

    def test_price_request_is_direct_full_sft(self):
        c = FakeClient(full=True)
        out = launch08.estimate_price(c, "file-train", "file-valid")
        self.assertTrue(out.allowed_to_proceed)
        q = c.fine_tuning.estimated
        self.assertEqual(q["model"], "Qwen/Qwen3.5-0.8B")
        self.assertEqual(q["training_method"], {"method": "sft", "train_on_inputs": "auto"})
        self.assertEqual(q["training_type"], {"type": "Full"})
        self.assertNotIn("from_hf_model", q)

    def test_create_payload_is_single_model_identity_and_seed_bound(self):
        p = launch08.create_payload("t", "v", "suffix")
        self.assertEqual(p["model"], "Qwen/Qwen3.5-0.8B")
        self.assertEqual(p["random_seed"], 3407)
        self.assertNotIn("from_hf_model", p)
        self.assertNotIn("hf_model_revision", p)
        self.assertNotIn("lora", p)
        self.assertEqual(p["training_type"], {"type": "Full"})

    def test_fingerprint_binds_dataset_bytes(self):
        a = launch08.campaign_fingerprint()
        launch08.TRAIN.write_text('{"messages":[1]}\n', encoding="utf-8")
        b = launch08.campaign_fingerprint()
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()

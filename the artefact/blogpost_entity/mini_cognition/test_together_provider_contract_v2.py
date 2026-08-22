#!/usr/bin/env python3
"""No-network regression tests for Together catalog + SDK-v2 admission.

Regression-only: the macro-cycle's unusual experiment is not consumed here.
"""
import importlib.util, types, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("launch_together_v1",HERE/"launch_together_v1.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class FineTuningV2Fake:
    def __init__(self,full_training=True,price=4.0,allowed=True):
        self.full_training=full_training; self.price=price; self.allowed=allowed
        self.limit_calls=[]; self.estimate_calls=[]; self.create_calls=[]; self.jobs=[]
    def get_model_limits(self,*,model):
        self.limit_calls.append(model)
        return types.SimpleNamespace(full_training=types.SimpleNamespace(max_batch_size=16) if self.full_training else None)
    def estimate_price(self,**kwargs):
        self.estimate_calls.append(dict(kwargs))
        if not isinstance(kwargs.get("training_type"),str): raise AssertionError("training_type must be string")
        if not isinstance(kwargs.get("training_method"),str): raise AssertionError("training_method must be string")
        return types.SimpleNamespace(estimated_total_price=self.price,allowed_to_proceed=self.allowed)
    def list(self): return types.SimpleNamespace(data=list(self.jobs))
    def create(self,**kwargs): self.create_calls.append(dict(kwargs)); return types.SimpleNamespace(id="ft-fake")

class FilesV2Fake:
    def __init__(self,processed=True): self.processed=processed; self.calls=[]
    def retrieve(self,file_id): self.calls.append(file_id); return types.SimpleNamespace(id=file_id,processed=self.processed)

class ClientV2Fake:
    def __init__(self,**kwargs): self.fine_tuning=FineTuningV2Fake(**kwargs); self.files=FilesV2Fake()

class ProviderContractTests(unittest.TestCase):
    def test_no_template_is_guessed(self):
        with self.assertRaises(SystemExit) as ctx: mod.require_explicit_template(None)
        self.assertIn("NO_COMPATIBLE_TOGETHER_TEMPLATE_CONFIGURED",str(ctx.exception))
    def test_explicit_template_passes_local_gate_only(self):
        t="provider/future-qwen2-compatible-base"; self.assertEqual(t,mod.require_explicit_template(t))
    def test_sdk_v2_limits_and_full_training_field(self):
        c=ClientV2Fake(full_training=True); t="provider/future-qwen2-compatible-base"; limits=mod.get_full_training_limits(c,t)
        self.assertIsNotNone(limits.full_training); self.assertEqual([t],c.fine_tuning.limit_calls); self.assertFalse(hasattr(c.fine_tuning,"model_limits"))
    def test_missing_full_training_fails_closed(self):
        with self.assertRaises(SystemExit): mod.get_full_training_limits(ClientV2Fake(full_training=False),"provider/not-full-ft")
    def test_missing_sdk_v2_method_fails_closed(self):
        c=types.SimpleNamespace(fine_tuning=types.SimpleNamespace())
        with self.assertRaises(SystemExit) as ctx: mod.get_full_training_limits(c,"provider/template")
        self.assertIn("TOGETHER_SDK_V2_REQUIRED",str(ctx.exception))
    def test_current_processed_boolean_completes_wait(self):
        c=ClientV2Fake(); meta=mod.wait_file(c,"file-v2",timeout_seconds=1); self.assertTrue(meta.processed); self.assertEqual(["file-v2"],c.files.calls)
    def test_price_uses_current_string_contract(self):
        c=ClientV2Fake(price=4.0); t="provider/future-qwen2-compatible-base"; estimate=mod.estimate_full_sft_price(c,"train","valid",t)
        self.assertEqual(4.0,float(estimate.estimated_total_price)); [call]=c.fine_tuning.estimate_calls
        self.assertEqual("sft",call["training_method"]); self.assertEqual("full",call["training_type"]); self.assertEqual(t,call["model"])
    def test_preflight_helpers_never_call_billed_create(self):
        c=ClientV2Fake(); t="provider/future-qwen2-compatible-base"; mod.require_explicit_template(t); mod.get_full_training_limits(c,t); mod.wait_file(c,"file-v2",timeout_seconds=1); mod.estimate_full_sft_price(c,"train","valid",t)
        self.assertEqual([],c.fine_tuning.create_calls)
    def test_exact_hf_revision_binding_is_preserved(self):
        model,rev=mod.resolve_hf_source(False); self.assertEqual(mod.PRIMARY_HF_MODEL,model); self.assertEqual(mod.PRIMARY_HF_REVISION,rev)
        self.assertEqual(rev,mod.campaign_descriptor(model,rev)["hf_model_revision"])

if __name__=="__main__": unittest.main(verbosity=2)

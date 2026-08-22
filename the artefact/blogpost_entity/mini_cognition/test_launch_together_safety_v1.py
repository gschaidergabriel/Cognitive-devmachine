#!/usr/bin/env python3
import importlib.util, os, tempfile, types, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("launch_together_v1", HERE/"launch_together_v1.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class FineTuningFake:
    def __init__(self): self.jobs=[]
    def list(self): return types.SimpleNamespace(data=list(self.jobs))

class ClientFake:
    def __init__(self): self.fine_tuning=FineTuningFake()

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); p=Path(self.tmp.name)
        self.old_paths=(mod.TRAIN,mod.VALID)
        self.old_template=(mod.TEMPLATE,mod.TEMPLATE_ARCH,mod.TEMPLATE_PARAMS_B)
        mod.TRAIN=p/"train.jsonl"; mod.VALID=p/"valid.jsonl"
        mod.TRAIN.write_text('{"messages":[]}\n',encoding="utf-8")
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
        mod.TEMPLATE="provider/qwen2-0.5b-training"
        mod.TEMPLATE_ARCH="qwen2"
        mod.TEMPLATE_PARAMS_B="0.5"
        self.hf="Qwen/Qwen2.5-0.5B"
    def tearDown(self):
        mod.TRAIN,mod.VALID=self.old_paths
        mod.TEMPLATE,mod.TEMPLATE_ARCH,mod.TEMPLATE_PARAMS_B=self.old_template
        self.tmp.cleanup(); os.environ.pop(mod.CREATE_CONFIRM_ENV,None)

    def test_template_claim_requires_explicit_same_architecture_and_size(self):
        mod.require_compatible_template_claim()
        for template,arch,size in [
            ("","qwen2","0.5"),
            ("provider/qwen2-7b","qwen2","7"),
            ("provider/other-0.5b","other","0.5"),
            ("provider/qwen2-0.5b","qwen2","not-a-number"),
        ]:
            mod.TEMPLATE,mod.TEMPLATE_ARCH,mod.TEMPLATE_PARAMS_B=template,arch,size
            with self.assertRaises(SystemExit):
                mod.require_compatible_template_claim()

    def test_fingerprint_binds_dataset_training_and_template_metadata(self):
        a=mod.campaign_fingerprint(self.hf)
        self.assertEqual(a,mod.campaign_fingerprint(self.hf))
        mod.VALID.write_text('{"messages":[2]}\n',encoding="utf-8")
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf))
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
        b=mod.campaign_fingerprint(self.hf)
        mod.TEMPLATE="provider/qwen2-0.5b-training-v2"
        self.assertNotEqual(b,mod.campaign_fingerprint(self.hf))

    def test_create_confirmation_requires_full_exact_fingerprint(self):
        fp=mod.campaign_fingerprint(self.hf)
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp[:24]
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp
        mod.require_create_confirmation(fp)

    def test_account_duplicate_guard_matches_campaign_suffix(self):
        c=ClientFake(); fp=mod.campaign_fingerprint(self.hf); suffix=mod.campaign_suffix(fp)
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-existing",status="running",model=mod.TEMPLATE,from_hf_model=self.hf,
            model_output_name="acct/output-"+suffix,
        ))
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(c,self.hf,mod.TEMPLATE,suffix)
        self.assertIn("ft-existing",str(ctx.exception))

    def test_regression_ambiguous_create_timeout_retry_remains_blocked(self):
        """Regression-only rerun of the earlier ambiguous-create intervention."""
        c=ClientFake(); fp=mod.campaign_fingerprint(self.hf); suffix=mod.campaign_suffix(fp)
        self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,mod.TEMPLATE,suffix))
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-ambiguous",status="pending",model=mod.TEMPLATE,from_hf_model=self.hf,
            model_output_name="acct/qwen-"+suffix,
        ))
        observed=TimeoutError("connection lost after remote create commit")
        self.assertIsInstance(observed,TimeoutError)
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(c,self.hf,mod.TEMPLATE,suffix)
        self.assertIn("DUPLICATE_CREATE_ABORT",str(ctx.exception))
        self.assertIn("ft-ambiguous",str(ctx.exception))
        self.assertEqual(1,len(c.fine_tuning.jobs))

if __name__=="__main__": unittest.main(verbosity=2)

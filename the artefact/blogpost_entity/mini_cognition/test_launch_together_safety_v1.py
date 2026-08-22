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
        self.old=(mod.TRAIN,mod.VALID)
        mod.TRAIN=p/"train.jsonl"; mod.VALID=p/"valid.jsonl"
        mod.TRAIN.write_text('{"messages":[]}\n',encoding="utf-8")
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
        self.hf="Qwen/Qwen2.5-0.5B"
    def tearDown(self):
        mod.TRAIN,mod.VALID=self.old; self.tmp.cleanup(); os.environ.pop(mod.CREATE_CONFIRM_ENV,None)

    def test_fingerprint_binds_dataset_and_training_config(self):
        a=mod.campaign_fingerprint(self.hf)
        self.assertEqual(a,mod.campaign_fingerprint(self.hf))
        mod.VALID.write_text('{"messages":[2]}\n',encoding="utf-8")
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf))

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

    def test_unusual_ambiguous_create_timeout_retry_is_blocked(self):
        """Unusual experiment: server accepted create, transport outcome is ambiguous.

        Simulate a create endpoint that durably registers the campaign then times out before
        returning its job id. The next launch must discover the account-side job and abort,
        preventing a second paid create.
        """
        c=ClientFake(); fp=mod.campaign_fingerprint(self.hf); suffix=mod.campaign_suffix(fp)
        self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,mod.TEMPLATE,suffix))

        # Fault injection: remote side commits job, local side observes only timeout.
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

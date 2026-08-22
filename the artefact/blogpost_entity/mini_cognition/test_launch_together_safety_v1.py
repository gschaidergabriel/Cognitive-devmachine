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
        self.hf=mod.PRIMARY_HF_MODEL
        self.rev=mod.PRIMARY_HF_REVISION
    def tearDown(self):
        mod.TRAIN,mod.VALID=self.old; self.tmp.cleanup()
        for name in (mod.CREATE_CONFIRM_ENV,"CLAYCOG_HF_MODEL","CLAYCOG_HF_REVISION","CLAYCOG_INSTRUCT_HF_MODEL","CLAYCOG_INSTRUCT_HF_REVISION"):
            os.environ.pop(name,None)

    def test_fingerprint_binds_dataset_training_config_and_hf_revision(self):
        a=mod.campaign_fingerprint(self.hf,self.rev)
        self.assertEqual(a,mod.campaign_fingerprint(self.hf,self.rev))
        mod.VALID.write_text('{"messages":[2]}\n',encoding="utf-8")
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,self.rev))
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
        other_rev="1"*40
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,other_rev))

    def test_exact_revision_defaults_and_custom_override_fail_closed(self):
        model,revision=mod.resolve_hf_source(False)
        self.assertEqual(mod.PRIMARY_HF_MODEL,model)
        self.assertEqual(mod.PRIMARY_HF_REVISION,revision)
        model,revision=mod.resolve_hf_source(True)
        self.assertEqual(mod.INSTRUCT_HF_MODEL,model)
        self.assertEqual(mod.INSTRUCT_HF_REVISION,revision)

        os.environ["CLAYCOG_HF_MODEL"]="example/custom-qwen2"
        with self.assertRaises(SystemExit): mod.resolve_hf_source(False)
        os.environ["CLAYCOG_HF_REVISION"]="abc"
        with self.assertRaises(SystemExit): mod.resolve_hf_source(False)
        os.environ["CLAYCOG_HF_REVISION"]="2"*40
        model,revision=mod.resolve_hf_source(False)
        self.assertEqual("example/custom-qwen2",model)
        self.assertEqual("2"*40,revision)

    def test_create_confirmation_requires_full_exact_fingerprint(self):
        fp=mod.campaign_fingerprint(self.hf,self.rev)
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp[:24]
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp
        mod.require_create_confirmation(fp)

    def test_account_duplicate_guard_matches_campaign_suffix(self):
        c=ClientFake(); fp=mod.campaign_fingerprint(self.hf,self.rev); suffix=mod.campaign_suffix(fp)
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-existing",status="running",model=mod.TEMPLATE,from_hf_model=self.hf,
            model_output_name="acct/output-"+suffix,
        ))
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(c,self.hf,mod.TEMPLATE,suffix)
        self.assertIn("ft-existing",str(ctx.exception))

    def test_unusual_ambiguous_create_timeout_retry_is_blocked(self):
        """Regression of the previously consumed unusual experiment from PR #772.

        Simulate a create endpoint that durably registers the campaign then times out before
        returning its job id. The next launch must discover the account-side job and abort,
        preventing a second paid create. This rerun is regression-only, not a new unusual
        experiment for the current go.
        """
        c=ClientFake(); fp=mod.campaign_fingerprint(self.hf,self.rev); suffix=mod.campaign_suffix(fp)
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

#!/usr/bin/env python3
import importlib.util, json, os, tempfile, types, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("launch_together_v1", HERE/"launch_together_v1.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class FineTuningFake:
    def __init__(self): self.jobs=[]
    def list(self): return types.SimpleNamespace(data=list(self.jobs))

class ClientFake:
    def __init__(self): self.fine_tuning=FineTuningFake()

class ConstructorFake:
    calls=[]
    def __init__(self,**kwargs):
        type(self).calls.append(dict(kwargs))
        self.fine_tuning=FineTuningFake()

class LimitsCurrent:
    def get_model_limits(self,model):
        return types.SimpleNamespace(full_training={"ok":True},model=model)

class LimitsLegacy:
    def model_limits(self,model_name):
        return types.SimpleNamespace(supports_full_training=True,model=model_name)

class LimitClient:
    def __init__(self,ft): self.fine_tuning=ft

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); p=Path(self.tmp.name)
        self.old=(mod.TRAIN,mod.VALID)
        mod.TRAIN=p/"train.jsonl"; mod.VALID=p/"valid.jsonl"
        mod.TRAIN.write_text('{"messages":[]}\n',encoding="utf-8")
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
        os.environ[mod.CREATE_LEDGER_DIR_ENV]=str(p/"ledger")
        self.hf="Qwen/Qwen2.5-0.5B"
    def tearDown(self):
        mod.TRAIN,mod.VALID=self.old; self.tmp.cleanup()
        os.environ.pop(mod.CREATE_CONFIRM_ENV,None)
        os.environ.pop(mod.CREATE_LEDGER_DIR_ENV,None)
        ConstructorFake.calls.clear()

    def test_fingerprint_binds_dataset_and_training_config(self):
        a=mod.campaign_fingerprint(self.hf)
        self.assertEqual(a,mod.campaign_fingerprint(self.hf))
        mod.VALID.write_text('{"messages":[2]}\n',encoding="utf-8")
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf))

    def test_fingerprint_binds_revision_template_and_corpus_generation(self):
        a=mod.campaign_fingerprint(self.hf,hf_revision="rev-a",template=self.hf,corpus_version="v2")
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,hf_revision="rev-b",template=self.hf,corpus_version="v2"))
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,hf_revision="rev-a",template="other/model",corpus_version="v2"))
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,hf_revision="rev-a",template=self.hf,corpus_version="v1"))

    def test_exact_05b_template_default_and_near_template_create_block(self):
        self.assertEqual(mod.HF_MODEL,mod.TEMPLATE)
        mod.assert_create_template_safe(self.hf,self.hf)
        for candidate in ("Qwen/Qwen2.5-1.5B","Qwen/Qwen2.5-7B-Instruct-Turbo"):
            with self.assertRaises(SystemExit) as ctx:
                mod.assert_create_template_safe(self.hf,candidate)
            self.assertIn("TEMPLATE_COMPATIBILITY_ABORT",str(ctx.exception))

    def test_immutable_hf_revision_gate(self):
        for bad in ("","main","master","latest","HEAD"):
            with self.assertRaises(SystemExit): mod.assert_immutable_revision(bad)
        self.assertEqual(mod.HF_REVISION,mod.assert_immutable_revision(mod.HF_REVISION))

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

    def test_ambiguous_create_visible_in_account_is_blocked(self):
        c=ClientFake(); fp=mod.campaign_fingerprint(self.hf); suffix=mod.campaign_suffix(fp)
        self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,mod.TEMPLATE,suffix))
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-ambiguous",status="pending",model=mod.TEMPLATE,from_hf_model=self.hf,
            model_output_name="acct/qwen-"+suffix,
        ))
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(c,self.hf,mod.TEMPLATE,suffix)
        self.assertIn("DUPLICATE_CREATE_ABORT",str(ctx.exception))
        self.assertEqual(1,len(c.fine_tuning.jobs))

    def test_local_intent_blocks_retry_even_if_provider_list_is_stale(self):
        c=ClientFake(); fp=mod.campaign_fingerprint(self.hf); suffix=mod.campaign_suffix(fp)
        self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,mod.TEMPLATE,suffix))
        path=mod.arm_create_intent(fp,self.hf,suffix)
        mod.update_create_intent(path,"UNKNOWN_REMOTE_CREATE",error_class="TimeoutError")
        self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,mod.TEMPLATE,suffix))
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_local_create_intent(fp)
        self.assertIn("UNKNOWN_REMOTE_CREATE",str(ctx.exception))
        self.assertIn("reconcile exact provider state",str(ctx.exception))

    def test_create_intent_is_atomic_exclusive_and_contains_no_secret(self):
        fp=mod.campaign_fingerprint(self.hf); suffix=mod.campaign_suffix(fp)
        os.environ["TOGETHER_API_KEY"]="SHOULD_NOT_ENTER_LEDGER"
        try:
            path=mod.arm_create_intent(fp,self.hf,suffix)
            data=path.read_text(encoding="utf-8")
            payload=json.loads(data)
            self.assertEqual("CREATE_ARMED",payload["status"])
            self.assertNotIn("SHOULD_NOT_ENTER_LEDGER",data)
            self.assertEqual(0o600,path.stat().st_mode & 0o777)
            with self.assertRaises(SystemExit):
                mod.arm_create_intent(fp,self.hf,suffix)
        finally:
            os.environ.pop("TOGETHER_API_KEY",None)

    def test_billed_create_client_disables_sdk_retries(self):
        mod.new_zero_retry_create_client(ConstructorFake)
        self.assertEqual([{"max_retries":0}],ConstructorFake.calls)

    def test_known_job_is_durably_bound_to_exact_fingerprint(self):
        fp=mod.campaign_fingerprint(self.hf); suffix=mod.campaign_suffix(fp)
        path=mod.arm_create_intent(fp,self.hf,suffix)
        mod.update_create_intent(path,"JOB_KNOWN",job_id="ft-known")
        payload=mod.read_create_ledger(fp)
        self.assertEqual("JOB_KNOWN",payload["status"])
        self.assertEqual("ft-known",payload["job_id"])
        self.assertEqual(fp,payload["fingerprint"])
        with self.assertRaises(SystemExit): mod.assert_no_local_create_intent(fp)

    def test_model_limits_current_legacy_and_missing_surfaces(self):
        _,surface=mod.get_full_training_limits(LimitClient(LimitsCurrent()),self.hf)
        self.assertEqual("get_model_limits",surface)
        _,surface=mod.get_full_training_limits(LimitClient(LimitsLegacy()),self.hf)
        self.assertEqual("model_limits",surface)
        class Missing: pass
        with self.assertRaises(SystemExit): mod.get_full_training_limits(LimitClient(Missing()),self.hf)

if __name__=="__main__": unittest.main(verbosity=2)

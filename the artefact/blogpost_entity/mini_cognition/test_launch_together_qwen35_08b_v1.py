#!/usr/bin/env python3
import builtins,importlib.util,json,os,stat,sys,tempfile,types,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("launch08",HERE/"launch_together_qwen35_08b_v1.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FT:
    def __init__(self,jobs=None,full=True):self.jobs=list(jobs or []);self.full=full;self.limits_kwargs=None;self.estimate_kwargs=None
    def list(self):return types.SimpleNamespace(data=self.jobs)
    def model_limits(self,**kw):self.limits_kwargs=kw;return types.SimpleNamespace(supports_full_training=self.full,full_training=types.SimpleNamespace() if self.full else None)
    def estimate_price(self,**kw):self.estimate_kwargs=kw;return types.SimpleNamespace(estimated_total_price=4.0,allowed_to_proceed=True)
    def create(self,training_file,*,validation_file=None,model=None,n_epochs=None,n_evals=None,n_checkpoints=None,random_seed=None,learning_rate=None,warmup_ratio=None,suffix=None,training_method="sft",train_on_inputs="auto",lora=True):return None
class LegacyFT:
    def create(self,training_file,*,training_method="sft"):return None
class Client:
    def __init__(self,jobs=None,full=True,ft=None):self.fine_tuning=ft or FT(jobs,full)
class TogetherCtor:
    last=None
    def __init__(self,**kw):type(self).last=kw
class Tests(unittest.TestCase):
    def setUp(self):
        self.c=os.environ.pop(m.CREATE_CONFIRM_ENV,None);self.l=os.environ.get(m.CREATE_LEDGER_DIR_ENV);self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.ot,self.ov=m.TRAIN,m.VALID;m.TRAIN=r/"t.jsonl";m.VALID=r/"v.jsonl";m.TRAIN.write_text('{"messages":[]}\n');m.VALID.write_text('{"messages":[]}\n')
    def tearDown(self):
        m.TRAIN,m.VALID=self.ot,self.ov;self.t.cleanup()
        if self.c is None:os.environ.pop(m.CREATE_CONFIRM_ENV,None)
        else:os.environ[m.CREATE_CONFIRM_ENV]=self.c
        if self.l is None:os.environ.pop(m.CREATE_LEDGER_DIR_ENV,None)
        else:os.environ[m.CREATE_LEDGER_DIR_ENV]=self.l
    def test_model_and_direct_campaign(self):
        self.assertEqual(m.MODEL,"Qwen/Qwen3.5-0.8B");m.validate_static_contract();d=m.campaign_descriptor();self.assertEqual(d["schema"],"claycog-08b-together-direct-campaign/v3");self.assertEqual(d["training_type"],{"type":"Full"});self.assertEqual(d["training_method"],{"method":"sft","train_on_inputs":"auto"});self.assertEqual(d["create_contract"],{"training_method":"sft","train_on_inputs":"auto","lora":False});self.assertEqual(d["random_seed"],3407);raw=json.dumps(d);self.assertNotIn("from_hf_model",raw);self.assertNotIn("template_model",raw)
    def test_local_checks_use_canonical_v2_validator(self):
        with mock.patch.object(m.subprocess,"run") as run:m.local_checks()
        self.assertEqual(run.call_count,2);generate=run.call_args_list[0].args[0];validate=run.call_args_list[1].args[0]
        self.assertEqual(Path(generate[1]).name,"generate_sft_v2.py");self.assertEqual(Path(validate[1]).name,"validate_corpus_v2.py");self.assertEqual(validate[2:],[str(m.TRAIN),str(m.VALID)]);self.assertTrue(run.call_args_list[0].kwargs["check"]);self.assertTrue(run.call_args_list[1].kwargs["check"])
    def test_free_only_policy_rejects_before_secret_lookup_and_provider_import(self):
        secret_reads=[];provider_imports=[];original_import=builtins.__import__
        def guarded_get(key,default=None):
            if key=="TOGETHER_API_KEY":secret_reads.append(key);raise AssertionError("secret lookup happened before FREE_ONLY rejection")
            return default
        def guarded_import(name,globals=None,locals=None,fromlist=(),level=0):
            if name=="together" or name.startswith("together."):provider_imports.append(name);raise AssertionError("Together import happened before FREE_ONLY rejection")
            return original_import(name,globals,locals,fromlist,level)
        with tempfile.TemporaryDirectory() as td:
            policy=Path(td)/"SUPERVISOR_INBOX.json";policy.write_text(json.dumps({"verified_updates":{"free_only":True}}))
            with mock.patch.object(m,"SUPERVISOR_POLICY",policy),mock.patch.object(m,"local_checks",lambda:None),mock.patch.object(m.os.environ,"get",side_effect=guarded_get),mock.patch("builtins.__import__",side_effect=guarded_import),mock.patch.object(sys,"argv",["launcher"]):
                with self.assertRaisesRegex(SystemExit,"FREE_ONLY_PROVIDER_REJECT"):m.main()
        self.assertEqual(secret_reads,[]);self.assertEqual(provider_imports,[])
    def test_execution_policy_fails_closed_and_only_explicit_false_opens(self):
        with tempfile.TemporaryDirectory() as td:
            policy=Path(td)/"policy.json";policy.write_text("{}")
            with self.assertRaisesRegex(SystemExit,"EXECUTION_POLICY_FREE_ONLY_UNKNOWN"):m.assert_provider_execution_allowed(policy)
            policy.write_text(json.dumps({"verified_updates":{"free_only":False}}));self.assertIsNone(m.assert_provider_execution_allowed(policy))
            policy.write_text("{bad")
            with self.assertRaisesRegex(SystemExit,"EXECUTION_POLICY_UNREADABLE"):m.assert_provider_execution_allowed(policy)
    def test_sdk_v2_model_limits(self):
        c=Client();m.get_full_training_limits(c);self.assertEqual(c.fine_tuning.limits_kwargs,{"model_name":m.EXPECTED_MODEL})
        with self.assertRaises(SystemExit):m.get_full_training_limits(Client(full=False))
    def test_sdk_create_signature_gate(self):
        p=m.assert_sdk_create_contract(Client());self.assertIn("training_method",p);self.assertIn("train_on_inputs",p);self.assertIn("lora",p)
        with self.assertRaisesRegex(SystemExit,"SDK_CREATE_CONTRACT_REJECT"):m.assert_sdk_create_contract(Client(ft=LegacyFT()))
    def test_estimate_schema_subset(self):
        c=Client();m.estimate_price(c,"t","v");q=c.fine_tuning.estimate_kwargs;self.assertEqual(q["training_type"],{"type":"Full"});self.assertEqual(q["training_method"],{"method":"sft","train_on_inputs":"auto"})
        for x in ("random_seed","learning_rate","warmup_ratio","from_hf_model"):self.assertNotIn(x,q)
    def test_create_payload_matches_current_sdk_v2_shape(self):
        p=m.create_payload("t","v","s");self.assertNotIn("training_type",p);self.assertEqual(p["training_method"],"sft");self.assertEqual(p["train_on_inputs"],"auto");self.assertIs(p["lora"],False);self.assertEqual(p["random_seed"],3407);self.assertEqual(p["learning_rate"],1e-5);self.assertEqual(p["warmup_ratio"],.03)
        for x in ("from_hf_model","hf_model_revision"):self.assertNotIn(x,p)
    def test_fingerprint_binds_dataset(self):
        a=m.campaign_fingerprint();m.TRAIN.write_text('{"messages":[1]}\n');self.assertNotEqual(a,m.campaign_fingerprint())
    def test_duplicate_guard(self):
        s="claycog08b-v3-dead";c=Client([{"id":"j","status":"running","model":m.MODEL,"model_output_name":"x"+s}])
        with self.assertRaises(SystemExit):m.assert_no_duplicate_campaign(c,s)
    def test_confirmation_and_private_intent(self):
        fp="a"*64
        with self.assertRaises(SystemExit):m.require_create_confirmation(fp)
        os.environ[m.CREATE_CONFIRM_ENV]=fp;m.require_create_confirmation(fp)
        with tempfile.TemporaryDirectory() as td:
            os.environ[m.CREATE_LEDGER_DIR_ENV]=td;fp=m.campaign_fingerprint();p=m.arm_create_intent(fp,m.campaign_suffix(fp));self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600);entry=m.read_create_ledger(fp);self.assertEqual(entry["schema"],"claycog-together-create-intent/v3");self.assertEqual(entry["campaign"]["training_type"],{"type":"Full"});self.assertEqual(entry["campaign"]["create_contract"],{"training_method":"sft","train_on_inputs":"auto","lora":False})
    def _full_expected(self):
        return {"training_file":"t","validation_file":"v","model":m.MODEL,"suffix":"claycog08b-v3-dead","n_epochs":3,"n_evals":2,"n_checkpoints":1,"learning_rate":1e-5,"warmup_ratio":.03,"training_method":{"method":"sft","train_on_inputs":"auto"},"training_type":{"type":"Full"}}
    def test_created_job_identity_mismatch_detection(self):
        expected=self._full_expected();good=types.SimpleNamespace(**{**expected,"training_method":types.SimpleNamespace(**expected["training_method"]),"training_type":types.SimpleNamespace(**expected["training_type"])});self.assertEqual(m.created_job_identity_mismatches(good,expected),{})
        bad=types.SimpleNamespace(**{**expected,"suffix":"wrong","training_method":types.SimpleNamespace(**expected["training_method"]),"training_type":types.SimpleNamespace(**expected["training_type"])});mm=m.created_job_identity_mismatches(bad,expected);self.assertEqual(mm["suffix"],{"expected":"claycog08b-v3-dead","observed":"wrong"})
    def test_seed_identity_uses_create_response_not_retrieve_schema(self):
        self.assertNotIn("random_seed",self._full_expected());m.assert_created_job_seed(types.SimpleNamespace(random_seed=3407))
        for job in (types.SimpleNamespace(random_seed=9),types.SimpleNamespace()):
            with self.assertRaises(SystemExit):m.assert_created_job_seed(job)
    def test_provider_training_identity_substitution_fails_closed(self):
        expected=self._full_expected();substituted=types.SimpleNamespace(**{**expected,"learning_rate":9e-4,"warmup_ratio":.5,"training_method":types.SimpleNamespace(**expected["training_method"]),"training_type":types.SimpleNamespace(type="Lora",lora_r=16)})
        mm=m.created_job_identity_mismatches(substituted,expected);self.assertEqual(mm["learning_rate"],{"expected":1e-5,"observed":9e-4});self.assertEqual(mm["warmup_ratio"],{"expected":.03,"observed":.5});self.assertEqual(mm["training_type"],{"expected":{"type":"Full"},"observed":{"type":"Lora"}})
    def test_zero_retry(self):
        TogetherCtor.last=None;m.new_zero_retry_create_client(TogetherCtor);self.assertEqual(TogetherCtor.last,{"max_retries":0})
if __name__=="__main__":unittest.main()

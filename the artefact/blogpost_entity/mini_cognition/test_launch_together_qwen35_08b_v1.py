#!/usr/bin/env python3
import builtins,importlib.util,json,os,socket,stat,tempfile,types,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("launch08",HERE/"launch_together_qwen35_08b_v1.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FT:
    def __init__(self,jobs=None,full=True):self.jobs=list(jobs or []);self.full=full;self.limits_kwargs=None;self.estimate_kwargs=None
    def list(self):return types.SimpleNamespace(data=self.jobs)
    def model_limits(self,**kw):self.limits_kwargs=kw;return types.SimpleNamespace(supports_full_training=self.full,full_training=types.SimpleNamespace() if self.full else None)
    def estimate_price(self,**kw):self.estimate_kwargs=kw;return types.SimpleNamespace(estimated_total_price=4.0,allowed_to_proceed=True)
class Client:
    def __init__(self,jobs=None,full=True):self.fine_tuning=FT(jobs,full)
class TogetherCtor:
    last=None
    def __init__(self,**kw):type(self).last=kw
class SecretTripwireEnv(dict):
    def get(self,key,default=None):
        if key=="TOGETHER_API_KEY":raise AssertionError("SECRET_LOOKUP_TRIPWIRE")
        return super().get(key,default)
    def __getitem__(self,key):
        if key=="TOGETHER_API_KEY":raise AssertionError("SECRET_LOOKUP_TRIPWIRE")
        return super().__getitem__(key)
class Tests(unittest.TestCase):
    def setUp(self):
        self.c=os.environ.pop(m.CREATE_CONFIRM_ENV,None);self.l=os.environ.get(m.CREATE_LEDGER_DIR_ENV);self.pm=os.environ.get("CLAY_PROVIDER_MODE");self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.ot,self.ov=m.TRAIN,m.VALID;m.TRAIN=r/"t.jsonl";m.VALID=r/"v.jsonl";m.TRAIN.write_text('{"messages":[]}\n');m.VALID.write_text('{"messages":[]}\n')
    def tearDown(self):
        m.TRAIN,m.VALID=self.ot,self.ov;self.t.cleanup()
        if self.c is None:os.environ.pop(m.CREATE_CONFIRM_ENV,None)
        else:os.environ[m.CREATE_CONFIRM_ENV]=self.c
        if self.l is None:os.environ.pop(m.CREATE_LEDGER_DIR_ENV,None)
        else:os.environ[m.CREATE_LEDGER_DIR_ENV]=self.l
        if self.pm is None:os.environ.pop("CLAY_PROVIDER_MODE",None)
        else:os.environ["CLAY_PROVIDER_MODE"]=self.pm
    def _control(self,mode="FREE_ONLY",free_only=True,together_forbidden=True):
        p=Path(self.t.name)/"control.json";p.write_text(json.dumps({"status":"ACTIVE","mode":mode,"preserved_hard_rules":{"free_only":free_only,"together_forbidden":together_forbidden}}));return p
    def test_model_and_direct_campaign(self):
        self.assertEqual(m.MODEL,"Qwen/Qwen3.5-0.8B");m.validate_static_contract();d=m.campaign_descriptor();self.assertEqual(d["training_type"],{"type":"Full"});self.assertEqual(d["random_seed"],3407);raw=json.dumps(d);self.assertNotIn("from_hf_model",raw);self.assertNotIn("template_model",raw)
    def test_local_checks_use_canonical_v2_validator(self):
        with mock.patch.object(m.subprocess,"run") as run:
            m.local_checks()
        self.assertEqual(run.call_count,2)
        generate=run.call_args_list[0].args[0];validate=run.call_args_list[1].args[0]
        self.assertEqual(Path(generate[1]).name,"generate_sft_v2.py")
        self.assertEqual(Path(validate[1]).name,"validate_corpus_v2.py")
        self.assertEqual(validate[2:],[str(m.TRAIN),str(m.VALID)])
        self.assertTrue(run.call_args_list[0].kwargs["check"]);self.assertTrue(run.call_args_list[1].kwargs["check"])
    def test_repository_control_currently_blocks_together_paid(self):
        control=m.load_provider_execution_control();self.assertEqual(control["mode"],m.CONTROL_MODE_FREE_ONLY);self.assertTrue(control["preserved_hard_rules"]["free_only"]);self.assertTrue(control["preserved_hard_rules"]["together_forbidden"]);self.assertFalse(m.provider_cost_admitted(m.TOGETHER_COST_CLASS,control))
    def test_cost_class_admission_is_control_bound(self):
        free={"status":"ACTIVE","mode":m.CONTROL_MODE_FREE_ONLY,"preserved_hard_rules":{"free_only":True,"together_forbidden":False}}
        self.assertTrue(m.provider_cost_admitted(m.COST_FREE,free))
        for cost in (m.COST_PAID,m.COST_SUBSCRIPTION,m.COST_UNKNOWN):self.assertFalse(m.provider_cost_admitted(cost,free))
        paid={"status":"ACTIVE","mode":m.CONTROL_MODE_PAID_ALLOWED,"preserved_hard_rules":{"free_only":False,"together_forbidden":False}}
        self.assertTrue(m.provider_cost_admitted(m.COST_PAID,paid));self.assertTrue(m.provider_cost_admitted(m.COST_SUBSCRIPTION,paid));self.assertFalse(m.provider_cost_admitted(m.COST_UNKNOWN,paid))
        paid["preserved_hard_rules"]["together_forbidden"]=True;self.assertFalse(m.provider_cost_admitted(m.COST_PAID,paid))
    def test_env_paid_allowed_cannot_override_free_only_control_before_any_tripwire(self):
        control=self._control();old_control,old_env,old_argv,old_local=m.CONTROL_PATH,m.os.environ,m.sys.argv,m.local_checks;old_import=builtins.__import__;old_socket=socket.socket
        trip=SecretTripwireEnv(dict(old_env));trip["CLAY_PROVIDER_MODE"]="PAID_ALLOWED";trip["TOGETHER_API_KEY"]="CANARY_MUST_NOT_BE_READ"
        def import_tripwire(name,*args,**kwargs):
            if name=="together" or name.startswith("together."):raise AssertionError("TOGETHER_IMPORT_TRIPWIRE")
            return old_import(name,*args,**kwargs)
        def socket_tripwire(*args,**kwargs):raise AssertionError("NETWORK_TRIPWIRE")
        def local_tripwire():raise AssertionError("LOCAL_CHECKS_TRIPWIRE")
        try:
            m.CONTROL_PATH=control;m.os.environ=trip;m.sys.argv=["launch_together_qwen35_08b_v1.py"];m.local_checks=local_tripwire;builtins.__import__=import_tripwire;socket.socket=socket_tripwire
            with self.assertRaises(SystemExit) as cm:m.main()
            self.assertIn("PROVIDER_ADMISSION_BLOCK",str(cm.exception));self.assertIn("cost_class=PAID",str(cm.exception))
        finally:
            socket.socket=old_socket;builtins.__import__=old_import;m.local_checks=old_local;m.sys.argv=old_argv;m.os.environ=old_env;m.CONTROL_PATH=old_control
    def test_sdk_v2_model_limits(self):
        c=Client();m.get_full_training_limits(c);self.assertEqual(c.fine_tuning.limits_kwargs,{"model_name":m.EXPECTED_MODEL})
        with self.assertRaises(SystemExit):m.get_full_training_limits(Client(full=False))
    def test_estimate_schema_subset(self):
        c=Client();m.estimate_price(c,"t","v");q=c.fine_tuning.estimate_kwargs;self.assertEqual(q["training_type"],{"type":"Full"});self.assertEqual(q["training_method"],{"method":"sft","train_on_inputs":"auto"})
        for x in ("random_seed","learning_rate","warmup_ratio","from_hf_model"):self.assertNotIn(x,q)
    def test_create_explicit_full_and_seed(self):
        p=m.create_payload("t","v","s");self.assertEqual(p["training_type"],{"type":"Full"});self.assertEqual(p["random_seed"],3407);self.assertEqual(p["learning_rate"],1e-5);self.assertEqual(p["warmup_ratio"],.03)
        for x in ("lora","from_hf_model","hf_model_revision","train_on_inputs"):self.assertNotIn(x,p)
    def test_fingerprint_binds_dataset(self):
        a=m.campaign_fingerprint();m.TRAIN.write_text('{"messages":[1]}\n');self.assertNotEqual(a,m.campaign_fingerprint())
    def test_duplicate_guard(self):
        s="claycog08b-v2-dead";c=Client([{"id":"j","status":"running","model":m.MODEL,"model_output_name":"x"+s}])
        with self.assertRaises(SystemExit):m.assert_no_duplicate_campaign(c,s)
    def test_confirmation_and_private_intent(self):
        fp="a"*64
        with self.assertRaises(SystemExit):m.require_create_confirmation(fp)
        os.environ[m.CREATE_CONFIRM_ENV]=fp;m.require_create_confirmation(fp)
        with tempfile.TemporaryDirectory() as td:
            os.environ[m.CREATE_LEDGER_DIR_ENV]=td;fp=m.campaign_fingerprint();p=m.arm_create_intent(fp,m.campaign_suffix(fp));self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600);self.assertEqual(m.read_create_ledger(fp)["campaign"]["training_type"],{"type":"Full"})
    def _full_expected(self):
        return {"training_file":"t","validation_file":"v","model":m.MODEL,"suffix":"claycog08b-v2-dead","n_epochs":3,"n_evals":2,"n_checkpoints":1,"random_seed":3407,"learning_rate":1e-5,"warmup_ratio":.03,"training_method":{"method":"sft","train_on_inputs":"auto"},"training_type":{"type":"Full"}}
    def test_created_job_identity_mismatch_detection(self):
        expected=self._full_expected();good=types.SimpleNamespace(**{**expected,"training_method":types.SimpleNamespace(**expected["training_method"]),"training_type":types.SimpleNamespace(**expected["training_type"])});self.assertEqual(m.created_job_identity_mismatches(good,expected),{})
        bad=types.SimpleNamespace(**{**expected,"random_seed":9,"training_method":types.SimpleNamespace(**expected["training_method"]),"training_type":types.SimpleNamespace(**expected["training_type"])});mm=m.created_job_identity_mismatches(bad,expected);self.assertEqual(mm["random_seed"],{"expected":3407,"observed":9})
    def test_provider_training_identity_substitution_fails_closed(self):
        expected=self._full_expected();substituted=types.SimpleNamespace(**{**expected,"learning_rate":9e-4,"warmup_ratio":.5,"training_method":types.SimpleNamespace(**expected["training_method"]),"training_type":types.SimpleNamespace(type="Lora",lora_r=16)})
        mm=m.created_job_identity_mismatches(substituted,expected);self.assertEqual(mm["learning_rate"],{"expected":1e-5,"observed":9e-4});self.assertEqual(mm["warmup_ratio"],{"expected":.03,"observed":.5});self.assertEqual(mm["training_type"],{"expected":{"type":"Full"},"observed":{"type":"Lora"}})
    def test_zero_retry(self):
        TogetherCtor.last=None;m.new_zero_retry_create_client(TogetherCtor);self.assertEqual(TogetherCtor.last,{"max_retries":0})
if __name__=="__main__":unittest.main()
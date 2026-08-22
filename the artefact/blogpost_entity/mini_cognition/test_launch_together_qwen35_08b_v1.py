#!/usr/bin/env python3
import importlib.util,json,os,stat,tempfile,types,unittest
from pathlib import Path
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
class Tests(unittest.TestCase):
    def setUp(self):
        self.c=os.environ.pop(m.CREATE_CONFIRM_ENV,None);self.l=os.environ.get(m.CREATE_LEDGER_DIR_ENV);self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.ot,self.ov,self.oc=m.TRAIN,m.VALID,m.CONTROL_PATH;m.TRAIN=r/"t.jsonl";m.VALID=r/"v.jsonl";m.CONTROL_PATH=r/"control.json";m.TRAIN.write_text('{"messages":[]}\n');m.VALID.write_text('{"messages":[]}\n')
    def tearDown(self):
        m.TRAIN,m.VALID,m.CONTROL_PATH=self.ot,self.ov,self.oc;self.t.cleanup()
        if self.c is None:os.environ.pop(m.CREATE_CONFIRM_ENV,None)
        else:os.environ[m.CREATE_CONFIRM_ENV]=self.c
        if self.l is None:os.environ.pop(m.CREATE_LEDGER_DIR_ENV,None)
        else:os.environ[m.CREATE_LEDGER_DIR_ENV]=self.l
    def test_model_and_direct_campaign(self):
        self.assertEqual(m.MODEL,"Qwen/Qwen3.5-0.8B");m.validate_static_contract();d=m.campaign_descriptor();self.assertEqual(d["training_type"],{"type":"Full"});self.assertEqual(d["random_seed"],3407);raw=json.dumps(d);self.assertNotIn("from_hf_model",raw);self.assertNotIn("template_model",raw)
    def test_free_only_rejects_from_canonical_control(self):
        m.CONTROL_PATH.write_text(json.dumps({"mode":"FREE_ONLY"}))
        self.assertEqual(m.active_research_mode(),"FREE_ONLY")
        with self.assertRaisesRegex(SystemExit,"FREE_ONLY_PROVIDER_REJECTED_BEFORE_SECRET_OR_NETWORK"):m.assert_provider_execution_admitted()
    def test_free_only_guard_precedes_secret_lookup_in_main(self):
        source=(HERE/"launch_together_qwen35_08b_v1.py").read_text(encoding="utf-8").split("def main():",1)[1]
        self.assertLess(source.index("assert_provider_execution_admitted()"),source.index('os.environ.get("TOGETHER_API_KEY")'))
    def test_missing_or_malformed_control_fails_closed(self):
        with self.assertRaisesRegex(SystemExit,"PROVIDER_CONTROL_UNRESOLVED"):m.assert_provider_execution_admitted()
        m.CONTROL_PATH.write_text("not-json")
        with self.assertRaisesRegex(SystemExit,"PROVIDER_CONTROL_UNRESOLVED"):m.assert_provider_execution_admitted()
        m.CONTROL_PATH.write_text("{}")
        with self.assertRaisesRegex(SystemExit,"PROVIDER_CONTROL_MODE_MISSING"):m.assert_provider_execution_admitted()
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
    def test_created_job_identity_mismatch_detection(self):
        expected={"training_file":"t","validation_file":"v","model":m.MODEL,"n_epochs":3,"n_evals":2,"random_seed":3407}
        good=types.SimpleNamespace(**expected);self.assertEqual(m.created_job_identity_mismatches(good,expected),{})
        bad=types.SimpleNamespace(**{**expected,"random_seed":9});mm=m.created_job_identity_mismatches(bad,expected);self.assertEqual(mm["random_seed"],{"expected":3407,"observed":9})
    def test_zero_retry(self):
        TogetherCtor.last=None;m.new_zero_retry_create_client(TogetherCtor);self.assertEqual(TogetherCtor.last,{"max_retries":0})
if __name__=="__main__":unittest.main()

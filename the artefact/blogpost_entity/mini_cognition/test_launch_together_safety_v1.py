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
        self.rev=mod.PINNED_REVISIONS[self.hf]
        # Synthetic Qwen2-family candidate used only for local gate tests. This test does
        # not claim that Together currently admits it for fine-tuning.
        self.template="Qwen/Qwen2.5-7B-Instruct-Turbo"
    def tearDown(self):
        mod.TRAIN,mod.VALID=self.old; self.tmp.cleanup(); os.environ.pop(mod.CREATE_CONFIRM_ENV,None)

    def fp(self):
        return mod.campaign_fingerprint(self.hf,self.rev,self.template)

    def test_fingerprint_binds_dataset_checkpoint_revision_and_template(self):
        a=self.fp()
        self.assertEqual(a,self.fp())
        mod.VALID.write_text('{"messages":[2]}\n',encoding="utf-8")
        self.assertNotEqual(a,self.fp())
        mod.VALID.write_text('{"messages":[1]}\n',encoding="utf-8")
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,"different-revision",self.template))
        self.assertNotEqual(a,mod.campaign_fingerprint(self.hf,self.rev,"Qwen/Qwen2.5-other-template"))

    def test_template_gate_has_no_implicit_default_and_rejects_qwen3_shortcut(self):
        old=mod.TEMPLATE
        try:
            mod.TEMPLATE=""
            with self.assertRaises(SystemExit) as missing:
                mod.resolve_template("")
            self.assertIn("TOGETHER_TEMPLATE_BLOCKED",str(missing.exception))
            with self.assertRaises(SystemExit) as mismatch:
                mod.resolve_template("Qwen/Qwen3.5-0.8B")
            self.assertIn("ARCHITECTURE_ABORT",str(mismatch.exception))
            self.assertEqual(self.template,mod.resolve_template(self.template))
        finally:
            mod.TEMPLATE=old

    def test_checkpoint_revision_is_pinned_or_explicit(self):
        self.assertEqual(self.rev,mod.resolve_revision(self.hf,""))
        self.assertEqual(
            mod.PINNED_REVISIONS["Qwen/Qwen2.5-0.5B-Instruct"],
            mod.resolve_revision("Qwen/Qwen2.5-0.5B-Instruct","")
        )
        with self.assertRaises(SystemExit) as missing:
            mod.resolve_revision("example/unknown","")
        self.assertIn("HF_REVISION_REQUIRED",str(missing.exception))
        self.assertEqual("deadbeef",mod.resolve_revision("example/unknown","deadbeef"))

    def test_create_confirmation_requires_full_exact_fingerprint(self):
        fp=self.fp()
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp[:24]
        with self.assertRaises(SystemExit): mod.require_create_confirmation(fp)
        os.environ[mod.CREATE_CONFIRM_ENV]=fp
        mod.require_create_confirmation(fp)

    def test_account_duplicate_guard_matches_campaign_suffix(self):
        c=ClientFake(); fp=self.fp(); suffix=mod.campaign_suffix(fp)
        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-existing",status="running",model=self.template,from_hf_model=self.hf,
            model_output_name="acct/output-"+suffix,
        ))
        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(c,self.hf,self.template,suffix)
        self.assertIn("ft-existing",str(ctx.exception))

    def test_regression_ambiguous_create_timeout_retry_is_blocked(self):
        """Regression-only rerun of the already-consumed PR #772 fault intervention."""
        c=ClientFake(); fp=self.fp(); suffix=mod.campaign_suffix(fp)
        self.assertEqual([],mod.matching_campaign_jobs(c,self.hf,self.template,suffix))

        c.fine_tuning.jobs.append(types.SimpleNamespace(
            id="ft-ambiguous",status="pending",model=self.template,from_hf_model=self.hf,
            model_output_name="acct/qwen-"+suffix,
        ))
        observed=TimeoutError("connection lost after remote create commit")
        self.assertIsInstance(observed,TimeoutError)

        with self.assertRaises(SystemExit) as ctx:
            mod.assert_no_duplicate_campaign(c,self.hf,self.template,suffix)
        self.assertIn("DUPLICATE_CREATE_ABORT",str(ctx.exception))
        self.assertIn("ft-ambiguous",str(ctx.exception))
        self.assertEqual(1,len(c.fine_tuning.jobs))


if __name__=="__main__": unittest.main(verbosity=2)

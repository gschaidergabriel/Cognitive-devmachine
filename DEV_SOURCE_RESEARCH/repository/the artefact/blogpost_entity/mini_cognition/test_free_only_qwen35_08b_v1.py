#!/usr/bin/env python3
import builtins,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("launch08",HERE/"launch_together_qwen35_08b_v1.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class RepositoryAuthorityTests(unittest.TestCase):
    def test_active_control_beats_inbox_false_before_work_secret_and_provider_import(self):
        touched={"local_checks":0,"secret":0,"provider_import":0}
        original_import=builtins.__import__
        def local_tripwire():
            touched["local_checks"]+=1
            raise AssertionError("local paid-lane work reached before active-control rejection")
        def env_get(key,default=None):
            if key=="TOGETHER_API_KEY":
                touched["secret"]+=1
                raise AssertionError("secret lookup reached before active-control rejection")
            return default
        def import_tripwire(name,globals=None,locals=None,fromlist=(),level=0):
            if name=="together" or name.startswith("together."):
                touched["provider_import"]+=1
                raise AssertionError("provider import reached before active-control rejection")
            return original_import(name,globals,locals,fromlist,level)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            control=root/"control.json"
            inbox=root/"SUPERVISOR_INBOX.json"
            control.write_text(json.dumps({"status":"ACTIVE","mode":"FREE_ONLY","preserved_hard_rules":{"free_only":True,"together_forbidden":True}}),encoding="utf-8")
            inbox.write_text(json.dumps({"verified_updates":{"free_only":False}}),encoding="utf-8")
            with mock.patch.object(m,"EXECUTION_CONTROL_CANDIDATES",(control,)),mock.patch.object(m,"SUPERVISOR_POLICY",inbox),mock.patch.object(m,"local_checks",local_tripwire),mock.patch.object(m.os.environ,"get",side_effect=env_get),mock.patch("builtins.__import__",side_effect=import_tripwire),mock.patch.object(sys,"argv",["launcher"]):
                with self.assertRaisesRegex(SystemExit,"source=active_control"):
                    m.main()
        self.assertEqual(touched,{"local_checks":0,"secret":0,"provider_import":0})

    def test_inactive_control_does_not_claim_authority(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"control.json"
            p.write_text(json.dumps({"status":"SUPERSEDED","mode":"FREE_ONLY","preserved_hard_rules":{"free_only":True,"together_forbidden":True}}),encoding="utf-8")
            self.assertEqual(m.active_repository_execution_controls((p,)),[])

    def test_active_hard_together_forbidden_blocks_even_without_free_only_mode(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"control.json"
            p.write_text(json.dumps({"status":"ACTIVE","mode":"OTHER","preserved_hard_rules":{"free_only":False,"together_forbidden":True}}),encoding="utf-8")
            with self.assertRaisesRegex(SystemExit,"source=active_control"):
                m.assert_active_repository_provider_allowed((p,))

if __name__=="__main__":unittest.main()

#!/usr/bin/env python3
"""Offline regression suite for OMEGA external task bridge, no provider calls."""
import base64
import json
import os
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import omega_job_bridge as b

class BridgeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.root=Path(self.tmp.name)
  self.db=b.db_open(self.root/"bridge.sqlite")
  self.job=b.make_job("job-one","gabriel","image","Create homepage image","grid10:s1:t1",
                      created_at="2026-10-29T00:00:00Z")
 def tearDown(self):
  self.db.close();self.tmp.cleanup()
 def test_schema(self):
  b.validate_job(self.job,"gabriel")
  self.assertEqual(len(self.job["request_sha256"]),64)
  with self.assertRaisesRegex(ValueError,"REQUEST_DIGEST"):
   b.validate_job(dict(self.job,prompt="tampered"))
 def test_wrong_host(self):
  with self.assertRaisesRegex(ValueError,"OWNER_HOST"):
   b.enqueue(self.db,dict(self.job,machine_id="andreas-maco"),"gabriel")
  with self.assertRaisesRegex(ValueError,"OWNER_HOST"):
   b.enqueue(self.db,self.job,"andreas")
 def test_path_traversal(self):
  with self.assertRaisesRegex(ValueError,"JOB_ID"):
   b.make_job("../../escaped","gabriel","image","hello","grid10:a")
 def test_duplicate_conflict(self):
  self.assertEqual(b.enqueue(self.db,self.job,"gabriel"),"queued")
  self.assertEqual(b.enqueue(self.db,self.job,"gabriel"),"duplicate")
  different=b.make_job("job-one","gabriel","image","different","grid10:x")
  with self.assertRaisesRegex(ValueError,"JOB_ID_COLLISION"):
   b.enqueue(self.db,different,"gabriel")
 def test_atomic_claim(self):
  b.enqueue(self.db,self.job,"gabriel")
  self.assertEqual(b.claim(self.db,"gabriel",{"image"})["job_id"],"job-one")
  self.assertIsNone(b.claim(self.db,"gabriel",{"image"}))
  self.assertIsNone(b.claim(self.db,"andreas",{"image"}))
 def test_receipt_exact_binding(self):
  b.enqueue(self.db,self.job,"gabriel")
  result=b.run_one(self.db,"gabriel",self.root,executor=lambda j,p:{"ok":True})
  self.assertEqual(result["status"],"PASS")
  b.verify_result(result,self.job)
  with self.assertRaisesRegex(ValueError,"LINEAGE"):
   b.verify_result(dict(result,owner="andreas"),self.job)
  self.assertIsNone(b.run_one(self.db,"gabriel",self.root,executor=lambda j,p:{"ok":True}))
 def test_no_replay_on_provider_error(self):
  b.enqueue(self.db,self.job,"gabriel")
  def fail(*a):raise RuntimeError("failure")
  result=b.run_one(self.db,"gabriel",self.root,executor=fail)
  self.assertEqual(result["status"],"FAIL")
  self.assertIsNone(b.run_one(self.db,"gabriel",self.root,executor=fail))
 def test_network_unknown(self):
  import urllib.error
  b.enqueue(self.db,self.job,"gabriel")
  def fail(*a):raise urllib.error.URLError("uncertain")
  self.assertEqual(b.run_one(self.db,"gabriel",self.root,executor=fail)["status"],"UNKNOWN")
 def test_disabled_api_gates_before_claim(self):
  b.enqueue(self.db,self.job,"gabriel")
  with patch.dict(os.environ,{"OMEGA_JOB_API_ENABLED":"0","OPENAI_API_KEY":"dummy"}):
   self.assertIsNone(b.run_one(self.db,"gabriel",self.root))
  self.assertEqual(self.db.execute("SELECT state FROM jobs").fetchone()[0],"QUEUED")
 def test_mock_image_bytes(self):
  png=b"\x89PNG\r\n\x1a\n"+"bytes".encode()
  with patch.dict(os.environ,{"OPENAI_API_KEY":"fake","OMEGA_JOB_API_ENABLED":"1","OMEGA_JOB_CAPABILITIES":"image"}):
   out=b.execute_api(self.job,self.root,post=lambda *a:{"data":[{"b64_json":base64.b64encode(png).decode()}]})
  self.assertEqual((self.root/"job-one.png").read_bytes(),png)
  self.assertEqual(out["artifact"]["sha256"],b.hashlib.sha256(png).hexdigest())
 def test_mock_chat(self):
  job=b.make_job("txt","gabriel","chat","Hello","grid10:s")
  with patch.dict(os.environ,{"OPENAI_API_KEY":"fake","OMEGA_JOB_API_ENABLED":"1","OMEGA_JOB_CAPABILITIES":"chat"}):
   out=b.execute_api(job,self.root,post=lambda *a:{"id":"resp1","output":[{"type":"message","content":[{"type":"output_text","text":"hello"}]}]})
  self.assertEqual(out["text"],"hello")
 def test_git_publish_idempotent(self):
  b.enqueue(self.db,self.job,"gabriel")
  b.run_one(self.db,"gabriel",self.root,executor=lambda *a:{"ok":True})
  class FakeGithub(b.Github):
   def __init__(self):self.values={}
   def request(self,method,branch,path,body=None):
    k=(branch,path)
    if method=="GET":return self.values.get(k)
    if k in self.values:raise ValueError("overwritten")
    self.values[k]={"content":body["content"]};return {}
  gh=FakeGithub()
  self.assertEqual(gh.publish(self.db,"gabriel"),1)
  self.assertEqual(gh.publish(self.db,"gabriel"),0)
  self.assertEqual(len(gh.values),1)
 def grid(self,owner="gabriel"):
  p=self.root/"grid.sqlite"
  c=sqlite3.connect(p)
  c.executescript("CREATE TABLE meta(k TEXT,v TEXT);CREATE TABLE scopes(scope TEXT,summary_json TEXT,state_epoch INTEGER,evidence_count INTEGER);CREATE TABLE tasks(task_id TEXT,scope TEXT,priority INTEGER,capability TEXT,status TEXT,claimed_by TEXT,payload_json TEXT);")
  c.executemany("INSERT INTO meta VALUES(?,?)",[("epoch","4"),("generation","2")])
  c.execute("INSERT INTO scopes VALUES(?,?,?,?)",("s1",'{"focus":"image"}',4,1))
  payload={"schema":"OMEGA_GRID_EXTERNAL_TASK/v1","owner":owner,"machine_id":"ai-core-node",
           "kind":"image","prompt":"Create hero image","context_refs":[],"created_at":"2026-10-29T00:00:00Z"}
  c.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?)",("t1","s1",10,"omega-external","OPEN",None,json.dumps(payload)))
  c.commit();c.close();return p
 def test_readonly_grid_capsule(self):
  p=self.grid()
  self.assertEqual(b.capsule(p,"s1")["generation"],2)
  self.assertEqual(b.grid_ingest(self.db,p,"gabriel"),1)
  self.assertEqual(b.grid_ingest(self.db,p,"gabriel"),0)
 def test_cross_host_grid_task_denied(self):
  p=self.grid(owner="andreas")
  with self.assertRaisesRegex(ValueError,"GRID_OWNER_MISMATCH"):
   b.grid_tasks(p,"gabriel")
 def test_result_channel_only(self):
  p=self.grid()
  b.grid_ingest(self.db,p,"gabriel")
  b.run_one(self.db,"gabriel",self.root,executor=lambda *a:{"ok":True})
  calls=[]
  class FakeFabric:
   def __init__(self,path):pass
   def snapshot(self):return types.SimpleNamespace(generation=2,epoch=4,state_digest="stub")
   def emit_node_result(self,packet):calls.append(packet)
  fake=types.ModuleType("grid10_fabric")
  fake.Fabric=FakeFabric
  fake.result_packet=lambda node,snap,scope,payload:{"schema":"NODE_RESULT/v1","source_node_id":node,"scope":scope,"payload":payload,"packet_digest":"stub"}
  with patch.dict(sys.modules,{"grid10_fabric":fake}):
   self.assertEqual(b.grid_reentry(self.db,p,"gabriel"),1)
   self.assertEqual(b.grid_reentry(self.db,p,"gabriel"),0)
  self.assertEqual(len(calls),1)
  self.assertEqual(calls[0]["payload"]["authority"],"RESULT_CHANNEL_ONLY")

if __name__=="__main__":
 unittest.main()

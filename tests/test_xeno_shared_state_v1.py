import sqlite3,tempfile,time,unittest
from dataclasses import replace
from pathlib import Path
from tools.xeno_shared_state_v1 import *
A="a"*64
class T(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.path=Path(self.t.name)/"s.sqlite"; self.secret=b"x"*32
  self.f=SharedStateFabric(self.path,fabric_id="f",authority_secret=self.secret)
  self.f.initialize_s1({"work":[{"work_id":"low","priority":1,"status":"OPEN","required_capabilities":["REASON"]},{"work_id":"high","priority":9,"status":"OPEN","required_capabilities":["REASON"]},{"work_id":"gpu","priority":99,"status":"OPEN","required_capabilities":["GPU"]}]})
  self.nodes=[]
 def tearDown(self):
  for n in self.nodes:n.close()
  self.f.close();self.t.cleanup()
 def adm(self,n,c=("REASON",)):return self.f.mint_admission(node_id=n,admission_id="a:"+n,capabilities=c,controller_authority_digest=A)
 def node(self,n,c=("REASON",)):
  x=self.f.admit_node(self.adm(n,c)); self.nodes.append(x); return x
 def controller(self):return SharedStateFabric(self.path,fabric_id="f",authority_secret=self.secret)
 def test_boot_read_only(self):
  n=self.node("n"); s=self.f.snapshot(); b=n.autonomous_boot(); self.assertEqual(b["selected_work"]["work_id"],"high"); self.assertEqual(b["s1_access"],"READ_ONLY"); self.assertFalse(hasattr(n,"coordinator_commit")); self.assertFalse(hasattr(n,"_f")); self.assertEqual(s,self.f.snapshot())
 def test_read_only_db_rejects_write(self):
  n=self.node("n")
  with self.assertRaises(sqlite3.OperationalError):n._reader.db.execute("UPDATE s1 SET epoch=999 WHERE singleton=1")
  self.assertEqual(self.f.snapshot().epoch,1)
 def test_result_is_signed_ephemeral(self):
  n=self.node("n"); s=n.snapshot(); r=n.make_result(work_id="high",snapshot=s,payload={"x":1}); self.assertFalse(r["s1_write"]); self.assertEqual(len(r["result_auth_mac"]),64); self.assertEqual(s,self.f.snapshot())
 def test_admission_mac_and_drift(self):
  a=self.adm("n"); bad=dict(a,admission_mac="0"*64); self.assertRaises(ValueError,self.f.admit_node,bad); self.nodes.append(self.f.admit_node(a)); self.assertRaises(ValueError,self.f.admit_node,self.adm("n",("REASON","GPU")))
 def test_ordinary_cannot_lease(self):self.node("n"); self.assertRaises(ValueError,self.f.issue_coordinator_lease,node_id="n",scope="global",ttl_seconds=60)
 def coord(self,n="c"):
  self.node(n,("REASON","COORDINATE")); return self.f.issue_coordinator_lease(node_id=n,scope="global",ttl_seconds=60)
 def test_lease_commit_and_stale_cas(self):
  l=self.coord(); s=self.f.snapshot(); x=self.f.coordinator_commit(lease=l,expected_epoch=s.epoch,expected_state_digest=s.state_digest,payload={"work":[]}); self.assertEqual(x["status"],"COMMITTED"); self.assertRaises(StaleState,self.f.coordinator_commit,lease=l,expected_epoch=s.epoch,expected_state_digest=s.state_digest,payload={"work":[]})
 def test_forged_replaced_expired_lease(self):
  l=self.coord("c1"); self.assertRaises(LeaseRejected,self.f.assert_lease,replace(l,token_mac="0"*64)); self.node("c2",("REASON","COORDINATE")); n=self.f.issue_coordinator_lease(node_id="c2",scope="global",ttl_seconds=60); self.assertRaises(LeaseRejected,self.f.assert_lease,l); self.f.assert_lease(n)
  e=self.f.issue_coordinator_lease(node_id="c2",scope="global",ttl_seconds=.01); time.sleep(.02); self.assertRaises(LeaseRejected,self.f.assert_lease,e)
 def test_replaced_coordinator_cannot_commit(self):
  l1=self.coord("c1"); s=self.f.snapshot(); self.node("c2",("REASON","COORDINATE")); self.f.issue_coordinator_lease(node_id="c2",scope="global",ttl_seconds=60)
  self.assertRaises(LeaseRejected,self.f.coordinator_commit,lease=l1,expected_epoch=s.epoch,expected_state_digest=s.state_digest,payload={"work":[]}); self.assertEqual(self.f.snapshot(),s)
 def test_result_duplicate_stale_and_auth(self):
  n=self.node("n"); l=self.coord(); s=n.snapshot(); r=n.make_result(work_id="high",snapshot=s,payload={"v":1})
  forged=dict(r,result_auth_mac="0"*64); self.assertRaises(ValueError,self.f.admit_result,lease=l,result=forged)
  self.assertEqual(self.f.admit_result(lease=l,result=r)["status"],"ADMITTED_CANDIDATE_ONLY"); self.assertRaises(DuplicateResult,self.f.admit_result,lease=l,result=r)
  self.f.coordinator_commit(lease=l,expected_epoch=s.epoch,expected_state_digest=s.state_digest,payload={"work":[]}); l2=self.f.issue_coordinator_lease(node_id="c",scope="global",ttl_seconds=60); late=n.make_result(work_id="high",snapshot=s,payload={"v":2}); self.assertRaises(StaleState,self.f.admit_result,lease=l2,result=late)
 def test_result_node_identity_bound(self):
  n=self.node("n"); l=self.coord(); s=n.snapshot(); r=n.make_result(work_id="high",snapshot=s,payload={"v":3}); fake=dict(r,node_id="ghost")
  self.assertRaises(ValueError,self.f.admit_result,lease=l,result=fake)
 def test_two_controller_replacement_observed(self):
  self.node("c1",("COORDINATE",)); self.node("c2",("COORDINATE",)); c2=self.controller()
  try:
   l1=self.f.issue_coordinator_lease(node_id="c1",scope="global",ttl_seconds=60); l2=c2.issue_coordinator_lease(node_id="c2",scope="global",ttl_seconds=60)
   self.assertRaises(LeaseRejected,self.f.assert_lease,l1); c2.assert_lease(l2)
  finally:c2.close()
if __name__=="__main__":unittest.main()

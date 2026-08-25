import tempfile,time,unittest
from dataclasses import replace
from pathlib import Path
from tools.xeno_shared_state_v1 import *
A="a"*64
class T(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.f=SharedStateFabric(Path(self.t.name)/"s.sqlite",fabric_id="f",authority_secret=b"x"*32)
  self.f.initialize_s1({"work":[{"work_id":"low","priority":1,"status":"OPEN","required_capabilities":["REASON"]},{"work_id":"high","priority":9,"status":"OPEN","required_capabilities":["REASON"]},{"work_id":"gpu","priority":99,"status":"OPEN","required_capabilities":["GPU"]}]})
 def tearDown(self):self.f.close();self.t.cleanup()
 def adm(self,n,c=("REASON",)):return self.f.mint_admission(node_id=n,admission_id="a:"+n,capabilities=c,controller_authority_digest=A)
 def test_boot_read_only(self):
  n=self.f.admit_node(self.adm("n")); s=self.f.snapshot(); b=n.autonomous_boot(); self.assertEqual(b["selected_work"]["work_id"],"high"); self.assertEqual(b["s1_access"],"READ_ONLY"); self.assertFalse(hasattr(n,"coordinator_commit")); self.assertEqual(s,self.f.snapshot())
 def test_result_ephemeral(self):
  n=self.f.admit_node(self.adm("n")); s=n.snapshot(); r=n.make_result(work_id="high",snapshot=s,payload={"x":1}); self.assertFalse(r["s1_write"]); self.assertEqual(s,self.f.snapshot())
 def test_admission_mac_and_drift(self):
  a=self.adm("n"); bad=dict(a,admission_mac="0"*64); self.assertRaises(ValueError,self.f.admit_node,bad); self.f.admit_node(a); self.assertRaises(ValueError,self.f.admit_node,self.adm("n",("REASON","GPU")))
 def test_ordinary_cannot_lease(self):self.f.admit_node(self.adm("n")); self.assertRaises(ValueError,self.f.issue_coordinator_lease,node_id="n",scope="global",ttl_seconds=60)
 def coord(self,n="c"):
  self.f.admit_node(self.adm(n,("REASON","COORDINATE"))); return self.f.issue_coordinator_lease(node_id=n,scope="global",ttl_seconds=60)
 def test_lease_commit_and_stale_cas(self):
  l=self.coord(); s=self.f.snapshot(); x=self.f.coordinator_commit(lease=l,expected_epoch=s.epoch,expected_state_digest=s.state_digest,payload={"work":[]}); self.assertEqual(x["status"],"COMMITTED"); self.assertRaises(StaleState,self.f.coordinator_commit,lease=l,expected_epoch=s.epoch,expected_state_digest=s.state_digest,payload={"work":[]})
 def test_forged_replaced_expired_lease(self):
  l=self.coord("c1"); self.assertRaises(LeaseRejected,self.f.assert_lease,replace(l,token_mac="0"*64)); self.f.admit_node(self.adm("c2",("REASON","COORDINATE"))); n=self.f.issue_coordinator_lease(node_id="c2",scope="global",ttl_seconds=60); self.assertRaises(LeaseRejected,self.f.assert_lease,l); self.f.assert_lease(n)
  e=self.f.issue_coordinator_lease(node_id="c2",scope="global",ttl_seconds=.01); time.sleep(.02); self.assertRaises(LeaseRejected,self.f.assert_lease,e)
 def test_result_duplicate_and_stale(self):
  n=self.f.admit_node(self.adm("n")); l=self.coord(); s=n.snapshot(); r=n.make_result(work_id="high",snapshot=s,payload={"v":1}); self.assertEqual(self.f.admit_result(lease=l,result=r)["status"],"ADMITTED_CANDIDATE_ONLY"); self.assertRaises(DuplicateResult,self.f.admit_result,lease=l,result=r); self.f.coordinator_commit(lease=l,expected_epoch=s.epoch,expected_state_digest=s.state_digest,payload={"work":[]}); l2=self.f.issue_coordinator_lease(node_id="c",scope="global",ttl_seconds=60); late=n.make_result(work_id="high",snapshot=s,payload={"v":2}); self.assertRaises(StaleState,self.f.admit_result,lease=l2,result=late)
if __name__=="__main__":unittest.main()

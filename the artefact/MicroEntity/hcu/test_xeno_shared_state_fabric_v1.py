import hashlib, sqlite3, unittest
import xeno_shared_state_fabric_v1 as f
H=lambda b: hashlib.sha256(b).hexdigest(); CAPA=H(b'a'); CAPB=H(b'b'); POL=H(b'p'); ELIG=H(b'e'); PAY=H(b'pay')
def state(): return {'work_items':[{'work_id':'low','status':'OPEN','priority':1,'required_capabilities':[],'payload_ref':'p:low'},{'work_id':'high','status':'OPEN','priority':9,'required_capabilities':['reason'],'payload_ref':'p:high'},{'work_id':'claimed','status':'CLAIMED','priority':99,'required_capabilities':[],'payload_ref':'p:c'}],'hyperposition':{'branches':['a','b']},'gwt':{'broadcast_epoch':0}}
class T(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(':memory:'); self.db.execute('PRAGMA foreign_keys=ON'); f.install_schema(self.db)
  self.s0=f.controller_initialize_scope(self.db,scope='global',generation=7,state=state())
  f.controller_admit_node(self.db,node_id='a',generation=7,capability_binding_sha256=CAPA,policy_binding_sha256=POL)
  f.controller_admit_node(self.db,node_id='b',generation=7,capability_binding_sha256=CAPB,policy_binding_sha256=POL); self.db.commit()
 def boot(self,now=10): return f.autonomous_boot(self.db,node_id='a',generation=7,capability_binding_sha256=CAPA,policy_binding_sha256=POL,capabilities=['reason'],scope='global',now_ns=now)
 def lease(self,node='b',lid='l1',issued=10,expires=100):
  s=f.read_snapshot(self.db,scope='global',generation=7)
  return f.controller_grant_lease(self.db,lease_id=lid,scope='global',node_id=node,generation=7,expected_epoch=s['epoch'],expected_state_sha256=s['state_sha256'],eligibility_sha256=ELIG,policy_binding_sha256=POL,issued_at_ns=issued,expires_at_ns=expires)
 def test_boot_read_only(self):
  b=self.boot(); self.assertTrue(b['read_only_s1']); self.assertEqual(b['selected_work_id'],'high'); self.assertIsNone(b['coordinator_lease_id']); self.assertEqual(f.read_snapshot(self.db,scope='global',generation=7)['epoch'],0)
 def test_result_requires_coordinator_and_ephemeral(self):
  b=self.boot()
  with self.assertRaisesRegex(f.SharedStateFabricError,'NO_VALID_COORDINATOR_ROUTE'): f.make_node_result(self.db,boot=b,result_id='r',work_id='high',payload_ref='r:x',payload_sha256=PAY,now_ns=11)
  self.lease(); b=self.boot(12); r=f.make_node_result(self.db,boot=b,result_id='r',work_id='high',payload_ref='r:x',payload_sha256=PAY,now_ns=12); self.assertEqual(r['coordinator_node_id'],'b')
  names={x[0] for x in self.db.execute("select name from sqlite_master where type='table'")}; self.assertNotIn('xeno_node_results',names)
 def test_no_lease_no_write(self):
  s=f.read_snapshot(self.db,scope='global',generation=7)
  with self.assertRaisesRegex(f.SharedStateFabricError,'NO_VALID_COORDINATOR_LEASE'): f.coordinator_commit(self.db,coordinator_node_id='a',coordinator_lease_id='fake',scope='global',generation=7,expected_epoch=s['epoch'],expected_state_sha256=s['state_sha256'],new_state=state(),now_ns=12)
 def test_cas_and_stale_result(self):
  self.lease(); b=self.boot(12); r=f.make_node_result(self.db,boot=b,result_id='r',work_id='high',payload_ref='r:x',payload_sha256=PAY,now_ns=12); s=f.validate_node_result(self.db,result=r,coordinator_node_id='b',coordinator_lease_id='l1',now_ns=12)
  ns=state(); ns['work_items'][1]['status']='DONE'; c=f.coordinator_commit(self.db,coordinator_node_id='b',coordinator_lease_id='l1',scope='global',generation=7,expected_epoch=s['epoch'],expected_state_sha256=s['state_sha256'],new_state=ns,now_ns=13); self.assertEqual(c['epoch'],1)
  with self.assertRaisesRegex(f.SharedStateFabricError,'STALE_NODE_RESULT_EPOCH'): f.validate_node_result(self.db,result=r,coordinator_node_id='b',coordinator_lease_id='l1',now_ns=14)
 def test_replacement_rejoin_and_scopes(self):
  self.lease(lid='old',expires=20); s=f.read_snapshot(self.db,scope='global',generation=7); f.controller_grant_lease(self.db,lease_id='new',scope='global',node_id='a',generation=7,expected_epoch=s['epoch'],expected_state_sha256=s['state_sha256'],eligibility_sha256=ELIG,policy_binding_sha256=POL,issued_at_ns=21,expires_at_ns=50); self.assertEqual(self.boot(22)['coordinator_node_id'],'a')
  f.controller_initialize_scope(self.db,scope='branch:a',generation=7,state={'work_items':[]}); self.db.commit(); bs=f.read_snapshot(self.db,scope='branch:a',generation=7); x=f.controller_grant_lease(self.db,lease_id='branch',scope='branch:a',node_id='b',generation=7,expected_epoch=bs['epoch'],expected_state_sha256=bs['state_sha256'],eligibility_sha256=ELIG,policy_binding_sha256=POL,issued_at_ns=22,expires_at_ns=60); self.assertEqual(x['scope'],'branch:a')
 def test_same_scope_concurrent_rejected(self):
  self.lease()
  s=f.read_snapshot(self.db,scope='global',generation=7)
  with self.assertRaisesRegex(f.SharedStateFabricError,'ACTIVE_COORDINATOR_ALREADY_EXISTS'): f.controller_grant_lease(self.db,lease_id='l2',scope='global',node_id='a',generation=7,expected_epoch=s['epoch'],expected_state_sha256=s['state_sha256'],eligibility_sha256=ELIG,policy_binding_sha256=POL,issued_at_ns=11,expires_at_ns=90)
if __name__=='__main__': unittest.main()

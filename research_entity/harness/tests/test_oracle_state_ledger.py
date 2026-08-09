import json, os, sys, tempfile, threading, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference"))
from oracle_state_ledger import (
    OracleStateLedger, Mutation, h,
    StaleEpoch, IdempotencyConflict, TamperDetected,
)

class OracleLedgerTests(unittest.TestCase):
    def test_typed_set_and_order(self):
        self.assertEqual(h({"$kind":"set","items":[3,1,1,2]}), h({"$kind":"set","items":[2,3,1]}))
        self.assertNotEqual(h({"$kind":"ordered","items":[1,2]}), h({"$kind":"ordered","items":[2,1]}))

    def test_semantic_vs_version_identity(self):
        a=OracleStateLedger(); b=OracleStateLedger()
        a.commit(event_id="a1",idem="a1",base_epoch=0,event_type="SET",writer="t",
                 mutations=[Mutation("w","x",1),Mutation("w","y",2)])
        b.commit(event_id="b1",idem="b1",base_epoch=0,event_type="SET",writer="t",
                 mutations=[Mutation("w","x",1)])
        b.commit(event_id="b2",idem="b2",base_epoch=1,event_type="SET",writer="t",
                 mutations=[Mutation("w","y",2)])
        self.assertEqual(a.semantic_state_hash,b.semantic_state_hash)
        self.assertNotEqual(a.state_version_hash,b.state_version_hash)
        a.close(); b.close()

    def test_execution_trace_separation(self):
        a=OracleStateLedger(); b=OracleStateLedger()
        kw=dict(event_id="e",idem="i",base_epoch=0,event_type="X",writer="t",
                mutations=[Mutation("w","x",1)],provenance={"p":1},source={"s":1})
        a.commit(**kw,execution={"attempt":1})
        b.commit(**kw,execution={"attempt":2})
        self.assertEqual(a.semantic_state_hash,b.semantic_state_hash)
        self.assertNotEqual(a.trace_root_hash,b.trace_root_hash)
        a.close(); b.close()

    def test_idempotency_payload_collision(self):
        l=OracleStateLedger()
        kw=dict(event_id="e",idem="i",base_epoch=0,event_type="X",writer="t",
                mutations=[Mutation("w","x",1)],provenance={"p":1},source={"s":1})
        l.commit(**kw)
        r=l.commit(**{**kw,"writer":"retry"},execution={"attempt":2})
        self.assertEqual(r["status"],"IDEMPOTENT_REPLAY")
        with self.assertRaises(IdempotencyConflict):
            l.commit(event_id="e",idem="i",base_epoch=0,event_type="X",writer="t",
                     mutations=[Mutation("w","x",2)],provenance={"p":1},source={"s":1})
        self.assertEqual(l.get("w","x")["value"],1)
        l.close()

    def test_stale_fail_closed(self):
        l=OracleStateLedger()
        l.commit(event_id="e",idem="e",base_epoch=0,event_type="X",writer="t",mutations=[Mutation("w","x",1)])
        before=(l.semantic_state_hash,l.state_version_hash,l.trace_root_hash)
        with self.assertRaises(StaleEpoch):
            l.commit(event_id="s",idem="s",base_epoch=0,event_type="X",writer="t",mutations=[Mutation("w","y",2)])
        self.assertEqual(before,(l.semantic_state_hash,l.state_version_hash,l.trace_root_hash))
        l.close()

    def test_fault_rollback(self):
        l=OracleStateLedger()
        before=(l.epoch,l.semantic_state_hash,l.state_version_hash,l.trace_root_hash)
        with self.assertRaises(RuntimeError):
            l.commit(event_id="f",idem="f",base_epoch=0,event_type="F",writer="t",
                     mutations=[Mutation("w","f",9)],fault_after="event")
        self.assertEqual(before,(l.epoch,l.semantic_state_hash,l.state_version_hash,l.trace_root_hash))
        self.assertIsNone(l.get("w","f"))
        l.close()

    def test_replay_verify(self):
        l=OracleStateLedger()
        for i in range(20):
            l.commit(event_id=f"e{i}",idem=f"i{i}",base_epoch=i,event_type="T",writer="t",
                     mutations=[Mutation(["world","gwt","memory"][i%3],f"k{i%5}",{"i":i})],
                     provenance={"fixture":"golden"},source={"baseline":"H1"},execution={"attempt":i})
        r=OracleStateLedger.replay(l.export_events())
        self.assertEqual((l.semantic_state_hash,l.state_version_hash,l.trace_root_hash,l.domain_epochs()),
                         (r.semantic_state_hash,r.state_version_hash,r.trace_root_hash,r.domain_epochs()))
        self.assertEqual(l.verify()["status"],"PASS")
        l.close(); r.close()

    def test_snapshot_exact_restore_and_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            l=OracleStateLedger()
            l.commit(event_id="e",idem="e",base_epoch=0,event_type="X",writer="t",
                     mutations=[Mutation("w","x",{"v":1})],provenance={"p":1})
            l.snapshot("s")
            p=os.path.join(td,"s.json"); l.export_snapshot("s",p)
            r=OracleStateLedger.restore_snapshot(p,os.path.join(td,"restore.db"))
            self.assertEqual((l.semantic_state_hash,l.state_version_hash,l.trace_root_hash),
                             (r.semantic_state_hash,r.state_version_hash,r.trace_root_hash))
            r.close()
            env=json.loads(Path(p).read_text()); env["payload"]["events"][0]["mutations"][0]["value"]={"v":2}
            Path(p).write_text(json.dumps(env))
            with self.assertRaises(TamperDetected):
                OracleStateLedger.restore_snapshot(p,os.path.join(td,"bad.db"))
            l.close()

    def test_two_writer_same_request(self):
        with tempfile.TemporaryDirectory() as td:
            db=os.path.join(td,"l.db")
            seed=OracleStateLedger(db); seed.close()
            barrier=threading.Barrier(2); out=[]; err=[]
            def w(name):
                try:
                    l=OracleStateLedger(db); barrier.wait(5)
                    r=l.commit(event_id="e",idem="i",base_epoch=0,event_type="X",writer=name,
                               mutations=[Mutation("w","x",1)],provenance={"p":"same"},source={"s":"same"},
                               execution={"writer":name})
                    out.append(r["status"]); l.close()
                except Exception as exc:
                    err.append(type(exc).__name__)
            ts=[threading.Thread(target=w,args=(f"w{i}",),daemon=True) for i in range(2)]
            [t.start() for t in ts]; [t.join(10) for t in ts]
            self.assertFalse(any(t.is_alive() for t in ts))
            self.assertEqual(err,[])
            self.assertEqual(sorted(out),["COMMITTED","IDEMPOTENT_REPLAY"])
            l=OracleStateLedger(db)
            self.assertEqual(l.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],1)
            l.close()

if __name__=="__main__":
    unittest.main(verbosity=2)

import math, os, tempfile, threading, unittest
from pathlib import Path

from .state_ledger import StateLedger, StaleEpoch, h
from .effect_gateway_runtime import SandboxEffectGateway, SandboxWriteProposal, EffectDenied
from .unifieddb_query_plane import UnifiedDBQueryPlane, QuerySpec

class AdversarialSandboxTests(unittest.TestCase):
    def test_concurrent_ledger_cas_allows_exactly_one_same_epoch_writer(self):
        fd,path=tempfile.mkstemp(); os.close(fd)
        try:
            seed=StateLedger(path); seed.close()
            barrier=threading.Barrier(8); results=[]; lock=threading.Lock()
            def worker(i):
                l=StateLedger(path); base=l.epoch; barrier.wait()
                try:
                    r=l.append_event(event_id=f'e{i}',idem=f'e{i}',base_epoch=base,event_type='RACE',writer=f'w{i}',ops=[{'op':'SET','domain':'race','key':str(i),'value':i,'epistemic':'KNOWN','status':'CURRENT'}]); x=r['status']
                except StaleEpoch: x='STALE'
                finally: l.close()
                with lock: results.append(x)
            ts=[threading.Thread(target=worker,args=(i,)) for i in range(8)]
            [t.start() for t in ts]; [t.join() for t in ts]
            self.assertEqual(results.count('COMMITTED'),1,results); self.assertEqual(results.count('STALE'),7,results)
            l=StateLedger(path); self.assertEqual(l.epoch,1); self.assertEqual(len(l.materialized()),1); l.close()
        finally:
            for p in (path,path+'-wal',path+'-shm'):
                if os.path.exists(p): os.unlink(p)

    def test_concurrent_same_effect_id_has_single_physical_winner(self):
        fd,db=tempfile.mkstemp(); os.close(fd)
        with tempfile.TemporaryDirectory() as td:
            try:
                seed=StateLedger(db); seed.close(); p=SandboxWriteProposal('same','x.txt','payload'); barrier=threading.Barrier(2); results=[]; lock=threading.Lock()
                def run():
                    l=StateLedger(db); g=SandboxEffectGateway(l,td); q=g.issue_permit(p); barrier.wait()
                    try: x=g.execute(p,q)['status']
                    except (StaleEpoch,EffectDenied) as e: x=type(e).__name__
                    finally: l.close()
                    with lock: results.append(x)
                t1=threading.Thread(target=run); t2=threading.Thread(target=run); t1.start(); t2.start(); t1.join(); t2.join()
                self.assertEqual(results.count('COMMITTED_VERIFIED'),1,results); self.assertEqual(Path(td,'x.txt').read_text(),'payload')
                l=StateLedger(db); rec=StateLedger.replay(l.export_events()); self.assertEqual(rec.semantic_state_hash,l.semantic_state_hash); self.assertEqual(rec.trace_root_hash,l.trace_root_hash); rec.close(); l.close()
            finally:
                for pth in (db,db+'-wal',db+'-shm'):
                    if os.path.exists(pth): os.unlink(pth)

    def test_symlink_escape_is_denied_before_mutation(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            os.symlink(outside,Path(root,'link'))
            l=StateLedger(); g=SandboxEffectGateway(l,root); p=SandboxWriteProposal('e','link/escape.txt','no'); q=g.issue_permit(p)
            with self.assertRaises(EffectDenied): g.execute(p,q)
            self.assertFalse(Path(outside,'escape.txt').exists()); self.assertEqual(l.epoch,0); l.close()

    def test_path_escape_corpus_is_fail_closed(self):
        bad=['../x','../../x','a/../../../x','/tmp/x','a/../../../../etc/passwd']
        with tempfile.TemporaryDirectory() as root:
            l=StateLedger(); g=SandboxEffectGateway(l,root)
            for i,path in enumerate(bad):
                p=SandboxWriteProposal(f'e{i}',path,'x'); q=g.issue_permit(p)
                with self.subTest(path=path):
                    with self.assertRaises(EffectDenied): g.execute(p,q)
            self.assertEqual(l.epoch,0); l.close()

    def test_nonfinite_numbers_never_enter_canonical_state(self):
        for bad in (float('nan'),float('inf'),float('-inf')):
            l=StateLedger()
            with self.subTest(value=bad):
                with self.assertRaises(ValueError): l.append_event(event_id='e',idem='e',base_epoch=0,event_type='X',writer='t',ops=[{'op':'SET','domain':'x','key':'k','value':bad,'epistemic':'KNOWN','status':'CURRENT'}])
                self.assertEqual(l.epoch,0)
            l.close()

    def test_typed_set_hash_is_order_invariant(self):
        a={'$kind':'set','items':[{'x':2},{'x':1},{'x':2}]}; b={'$kind':'set','items':[{'x':1},{'x':2}]}; self.assertEqual(h(a),h(b))

    def test_query_resource_bounds_reject_extreme_limit(self):
        l=StateLedger(); p=UnifiedDBQueryPlane(l)
        with self.assertRaises(ValueError): p.query(QuerySpec('q',limit=5000))
        l.close()

    def test_randomized_replay_chain_stays_exact(self):
        l=StateLedger()
        for i in range(200):
            l.append_event(event_id=f'e{i}',idem=f'e{i}',base_epoch=l.epoch,event_type='FUZZ',writer='deterministic-fuzz',ops=[{'op':'SET','domain':f'd{i%7}','key':f'k{i%19}','value':{'i':i,'set':{'$kind':'set','items':[i%5,(i+1)%5]}},'epistemic':'KNOWN' if i%11 else 'UNKNOWN','status':'CURRENT'}])
        x=StateLedger.replay(l.export_events()); self.assertEqual(x.epoch,l.epoch); self.assertEqual(x.semantic_state_hash,l.semantic_state_hash); self.assertEqual(x.trace_root_hash,l.trace_root_hash); x.close(); l.close()

if __name__=='__main__': unittest.main()

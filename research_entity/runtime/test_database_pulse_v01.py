import json, sqlite3, unittest
from pathlib import Path
from database_pulse_runtime_v01 import DatabasePulseEngine, StageResult

HERE=Path(__file__).resolve().parent
U10=(HERE/'RAE_UNIFIEDDB_V10_POSSIBILITY_COMPILER.sql').read_text(encoding='utf-8')
PULSE_SCHEMA=(HERE/'RAE_DATABASE_PULSE_V0_1.sql').read_text(encoding='utf-8')

def add_field(c, epoch, src, graph, status='BUILDING', candidate='c1', anchor='a1'):
    c.execute("INSERT INTO clay_possibility_field_epochs VALUES(?,?,?,?,?,?,?,?,?,?)",
              (epoch,src,graph,'comp','in','field',status,'t',None,'{}'))
    fid=f'f{epoch}:{anchor}'
    c.execute("INSERT INTO clay_possibility_anchor_fields VALUES(?,?,?,?,?,?,?,?,?,?,?)",
              (fid,epoch,anchor,'test',1,0,0.1,'in','out','CURRENT','t'))
    c.execute("INSERT OR IGNORE INTO clay_possibility_ordinals VALUES(?,?,?,?,?)",(candidate,1,src,None,'CURRENT'))
    c.execute("INSERT INTO clay_possibility_field_members VALUES(?,?,?,?,?,?,?,?,?,?)",
              (fid,candidate,1,0,1.0,1.0,1,0,'[]','{}'))

class T(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(':memory:'); self.c.execute('PRAGMA foreign_keys=ON'); self.c.executescript(U10); self.c.executescript(PULSE_SCHEMA)
        self.c.execute("INSERT INTO clay_possibility_compiler_specs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                       ('comp','1',2,4,100,'{}','{}','{}','{}','hash','CURRENT','t'))
        add_field(self.c,1,1,1,'CURRENT'); self.c.commit()
        self.e=DatabasePulseEngine(self.c)
    def tearDown(self): self.c.close()

    def manifest(self, mid='m1', parent_src=1, src=2, parent_graph=1, graph=1, changed=['x'], anchors=['a1']):
        self.c.execute("INSERT INTO database_pulse_change_manifests VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (mid,parent_src,src,parent_graph,graph,json.dumps(changed),json.dumps(anchors),1,'{}','hash','VERIFIED','t')); self.c.commit()

    def invalid(self, iid='i1', src=1, graph=1, mode='FACET_ONLY', anchors=['a1']):
        self.c.execute("INSERT INTO clay_possibility_invalidation_queue VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (iid,src,graph,'x','CHANGE',json.dumps(anchors),mode,'[]','t',None,'OPEN')); self.c.commit()

    def test_noop_zero_model(self):
        r=self.e.pulse_once(pulse_id='p0',source_epoch=1,graph_epoch=1,timestamp='t')
        self.assertEqual((r['state'],r['plan_class'],r['model_call_count']),('NOOP','NOOP',0))
    def test_unexplained_epoch_drift_fails(self):
        r=self.e.pulse_once(pulse_id='p1',source_epoch=2,graph_epoch=1,timestamp='t')
        self.assertEqual(r['state'],'FAILED'); self.assertIn('UNEXPLAINED',r['reason'])
        self.assertEqual(self.c.execute("SELECT field_epoch FROM clay_possibility_field_epochs WHERE status='CURRENT'").fetchone()[0],1)
    def test_highest_dirty_repair_wins(self):
        self.invalid('i1',1,1,'FACET_ONLY'); self.invalid('i2',1,1,'ANCHOR_RECOMPILE',['a2'])
        p=self.e.plan(pulse_id='p',source_epoch=1,graph_epoch=1)
        self.assertEqual(p.plan_class,'ANCHOR_RECOMPILE'); self.assertEqual(set(p.affected_anchors),{'a1','a2'})
    def test_graph_epoch_mismatch_fails(self):
        self.invalid('i1',1,2,'ANCHOR_RECOMPILE')
        p=self.e.plan(pulse_id='p',source_epoch=1,graph_epoch=1)
        self.assertEqual(p.plan_class,'FAIL_CLOSED')
    def test_publish_shadow_and_close_dirty(self):
        self.invalid('i1',2,1,'ANCHOR_RECOMPILE'); self.manifest()
        def stage(c,p):
            add_field(c,2,2,1,'BUILDING'); c.commit()
            return StageResult(2,model_call_count=0,state_transition_count=2,evidence={'compiler':'fixture'})
        r=self.e.pulse_once(pulse_id='p2',source_epoch=2,graph_epoch=1,stage_fn=stage,timestamp='t')
        self.assertEqual(r['state'],'PUBLISHED')
        self.assertEqual(self.c.execute("SELECT field_epoch FROM clay_possibility_field_epochs WHERE status='CURRENT'").fetchone()[0],2)
        self.assertEqual(self.c.execute("SELECT status FROM clay_possibility_field_epochs WHERE field_epoch=1").fetchone()[0],'SUPERSEDED')
        self.assertEqual(self.c.execute("SELECT status FROM clay_possibility_invalidation_queue WHERE invalidation_id='i1'").fetchone()[0],'DONE')
    def test_empty_shadow_quarantined_preserves_lkg(self):
        self.invalid('i1',2,1,'FIELD_REBUILD')
        def stage(c,p):
            c.execute("INSERT INTO clay_possibility_field_epochs VALUES(?,?,?,?,?,?,?,?,?,?)",(2,2,1,'comp','in','field','BUILDING','t',None,'{}')); c.commit()
            return StageResult(2)
        r=self.e.pulse_once(pulse_id='p3',source_epoch=2,graph_epoch=1,stage_fn=stage,timestamp='t')
        self.assertEqual(r['state'],'QUARANTINED')
        self.assertEqual(self.c.execute("SELECT field_epoch FROM clay_possibility_field_epochs WHERE status='CURRENT'").fetchone()[0],1)
        self.assertEqual(self.c.execute("SELECT status FROM clay_possibility_invalidation_queue WHERE invalidation_id='i1'").fetchone()[0],'OPEN')
    def test_head_race_preserves_newer_current(self):
        self.invalid('i1',2,1,'ANCHOR_RECOMPILE'); self.manifest()
        def stage(c,p):
            add_field(c,2,2,1,'BUILDING',candidate='c1')
            c.execute("UPDATE clay_possibility_field_epochs SET status='SUPERSEDED' WHERE field_epoch=1")
            add_field(c,99,2,1,'CURRENT',candidate='c1',anchor='other')
            c.commit(); return StageResult(2)
        r=self.e.pulse_once(pulse_id='p4',source_epoch=2,graph_epoch=1,stage_fn=stage,timestamp='t')
        self.assertEqual(r['state'],'QUARANTINED')
        self.assertEqual(self.c.execute("SELECT field_epoch FROM clay_possibility_field_epochs WHERE status='CURRENT'").fetchone()[0],99)
    def test_epoch_advance_without_manifest_escalates_full_rebuild(self):
        self.invalid('i1',2,1,'FACET_ONLY')
        p=self.e.plan(pulse_id='px',source_epoch=2,graph_epoch=1)
        self.assertEqual(p.plan_class,'FIELD_REBUILD')
        self.assertEqual(p.reason,'NO_VERIFIED_COMPLETE_CHANGE_MANIFEST')
    def test_verified_manifest_allows_scoped_repair(self):
        self.invalid('i1',2,1,'FACET_ONLY'); self.manifest(anchors=['a1'])
        p=self.e.plan(pulse_id='py',source_epoch=2,graph_epoch=1)
        self.assertEqual(p.plan_class,'ANCHOR_RECOMPILE')
        self.assertEqual(p.change_manifest_id,'m1')
    def test_truncated_witness_forces_anchor_recompile(self):
        self.c.execute("UPDATE clay_possibility_field_members SET witness_truncated=1 WHERE field_id='f1:a1'"); self.c.commit()
        self.invalid('i1',1,1,'WITNESS_REPAIR',['a1'])
        p=self.e.plan(pulse_id='pt',source_epoch=1,graph_epoch=1)
        self.assertEqual(p.plan_class,'ANCHOR_RECOMPILE')
        self.assertEqual(p.reason,'TRUNCATED_WITNESS_FORCES_ANCHOR_RECOMPILE')
    def test_dirty_frontier_overflow_forces_full_rebuild(self):
        self.e=DatabasePulseEngine(self.c,max_invalidations=2)
        for n in range(3): self.invalid(f'i{n}',1,1,'FACET_ONLY',[f'a{n}'])
        p=self.e.plan(pulse_id='po',source_epoch=1,graph_epoch=1)
        self.assertEqual(p.plan_class,'FIELD_REBUILD')
        self.assertTrue(p.close_all_invalidations)
        self.assertEqual(p.invalidation_count_total,3)
    def test_semantic_plan_hash_ignores_pulse_instance_id(self):
        self.invalid('i1',1,1,'FACET_ONLY',['a1'])
        a=self.e.plan(pulse_id='one',source_epoch=1,graph_epoch=1)
        b=self.e.plan(pulse_id='two',source_epoch=1,graph_epoch=1)
        self.assertEqual(a.semantic_plan_hash,b.semantic_plan_hash)
    def test_multiple_current_fields_fail_closed_with_receipt(self):
        add_field(self.c,9,1,1,'CURRENT',candidate='c1',anchor='other'); self.c.commit()
        r=self.e.pulse_once(pulse_id='pm',source_epoch=1,graph_epoch=1,timestamp='t')
        self.assertEqual(r['state'],'FAILED')
        row=self.c.execute("SELECT state,plan_class FROM database_pulse_cycles WHERE pulse_id='pm'").fetchone()
        self.assertEqual(tuple(row),('FAILED','FAIL_CLOSED'))
    def test_plan_hash_is_deterministic(self):
        self.invalid('i1',1,1,'WITNESS_REPAIR',['b','a'])
        a=self.e.plan(pulse_id='same',source_epoch=1,graph_epoch=1)
        b=self.e.plan(pulse_id='same',source_epoch=1,graph_epoch=1)
        self.assertEqual(a.semantic_plan_hash,b.semantic_plan_hash)

if __name__=='__main__': unittest.main(verbosity=2)

from __future__ import annotations
import sqlite3, sys, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
runtime = HERE / 'possibility_preprocessor_v10.py'
schema = HERE / 'RAE_UNIFIEDDB_V10_POSSIBILITY_COMPILER.sql'
if not runtime.exists(): runtime = Path('/tmp/possibility_preprocessor_v10.py')
if not schema.exists(): schema = Path('/tmp/RAE_UNIFIEDDB_V10_POSSIBILITY_COMPILER.sql')
sys.path.insert(0, str(runtime.parent))
from possibility_preprocessor_v10 import CandidateMeta, CompilerConfig, GraphEdge, PossibilityCompiler, TruncatedField

class U10Tests(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:')
        self.c.execute('PRAGMA foreign_keys=ON')
        self.c.executescript(schema.read_text())
        self.pc = PossibilityCompiler(self.c, CompilerConfig(max_depth=3,max_witnesses_per_candidate=4,max_path_states=1000))
        self.now='2026-08-10T00:00:00Z'
        self.pc.install_spec(self.now)

    def build_small(self):
        edges=[GraphEdge('A','B',.9,'AB'),GraphEdge('B','C',.9,'BC'),GraphEdge('C','D',1.0,'CD'),GraphEdge('A','C',.8,'AC')]
        meta={
            'A':CandidateMeta(1.0,facets={'available':'yes'}),
            'B':CandidateMeta(.5,facets={'available':'yes'}),
            'C':CandidateMeta(.6,facets={'available':'no'}),
            'D':CandidateMeta(1.0,facets={'available':'yes'}),
        }
        self.pc.start_field_epoch(field_epoch=1,source_epoch=5,graph_epoch=7,input_hash='x',built_at=self.now)
        self.pc.build_facets(field_epoch=1,candidate_meta=meta,source_epoch=5,created_at=self.now)
        r=self.pc.compile_anchor(field_epoch=1,source_epoch=5,graph_epoch=7,anchor_ref='A',edges=edges,candidate_meta=meta,created_at=self.now)
        self.pc.complete_field_epoch(1,self.now)
        return r

    def test_hyperposition_preserves_alternative_paths(self):
        self.build_small()
        ws=self.c.execute("SELECT path_score,path_refs_clay FROM clay_possibility_witnesses WHERE candidate_ref='D' ORDER BY witness_rank").fetchall()
        self.assertEqual(len(ws),2)
        self.assertAlmostEqual(ws[0][0],.81,places=8)
        self.assertAlmostEqual(ws[1][0],.8,places=8)

    def test_dynamic_facet_projection(self):
        self.build_small()
        q=self.pc.query(anchor_ref='A',required_facets={'available':'yes'},limit=4,expected_source_epoch=5,expected_graph_epoch=7)
        self.assertEqual([x[0] for x in q],['A','D','B'])

    def test_shadow_build_keeps_lkg_and_epoch_guard_rejects_mix(self):
        self.build_small()
        self.pc.start_field_epoch(field_epoch=2,source_epoch=6,graph_epoch=8,input_hash='unfinished',built_at=self.now)
        self.assertEqual(self.c.execute('SELECT field_epoch FROM v_clay_current_possibility_field_epoch').fetchone()[0],1)
        with self.assertRaises(TruncatedField):
            self.pc.query(anchor_ref='A',expected_source_epoch=6)

    def test_truncation_forces_exact_fallback(self):
        c=sqlite3.connect(':memory:'); c.execute('PRAGMA foreign_keys=ON'); c.executescript(schema.read_text())
        pc=PossibilityCompiler(c,CompilerConfig(max_depth=3,max_witnesses_per_candidate=2,max_path_states=2)); pc.install_spec(self.now)
        meta={x:CandidateMeta() for x in 'ABCD'}
        pc.start_field_epoch(field_epoch=1,source_epoch=1,graph_epoch=1,input_hash='t',built_at=self.now)
        pc.build_facets(field_epoch=1,candidate_meta=meta,source_epoch=1,created_at=self.now)
        r=pc.compile_anchor(field_epoch=1,source_epoch=1,graph_epoch=1,anchor_ref='A',edges=[GraphEdge('A','B'),GraphEdge('A','C'),GraphEdge('B','D')],candidate_meta=meta,created_at=self.now)
        self.assertTrue(r['truncated']); pc.complete_field_epoch(1,self.now)
        with self.assertRaises(TruncatedField): pc.query(anchor_ref='A',require_exact=True)

if __name__=='__main__': unittest.main(verbosity=2)

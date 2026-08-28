import copy
import unittest
from tools import trigger2_multihop_binding_generator_v1 as gen

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=gen.build_rows()
    def test_full(self):
        a=gen.validate_rows(self.rows)
        self.assertTrue(a['pass'], a['failures'][:10])
        self.assertEqual(1728,a['rows_total'])
        self.assertEqual({1:432,2:432,3:432,4:432},a['depth_counts'])
        self.assertAlmostEqual(0,a['class_symbol_mi_bits'],places=12)
    def test_target_depth(self):
        for r in self.rows[::37]:
            cb=gen.parse_codebook(r['prompt']); edges=gen.parse_bindings(r['prompt']); c=r['curriculum']['semantic_class_metadata_only']
            t,p=gen.resolve(cb[c],edges); self.assertEqual(r['target'],t); self.assertEqual(r['curriculum']['referential_depth'],len(p)-1)
    def test_target_tamper(self):
        b=copy.deepcopy(self.rows); b[0]['target']=next(x for x in gen.OUTPUT_SLOTS if x!=b[0]['target']); self.assertFalse(gen.validate_rows(b)['pass'])
    def test_metadata_lie(self):
        b=copy.deepcopy(self.rows); b[0]['curriculum']['binding_edges'][0][1]='x'; self.assertFalse(gen.validate_rows(b)['pass'])
    def test_leak(self):
        b=copy.deepcopy(self.rows); b[0]['prompt']+=' Hint: ALLOW'; self.assertFalse(gen.validate_rows(b)['pass'])
    def test_root_perm_lie(self):
        b=copy.deepcopy(self.rows); p=b[0]['curriculum']['root_permutation']; b[0]['curriculum']['root_permutation']=[p[1],p[0],p[2]]; self.assertFalse(gen.validate_rows(b)['pass'])
    def test_cycle(self):
        r=copy.deepcopy(self.rows[0]); cb=gen.parse_codebook(r['prompt']); edges=gen.parse_bindings(r['prompt']); c=r['curriculum']['semantic_class_metadata_only']; root=cb[c]
        edges=[(a,root if a==root else z) for a,z in edges]; old=gen._bindings(gen.parse_bindings(r['prompt'])); r['prompt']=r['prompt'].replace(old,gen._bindings(edges)); r['curriculum']['binding_edges']=[list(x) for x in edges]
        self.assertFalse(gen.validate_rows([r])['pass'])
    def test_distractors_disjoint(self):
        for r in self.rows[::53]:
            cb=gen.parse_codebook(r['prompt']); edges=gen.parse_bindings(r['prompt']); occupied=set()
            for root in cb.values(): _,p=gen.resolve(root,edges); occupied.update(x for x in p if x not in gen.OUTPUT_SLOTS)
            for d in r['curriculum']['distractor_roots']: _,p=gen.resolve(d,edges); self.assertFalse(occupied & {x for x in p if x not in gen.OUTPUT_SLOTS})

if __name__=='__main__': unittest.main()

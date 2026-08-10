import hashlib, random, unittest
from .state_merkle_treap_shadow import MerkleTreapStateShadow, TreapProof

def rh(x):return hashlib.sha256(x.encode()).hexdigest()

class MerkleTreapShadowTests(unittest.TestCase):
    def test_rebuild_is_order_independent_and_linear_nodes(self):
        rows=[('d',f'k{i:04d}',rh(f'v{i}')) for i in range(500)]
        a=MerkleTreapStateShadow(); ar=a.rebuild(rows); self.assertEqual(a.node_count(),len(rows))
        b=MerkleTreapStateShadow(); shuffled=list(rows); random.Random(77).shuffle(shuffled); br=b.rebuild(shuffled)
        self.assertEqual(ar,br); self.assertEqual(b.node_count(),len(rows))
    def test_incremental_update_equals_full_rebuild(self):
        rows={('d',f'k{i:03d}'):rh(f'v{i}') for i in range(120)}
        a=MerkleTreapStateShadow(); a.rebuild((d,k,v) for (d,k),v in rows.items()); rng=random.Random(15)
        for step in range(80):
            key=('d',f'k{rng.randrange(120):03d}'); rows[key]=rh(f'x{step}-{rng.randrange(9999)}'); a.update_hash(domain=key[0],key=key[1],row_hash_hex=rows[key])
            b=MerkleTreapStateShadow(); b.rebuild((d,k,v) for (d,k),v in rows.items()); self.assertEqual(a.map_root(),b.map_root())
    def test_remove_equals_rebuild(self):
        rows={('d',f'k{i:03d}'):rh(f'v{i}') for i in range(80)}; a=MerkleTreapStateShadow(); a.rebuild((d,k,v) for (d,k),v in rows.items())
        del rows[('d','k017')]; a.remove(domain='d',key='k017'); b=MerkleTreapStateShadow(); b.rebuild((d,k,v) for (d,k),v in rows.items()); self.assertEqual(a.map_root(),b.map_root())
    def test_internal_node_proofs_and_tamper_detection(self):
        a=MerkleTreapStateShadow(); rows=[('memory',f'k{i}',rh(f'v{i}')) for i in range(100)]; a.rebuild(rows)
        for i in (0,7,37,99):
            p=a.proof(domain='memory',key=f'k{i}'); self.assertTrue(MerkleTreapStateShadow.verify(p))
            bad=TreapProof(p.key_hash_hex,rh('tamper'),p.target_left_hash_hex,p.target_right_hash_hex,p.steps,p.root_hash_hex); self.assertFalse(MerkleTreapStateShadow.verify(bad))
    def test_metadata_commit_changes_without_map_change(self):
        a=MerkleTreapStateShadow(); a.update_hash(domain='a',key='b',row_hash_hex=rh('row')); kw={'global_epoch':1,'domain_epochs_hash_hex':rh('d'),'semantic_chain_hash_hex':rh('s')}; x=a.committed_root(**kw)
        self.assertNotEqual(x,a.committed_root(**{**kw,'global_epoch':2})); self.assertEqual(x,a.committed_root(**kw))
if __name__=='__main__':unittest.main()
